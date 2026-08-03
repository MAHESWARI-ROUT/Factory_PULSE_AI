import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import HealthRing from "../components/HealthRing.jsx";
import { StatusBadge } from "../components/Badges.jsx";
import { LoadingState, ErrorState } from "./ExecutiveDashboard.jsx";

export default function MachineList() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("All");

  useEffect(() => {
    api.listMachines().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  const statuses = ["All", "Excellent", "Healthy", "Warning", "Critical"];
  const machines = data.machines.filter(
    (m) => filter === "All" || m.latest_snapshot?.health_status === filter
  );

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-signal-cyan mb-1">Fleet</p>
          <h2 className="font-display text-2xl font-semibold">Machines ({data.total})</h2>
        </div>
        <div className="flex gap-1.5">
          {statuses.map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filter === s
                  ? "bg-base-800 text-signal-cyan border border-signal-cyan/40"
                  : "text-ink-500 border border-base-700 hover:text-ink-300"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </header>

      <div className="grid grid-cols-4 gap-4">
        {machines.map((m) => (
          <Link
            key={m.machine_id}
            to={`/machines/${m.machine_id}`}
            className="panel p-5 flex items-center gap-4 hover:border-signal-cyan/40 transition-colors"
          >
            <HealthRing
              score={m.latest_snapshot?.health_score ?? 0}
              status={m.latest_snapshot?.health_status ?? "Healthy"}
              size={64}
              strokeWidth={5}
            />
            <div className="flex-1 min-w-0">
              <p className="font-display font-medium">{m.machine_id}</p>
              <p className="text-xs text-ink-500 mb-1.5">Type {m.machine_type} &middot; {m.location}</p>
              {m.latest_snapshot && <StatusBadge status={m.latest_snapshot.health_status} />}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
