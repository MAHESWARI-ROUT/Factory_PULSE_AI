import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Executive", icon: "◆" },
  { to: "/risk", label: "Risk Board", icon: "▲" },
  { to: "/machines", label: "Machines", icon: "▦" },
  { to: "/reports", label: "Reports", icon: "▤" },
  { to: "/chat", label: "Assistant", icon: "◈" },
];

export default function Sidebar() {
  return (
    <aside className="w-56 shrink-0 h-screen sticky top-0 bg-base-900 border-r border-base-700 flex flex-col">
      <div className="px-5 py-6">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-signal-cyan shadow-[0_0_12px_2px_rgba(63,208,224,0.6)]" />
          <h1 className="font-display font-semibold text-lg tracking-tight">FactoryPulse</h1>
        </div>
        <p className="text-[11px] text-ink-500 mt-1 pl-4">Predictive Maintenance Copilot</p>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-base-800 text-signal-cyan"
                  : "text-ink-300 hover:bg-base-800/60 hover:text-ink-100"
              }`
            }
          >
            <span className="text-xs opacity-70">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-base-700">
        <p className="text-[10px] text-ink-500 leading-relaxed">
          AI predictions are decision support, not a substitute for physical inspection.
        </p>
      </div>
    </aside>
  );
}
