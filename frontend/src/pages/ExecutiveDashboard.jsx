import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "../api/client.js";
import { StatCard } from "../components/Badges.jsx";

const FAILURE_LABELS = {
  NONE: "No Failure",
  HDF: "Heat Dissipation",
  PWF: "Power Failure",
  OSF: "Overstrain",
  TWF: "Tool Wear",
  RNF: "Random",
};

export default function ExecutiveDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.executiveDashboard().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  const chartData = data.failure_type_distribution
    .filter((d) => d.failure_type !== "NONE")
    .map((d) => ({ name: FAILURE_LABELS[d.failure_type] || d.failure_type, count: d.count }));

  return (
    <div className="space-y-7">
      <header>
        <p className="text-xs uppercase tracking-wider text-signal-cyan mb-1">Executive Overview</p>
        <h2 className="font-display text-2xl font-semibold">Plant Health Summary</h2>
      </header>

      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Total Machines" value={data.total_machines} accent="#EAEEF6" />
        <StatCard label="Healthy" value={data.healthy_count} accent="#3ED598" sublabel="Excellent + Healthy" />
        <StatCard label="Critical" value={data.critical_count} accent="#EF5A5A" sublabel="Needs immediate attention" />
        <StatCard
          label="Avg Health Score"
          value={data.average_health_score.toFixed(1)}
          accent="#3FD0E0"
          sublabel="out of 100"
        />
      </div>

      <div className="grid grid-cols-5 gap-6">
        <div className="col-span-3 panel p-6">
          <h3 className="font-display text-sm font-medium text-ink-300 mb-4">
            Failure Type Distribution
          </h3>
          {chartData.length === 0 ? (
            <p className="text-sm text-ink-500">No active failure signatures across the fleet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C2740" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "#7C88A3", fontSize: 11 }} axisLine={{ stroke: "#1C2740" }} />
                <YAxis tick={{ fill: "#7C88A3", fontSize: 11 }} axisLine={{ stroke: "#1C2740" }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ background: "#141D33", border: "1px solid #2A3654", borderRadius: 8 }}
                  labelStyle={{ color: "#EAEEF6" }}
                />
                <Bar dataKey="count" fill="#3FD0E0" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="col-span-2 panel p-6">
          <h3 className="font-display text-sm font-medium text-ink-300 mb-4">AI Recommendations</h3>
          <ul className="space-y-3">
            {data.ai_recommendations.map((rec, i) => (
              <li key={i} className="text-sm text-ink-300 leading-relaxed border-l-2 border-signal-cyan/40 pl-3">
                {rec}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export function LoadingState() {
  return <p className="text-sm text-ink-500">Loading plant data...</p>;
}

export function ErrorState({ message }) {
  return (
    <div className="panel p-6 border-signal-red/40">
      <p className="text-sm text-signal-red">Couldn't reach the FactoryPulse API.</p>
      <p className="text-xs text-ink-500 mt-1">{message}</p>
    </div>
  );
}
