import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "../api/client.js";
import HealthRing from "../components/HealthRing.jsx";
import { StatusBadge, PriorityBadge } from "../components/Badges.jsx";
import { LoadingState, ErrorState } from "./ExecutiveDashboard.jsx";

export default function MachineDetail() {
  const { machineId } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null);
    api.getMachine(machineId).then(setData).catch((e) => setError(e.message));
  }, [machineId]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  const latest = data.latest_snapshot;
  const trend = [...data.history]
    .reverse()
    .map((s) => ({ time: new Date(s.recorded_at).toLocaleDateString(), health: s.health_score }));

  return (
    <div className="space-y-7">
      <Link to="/machines" className="text-xs text-ink-500 hover:text-signal-cyan">
        &larr; Back to machines
      </Link>

      <div className="panel p-6 flex items-center gap-6">
        <HealthRing score={latest?.health_score ?? 0} status={latest?.health_status ?? "Healthy"} size={110} strokeWidth={9} />
        <div className="flex-1">
          <h2 className="font-display text-2xl font-semibold mb-1">{data.machine_id}</h2>
          <p className="text-sm text-ink-500 mb-3">Type {data.machine_type} &middot; {data.location}</p>
          <div className="flex gap-2">
            {latest && <StatusBadge status={latest.health_status} />}
            {latest && <PriorityBadge priority={latest.priority} />}
          </div>
        </div>
        {latest && (
          <div className="text-right">
            <p className="text-xs text-ink-500 uppercase tracking-wider mb-1">Predicted Failure</p>
            <p className="font-display text-lg">{latest.predicted_failure_type}</p>
            <p className="data-num text-sm text-ink-300">
              {(latest.failure_probability * 100).toFixed(1)}% probability
            </p>
          </div>
        )}
      </div>

      {latest && (
        <div className="panel p-6">
          <h3 className="font-display text-sm font-medium text-ink-300 mb-3">AI Maintenance Assistant</h3>
          <p className="text-sm text-ink-100 leading-relaxed">{latest.recommended_action}</p>
        </div>
      )}

      <div className="grid grid-cols-5 gap-4">
        {latest && (
          <>
            <SensorStat label="Air Temp" value={`${latest.air_temperature_k.toFixed(1)} K`} />
            <SensorStat label="Process Temp" value={`${latest.process_temperature_k.toFixed(1)} K`} />
            <SensorStat label="Rotational Speed" value={`${latest.rotational_speed_rpm.toFixed(0)} rpm`} />
            <SensorStat label="Torque" value={`${latest.torque_nm.toFixed(1)} Nm`} />
            <SensorStat label="Tool Wear" value={`${latest.tool_wear_min.toFixed(0)} min`} />
          </>
        )}
      </div>

      <div className="panel p-6">
        <h3 className="font-display text-sm font-medium text-ink-300 mb-4">Health Score History</h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={trend}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1C2740" vertical={false} />
            <XAxis dataKey="time" tick={{ fill: "#7C88A3", fontSize: 10 }} axisLine={{ stroke: "#1C2740" }} />
            <YAxis domain={[0, 100]} tick={{ fill: "#7C88A3", fontSize: 11 }} axisLine={{ stroke: "#1C2740" }} />
            <Tooltip
              contentStyle={{ background: "#141D33", border: "1px solid #2A3654", borderRadius: 8 }}
              labelStyle={{ color: "#EAEEF6" }}
            />
            <Line type="monotone" dataKey="health" stroke="#3FD0E0" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function SensorStat({ label, value }) {
  return (
    <div className="panel p-4">
      <p className="text-[11px] uppercase tracking-wider text-ink-500 mb-1">{label}</p>
      <p className="data-num text-lg font-medium text-ink-100">{value}</p>
    </div>
  );
}
