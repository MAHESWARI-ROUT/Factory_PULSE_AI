import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
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

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-signal-cyan mb-1">Automatic Report</p>
          <h2 className="font-display text-2xl font-semibold">Maintenance Report</h2>
        </div>
        <div className="text-right">
          <p className="text-xs text-ink-500">
            Generated {new Date(data.generated_at).toLocaleString()}
          </p>
          <p className="text-xs text-signal-red mt-0.5">{data.urgent_count} urgent machines</p>
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
