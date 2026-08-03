/**
 * A circular gauge in the style of a physical instrument-cluster dial --
 * this is FactoryPulse's signature element: every machine's health score
 * reads like a gauge you'd find bolted to the machine itself, not a generic
 * progress bar or donut chart.
 */
const STATUS_COLORS = {
  Excellent: "#3ED598",
  Healthy: "#3FD0E0",
  Warning: "#F5A524",
  Critical: "#EF5A5A",
};

export default function HealthRing({ score, status, size = 88, strokeWidth = 7 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const sweep = 270; // gauge sweeps 270 degrees, like a real dial
  const offset = circumference * (1 - (score / 100) * (sweep / 360));
  const color = STATUS_COLORS[status] || STATUS_COLORS.Healthy;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-[225deg]">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#1C2740"
          strokeWidth={strokeWidth}
          strokeDasharray={`${circumference * (sweep / 360)} ${circumference}`}
          strokeLinecap="round"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={`${circumference * (sweep / 360)} ${circumference}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="data-num text-lg font-semibold" style={{ color }}>
          {Math.round(score)}
        </span>
        <span className="text-[9px] uppercase tracking-wider text-ink-500">health</span>
      </div>
    </div>
  );
}

export { STATUS_COLORS };
