import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import { StatCard, StatusBadge } from "../components/Badges.jsx";
import { LoadingState, ErrorState } from "./ExecutiveDashboard.jsx";

export default function RiskDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.riskDashboard().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  return (
    <div className="space-y-7">
      <header>
        <p className="text-xs uppercase tracking-wider text-signal-amber mb-1">Operational View</p>
        <h2 className="font-display text-2xl font-semibold">Risk Dashboard</h2>
      </header>

      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Excellent" value={data.excellent_count} accent="#3ED598" />
        <StatCard label="Healthy" value={data.healthy_count} accent="#3FD0E0" />
        <StatCard label="Warning" value={data.warning_count} accent="#F5A524" />
        <StatCard label="Critical" value={data.critical_count} accent="#EF5A5A" />
      </div>

      <div className="panel p-6">
        <h3 className="font-display text-sm font-medium text-ink-300 mb-4">
          Fleet Health Trend (14 days)
        </h3>
        {data.health_trend.length === 0 ? (
          <p className="text-sm text-ink-500">Not enough history yet to plot a trend.</p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data.health_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1C2740" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: "#7C88A3", fontSize: 11 }} axisLine={{ stroke: "#1C2740" }} />
              <YAxis domain={[0, 100]} tick={{ fill: "#7C88A3", fontSize: 11 }} axisLine={{ stroke: "#1C2740" }} />
              <Tooltip
                contentStyle={{ background: "#141D33", border: "1px solid #2A3654", borderRadius: 8 }}
                labelStyle={{ color: "#EAEEF6" }}
              />
              <Line
                type="monotone"
                dataKey="average_health_score"
                stroke="#3FD0E0"
                strokeWidth={2}
                dot={{ fill: "#3FD0E0", r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="panel p-6">
        <h3 className="font-display text-sm font-medium text-ink-300 mb-4">Top At-Risk Machines</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wider text-ink-500 border-b border-base-700">
              <th className="pb-3 font-medium">Machine</th>
              <th className="pb-3 font-medium">Health Score</th>
              <th className="pb-3 font-medium">Status</th>
              <th className="pb-3 font-medium">Predicted Failure</th>
              <th className="pb-3 font-medium">Probability</th>
            </tr>
          </thead>
          <tbody>
            {data.top_risk_machines.map((m) => (
              <tr key={m.machine_id} className="border-b border-base-800 last:border-0">
                <td className="py-3">
                  <Link to={`/machines/${m.machine_id}`} className="text-signal-cyan hover:underline">
                    {m.machine_id}
                  </Link>
                </td>
                <td className="py-3 data-num">{m.health_score.toFixed(1)}</td>
                <td className="py-3">
                  <StatusBadge status={m.health_status} />
                </td>
                <td className="py-3 text-ink-300">{m.predicted_failure_type}</td>
                <td className="py-3 data-num">{(m.failure_probability * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
