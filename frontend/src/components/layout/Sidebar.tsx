import { NavLink } from "react-router-dom";
import { LayoutDashboard, Briefcase, ClipboardList, Bug, Settings } from "lucide-react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/jobs", icon: Briefcase, label: "Jobs" },
  { to: "/applications", icon: ClipboardList, label: "Applications" },
  { to: "/scrapers", icon: Bug, label: "Scrapers" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  return (
    <aside className="w-56 bg-dark-900 border-r border-dark-700 flex flex-col h-screen fixed left-0 top-0">
      <div className="px-5 py-5 flex items-center gap-3">
        <div className="w-9 h-9 bg-gradient-to-br from-tier-s to-tier-a rounded-lg flex items-center justify-center text-white font-bold text-sm">
          JF
        </div>
        <div>
          <div className="text-slate-50 font-bold text-sm">Job Finder</div>
          <div className="text-slate-500 text-[10px]">v5 Pro</div>
        </div>
      </div>
      <nav className="px-3 flex-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-sm transition-colors ${
                isActive
                  ? "bg-dark-800 text-slate-50 font-medium"
                  : "text-slate-400 hover:text-slate-50 hover:bg-dark-800/50"
              }`
            }
          >
            <item.icon size={18} />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
