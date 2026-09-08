import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { api } from "../api/client.js";
import HealthRing from "../components/HealthRing.jsx";
import { StatusBadge, PriorityBadge } from "../components/Badges.jsx";

export default function BatchPredict() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [selectedRow, setSelectedRow] = useState(null);
  const inputRef = useRef(null);

  function pickFile(f) {
    if (!f) return;
    setFile(f);
    setResult(null);
    setError(null);
  }

  async function runPrediction() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.batchPredict(file);
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function exportResultsCsv() {
    if (!result) return;
    const header = [
      "machine_id",
      "machine_type",
      "air_temperature_k",
      "process_temperature_k",
      "rotational_speed_rpm",
      "torque_nm",
      "tool_wear_min",
      "health_score",
      "health_status",
      "failure_probability",
      "predicted_failure_type",
      "anomaly_score",
      "is_anomaly",
      "priority",
      "recommended_action",
      "ai_explanation",
    ];
    const lines = result.results.map((r) =>
      [
        r.machine_id,
        r.machine_type,
        r.air_temperature_k,
        r.process_temperature_k,
        r.rotational_speed_rpm,
        r.torque_nm,
        r.tool_wear_min,
        r.health_score,
        r.health_status,
        (r.failure_probability * 100).toFixed(1) + "%",
        r.predicted_failure_type,
        r.anomaly_score,
        r.is_anomaly,
        r.priority,
        `"${r.recommended_action.replace(/"/g, '""')}"`,
        `"${r.ai_explanation.replace(/"/g, '""')}"`,
      ].join(",")
    );
    const csv = [header.join(","), ...lines].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "factorypulse_batch_predictions.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadDetailedPdf() {
    if (!result) return;
    const doc = new jsPDF({ orientation: "landscape", unit: "pt" });
    const generatedAt = new Date().toLocaleString();
    const urgentCount = result.results.filter((r) => r.priority === "Urgent").length;

    doc.setFontSize(16);
    doc.text("FactoryPulse AI — Batch Prediction Report", 40, 40);
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`Source file: ${result.filename} · Generated ${generatedAt}`, 40, 58);
    doc.text(
      `${result.successful}/${result.total_rows} rows processed · ${urgentCount} urgent · ${result.failed} failed`,
      40,
      72
    );

    // Summary table — one row per machine, same shape as the automatic
    // maintenance report, plus the anomaly-detector columns unique to a
    // fresh batch upload.
    autoTable(doc, {
      startY: 90,
      head: [
        [
          "Machine ID",
          "Health",
          "Failure Prob.",
          "Predicted Type",
          "Anomaly",
          "Priority",
          "Recommended Action",
        ],
      ],
      body: result.results.map((r) => [
        r.machine_id,
        `${Math.round(r.health_score)}/100`,
        `${(r.failure_probability * 100).toFixed(1)}%`,
        r.predicted_failure_type,
        r.is_anomaly ? `Yes (${r.anomaly_score.toFixed(2)})` : "No",
        r.priority,
        r.recommended_action,
      ]),
      styles: { fontSize: 9, cellPadding: 6, overflow: "linebreak" },
      headStyles: { fillColor: [20, 29, 51], textColor: 255 },
      columnStyles: {
        0: { cellWidth: 75 },
        1: { cellWidth: 55 },
        2: { cellWidth: 70 },
        3: { cellWidth: 90 },
        4: { cellWidth: 70 },
        5: { cellWidth: 55 },
        6: { cellWidth: "auto" },
      },
      didParseCell: (hookData) => {
        if (hookData.section === "body" && hookData.column.index === 5) {
          const priority = hookData.cell.raw;
          const colors = { Urgent: [239, 90, 90], High: [245, 165, 36], Medium: [63, 208, 224], Low: [124, 136, 163] };
          if (colors[priority]) hookData.cell.styles.textColor = colors[priority];
        }
      },
    });

    // Detailed per-machine section — mirrors the single-machine detail
    // page: sensor readings, the full ML pipeline output, and the
    // Gemini/rule-based AI explanation, one block per uploaded row.
    doc.addPage();
    doc.setFontSize(14);
    doc.text("Detailed Machine Reports", 40, 40);

    let y = 64;
    const pageHeight = doc.internal.pageSize.getHeight();
    result.results.forEach((r, idx) => {
      if (y > pageHeight - 140) {
        doc.addPage();
        y = 48;
      }
      doc.setFontSize(11);
      doc.setTextColor(20);
      doc.text(`${idx + 1}. ${r.machine_id} — Type ${r.machine_type}`, 40, y);
      y += 16;
      doc.setFontSize(9);
      doc.setTextColor(90);
      doc.text(
        `Health ${Math.round(r.health_score)}/100 (${r.health_status}) · ${r.predicted_failure_type} ` +
          `(${(r.failure_probability * 100).toFixed(1)}%) · Anomaly: ${r.is_anomaly ? "Yes" : "No"} ` +
          `(score ${r.anomaly_score.toFixed(2)}) · Priority: ${r.priority}`,
        40,
        y
      );
      y += 14;
      doc.text(
        `Air ${r.air_temperature_k.toFixed(1)}K · Process ${r.process_temperature_k.toFixed(1)}K · ` +
          `${r.rotational_speed_rpm.toFixed(0)} rpm · ${r.torque_nm.toFixed(1)} Nm · ` +
          `Tool wear ${r.tool_wear_min.toFixed(0)} min`,
        40,
        y
      );
      y += 14;
      doc.setTextColor(20);
      const wrappedAction = doc.splitTextToSize(`Action: ${r.recommended_action}`, 700);
      doc.text(wrappedAction, 40, y);
      y += wrappedAction.length * 12 + 2;
      const wrappedExplanation = doc.splitTextToSize(`AI Assistant: ${r.ai_explanation}`, 700);
      doc.text(wrappedExplanation, 40, y);
      y += wrappedExplanation.length * 12 + 18;
    });

    doc.save(`factorypulse-batch-report-${new Date().toISOString().slice(0, 10)}.pdf`);
  }

  const sortedResults = result
    ? [...result.results].sort((a, b) => a.health_score - b.health_score)
    : [];

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs uppercase tracking-wider text-signal-cyan mb-1">Batch Analysis</p>
        <h2 className="font-display text-2xl font-semibold">Upload &amp; Predict</h2>
        <p className="text-sm text-ink-500 mt-1 max-w-2xl">
          Upload a CSV or Excel export collected from IoT sensors across your fleet — one row per
          machine reading. FactoryPulse will score every row's health, failure risk, and
          recommended action in a single pass.
        </p>
      </header>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          pickFile(e.dataTransfer.files?.[0]);
        }}
        onClick={() => inputRef.current?.click()}
        className={`panel p-10 flex flex-col items-center justify-center gap-3 cursor-pointer transition-colors border-dashed ${
          dragActive ? "border-signal-cyan/60 bg-base-800/60" : "border-base-700"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          onChange={(e) => pickFile(e.target.files?.[0])}
        />
        <span className="text-3xl opacity-60">⇧</span>
        <p className="text-sm text-ink-200">
          {file ? (
            <span className="text-signal-cyan font-medium">{file.name}</span>
          ) : (
            <>Drag a CSV/Excel file here, or click to browse</>
          )}
        </p>
        <p className="text-xs text-ink-500">Accepts .csv, .xlsx, .xls</p>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={runPrediction}
          disabled={!file || loading}
          className="px-5 py-2.5 rounded-lg bg-signal-cyan/15 text-signal-cyan text-sm font-medium hover:bg-signal-cyan/25 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? "Predicting..." : "Run Batch Prediction"}
        </button>
        <a
          href={api.batchTemplateUrl()}
          className="text-xs text-ink-500 hover:text-signal-cyan underline underline-offset-2"
        >
          Download CSV template
        </a>
        {result && (
          <div className="ml-auto flex items-center gap-3">
            <button
              onClick={downloadDetailedPdf}
              className="px-4 py-2 rounded-lg border border-base-700 text-xs text-ink-300 hover:border-signal-cyan/40 hover:text-signal-cyan transition-colors"
            >
              Download detailed PDF report
            </button>
            <button
              onClick={exportResultsCsv}
              className="px-4 py-2 rounded-lg border border-base-700 text-xs text-ink-300 hover:border-signal-cyan/40 hover:text-signal-cyan transition-colors"
            >
              Export results as CSV
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="panel p-4 border-signal-red/40">
          <p className="text-sm text-signal-red">{error}</p>
        </div>
      )}

      {result && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <SummaryStat label="Rows Processed" value={result.total_rows} accent="#EAEEF6" />
            <SummaryStat label="Successful" value={result.successful} accent="#3ED598" />
            <SummaryStat label="Failed Rows" value={result.failed} accent="#EF5A5A" />
            <SummaryStat
              label="Critical / Urgent"
              value={result.results.filter((r) => r.priority === "Urgent").length}
              accent="#F5A524"
            />
          </div>

          {result.errors.length > 0 && (
            <div className="panel p-4 border-signal-amber/30">
              <p className="text-xs font-medium text-signal-amber mb-2">
                {result.errors.length} row(s) could not be processed
              </p>
              <ul className="text-xs text-ink-400 space-y-1">
                {result.errors.map((e) => (
                  <li key={e.row_number}>
                    Row {e.row_number}: {e.error}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid grid-cols-4 gap-4">
            {sortedResults.map((r) => (
              <button
                key={`${r.machine_id}-${r.row_number}`}
                onClick={() => setSelectedRow(r)}
                className="panel p-5 flex items-center gap-4 text-left hover:border-signal-cyan/40 transition-colors"
              >
                <HealthRing score={r.health_score} status={r.health_status} size={64} strokeWidth={5} />
                <div className="flex-1 min-w-0">
                  <p className="font-display font-medium truncate">{r.machine_id}</p>
                  <p className="text-xs text-ink-500 mb-1.5">
                    {r.predicted_failure_type} &middot; {(r.failure_probability * 100).toFixed(0)}%
                  </p>
                  <div className="flex gap-1.5 flex-wrap">
                    <StatusBadge status={r.health_status} />
                    <PriorityBadge priority={r.priority} />
                    {r.is_anomaly && (
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wide bg-signal-amber/10 text-signal-amber">
                        Anomaly
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </>
      )}

      {selectedRow && <RowDetailModal row={selectedRow} onClose={() => setSelectedRow(null)} />}
    </div>
  );
}

function RowDetailModal({ row, onClose }) {
  const isKnownMachine = !row.machine_id.startsWith("UPLOAD-ROW");

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-6"
      onClick={onClose}
    >
      <div
        className="panel w-full max-w-2xl max-h-[85vh] overflow-y-auto p-6 space-y-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            <HealthRing score={row.health_score} status={row.health_status} size={72} strokeWidth={6} />
            <div>
              <h3 className="font-display text-xl font-semibold">{row.machine_id}</h3>
              <p className="text-xs text-ink-500 mb-2">Type {row.machine_type} &middot; Row {row.row_number}</p>
              <div className="flex gap-1.5 flex-wrap">
                <StatusBadge status={row.health_status} />
                <PriorityBadge priority={row.priority} />
                {row.is_anomaly && (
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wide bg-signal-amber/10 text-signal-amber">
                    Anomaly (score {row.anomaly_score.toFixed(2)})
                  </span>
                )}
              </div>
            </div>
          </div>
          <button onClick={onClose} className="text-ink-500 hover:text-ink-100 text-xl leading-none">
            &times;
          </button>
        </div>

        <div className="panel p-4 bg-base-800/40">
          <p className="text-xs text-ink-500 uppercase tracking-wider mb-1">Predicted Failure</p>
          <p className="font-display text-lg">{row.predicted_failure_type}</p>
          <p className="data-num text-sm text-ink-300">{(row.failure_probability * 100).toFixed(1)}% probability</p>
        </div>

        <div>
          <h4 className="font-display text-sm font-medium text-ink-300 mb-2">AI Maintenance Assistant</h4>
          <p className="text-sm text-ink-100 leading-relaxed mb-2">{row.recommended_action}</p>
          <p className="text-sm text-ink-400 leading-relaxed italic">{row.ai_explanation}</p>
        </div>

        <div>
          <h4 className="font-display text-sm font-medium text-ink-300 mb-3">Sensor Readings</h4>
          <div className="grid grid-cols-5 gap-3">
            <SensorStat label="Air Temp" value={`${row.air_temperature_k.toFixed(1)} K`} />
            <SensorStat label="Process Temp" value={`${row.process_temperature_k.toFixed(1)} K`} />
            <SensorStat label="Rotational Speed" value={`${row.rotational_speed_rpm.toFixed(0)} rpm`} />
            <SensorStat label="Torque" value={`${row.torque_nm.toFixed(1)} Nm`} />
            <SensorStat label="Tool Wear" value={`${row.tool_wear_min.toFixed(0)} min`} />
          </div>
        </div>

        {isKnownMachine && (
          <Link
            to={`/machines/${row.machine_id}`}
            className="inline-block text-xs text-signal-cyan hover:underline underline-offset-2"
          >
            View full machine history &rarr;
          </Link>
        )}
      </div>
    </div>
  );
}

function SensorStat({ label, value }) {
  return (
    <div className="panel p-3">
      <p className="text-[10px] uppercase tracking-wider text-ink-500 mb-1">{label}</p>
      <p className="data-num text-sm font-medium text-ink-100">{value}</p>
    </div>
  );
}

function SummaryStat({ label, value, accent }) {
  return (
    <div className="panel p-5 flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wider text-ink-500">{label}</span>
      <span className="data-num text-3xl font-semibold" style={{ color: accent }}>
        {value}
      </span>
    </div>
  );
}
