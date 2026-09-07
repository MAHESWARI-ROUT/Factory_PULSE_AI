import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { api } from "../api/client.js";
import { PriorityBadge } from "../components/Badges.jsx";
import { LoadingState, ErrorState } from "./ExecutiveDashboard.jsx";

export default function MaintenanceReports() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.maintenanceReport().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  function downloadPdf() {
    const doc = new jsPDF({ orientation: "landscape", unit: "pt" });
    const generatedAt = new Date(data.generated_at).toLocaleString();

    doc.setFontSize(16);
    doc.text("FactoryPulse AI — Maintenance Report", 40, 40);
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`Generated ${generatedAt}`, 40, 58);
    doc.text(`${data.urgent_count} urgent machine(s) of ${data.total_machines_reviewed} reviewed`, 40, 72);

    autoTable(doc, {
      startY: 90,
      head: [["Machine ID", "Failure Probability", "Predicted Type", "Priority", "Recommended Action"]],
      body: data.rows.map((r) => [
        r.machine_id,
        `${(r.failure_probability * 100).toFixed(1)}%`,
        r.predicted_failure_type,
        r.priority,
        r.recommended_action,
      ]),
      styles: { fontSize: 9, cellPadding: 6, overflow: "linebreak" },
      headStyles: { fillColor: [20, 29, 51], textColor: 255 },
      columnStyles: {
        0: { cellWidth: 80 },
        1: { cellWidth: 100 },
        2: { cellWidth: 90 },
        3: { cellWidth: 70 },
        4: { cellWidth: "auto" },
      },
      didParseCell: (hookData) => {
        if (hookData.section === "body" && hookData.column.index === 3) {
          const priority = hookData.cell.raw;
          const colors = {
            Urgent: [239, 90, 90],
            High: [245, 165, 36],
            Medium: [63, 208, 224],
            Low: [124, 136, 163],
          };
          if (colors[priority]) hookData.cell.styles.textColor = colors[priority];
        }
      },
    });

    doc.save(`factorypulse-maintenance-report-${new Date(data.generated_at).toISOString().slice(0, 10)}.pdf`);
  }

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-signal-cyan mb-1">Automatic Report</p>
          <h2 className="font-display text-2xl font-semibold">Maintenance Report</h2>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-xs text-ink-500">
              Generated {new Date(data.generated_at).toLocaleString()}
            </p>
            <p className="text-xs text-signal-red mt-0.5">{data.urgent_count} urgent machines</p>
          </div>
          <button
            onClick={downloadPdf}
            className="px-4 py-2.5 rounded-lg bg-signal-cyan/15 text-signal-cyan text-sm font-medium hover:bg-signal-cyan/25 transition-colors whitespace-nowrap"
          >
            Download PDF
          </button>
        </div>
      </header>

      <div className="panel overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wider text-ink-500 border-b border-base-700 bg-base-800/40">
              <th className="px-5 py-3 font-medium">Machine ID</th>
              <th className="px-5 py-3 font-medium">Failure Probability</th>
              <th className="px-5 py-3 font-medium">Predicted Type</th>
              <th className="px-5 py-3 font-medium">Priority</th>
              <th className="px-5 py-3 font-medium">Recommended Action</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr key={r.machine_id} className="border-b border-base-800 last:border-0">
                <td className="px-5 py-3">
                  <Link to={`/machines/${r.machine_id}`} className="text-signal-cyan hover:underline">
                    {r.machine_id}
                  </Link>
                </td>
                <td className="px-5 py-3 data-num">{(r.failure_probability * 100).toFixed(1)}%</td>
                <td className="px-5 py-3 text-ink-300">{r.predicted_failure_type}</td>
                <td className="px-5 py-3">
                  <PriorityBadge priority={r.priority} />
                </td>
                <td className="px-5 py-3 text-ink-300 max-w-md">{r.recommended_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
