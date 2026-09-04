import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import HealthRing from "../components/HealthRing.jsx";
import { StatusBadge, PriorityBadge } from "../components/Badges.jsx";

export default function BatchPredict() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
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
      "health_score",
      "health_status",
      "failure_probability",
      "predicted_failure_type",
      "priority",
      "recommended_action",
    ];
    const lines = result.results.map((r) =>
      [
        r.machine_id,
        r.health_score,
        r.health_status,
        (r.failure_probability * 100).toFixed(1) + "%",
        r.predicted_failure_type,
        r.priority,
        `"${r.recommended_action.replace(/"/g, '""')}"`,
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
          <button
            onClick={exportResultsCsv}
            className="ml-auto px-4 py-2 rounded-lg border border-base-700 text-xs text-ink-300 hover:border-signal-cyan/40 hover:text-signal-cyan transition-colors"
          >
            Export results as CSV
          </button>
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
              <Link
                key={`${r.machine_id}-${r.row_number}`}
                to={r.machine_id.startsWith("UPLOAD-ROW") ? "#" : `/machines/${r.machine_id}`}
                className="panel p-5 flex items-center gap-4 hover:border-signal-cyan/40 transition-colors"
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
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
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
