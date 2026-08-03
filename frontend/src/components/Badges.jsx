import { STATUS_COLORS } from "./HealthRing.jsx";

export function StatusBadge({ status }) {
  const color = STATUS_COLORS[status] || STATUS_COLORS.Healthy;
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
      style={{ backgroundColor: `${color}1A`, color }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
      {status}
    </span>
  );
}

const PRIORITY_COLORS = {
  Urgent: "#EF5A5A",
  High: "#F5A524",
  Medium: "#3FD0E0",
  Low: "#7C88A3",
};

export function PriorityBadge({ priority }) {
  const color = PRIORITY_COLORS[priority] || PRIORITY_COLORS.Low;
  return (
    <span
      className="px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wide"
      style={{ backgroundColor: `${color}1A`, color }}
    >
      {priority}
    </span>
  );
}

export function StatCard({ label, value, sublabel, accent = "#3FD0E0" }) {
  return (
    <div className="panel p-5 flex flex-col gap-1">
      <span className="text-xs uppercase tracking-wider text-ink-500">{label}</span>
      <span className="data-num text-3xl font-semibold" style={{ color: accent }}>
        {value}
      </span>
      {sublabel && <span className="text-xs text-ink-500">{sublabel}</span>}
    </div>
  );
}
