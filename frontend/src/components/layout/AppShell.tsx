import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, LayoutDashboard } from "lucide-react";
import clsx from "clsx";

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <aside className="hidden w-52 shrink-0 flex-col border-r border-surface-border bg-surface-raised md:flex">
        <div className="border-b border-surface-border px-4 py-4">
          <p className="text-sm font-semibold text-slate-100">InsightPulse</p>
          <p className="text-[10px] text-slate-500">Election Intelligence</p>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-2 rounded px-3 py-2 text-xs font-medium",
                isActive ? "bg-sky-950/50 text-sky-300" : "text-slate-400 hover:bg-slate-800/50",
              )
            }
          >
            <BarChart3 className="h-4 w-4" />
            PRN Monitoring
          </NavLink>
          <a
            href="/"
            className="flex items-center gap-2 rounded px-3 py-2 text-xs font-medium text-slate-500 hover:bg-slate-800/50"
          >
            <LayoutDashboard className="h-4 w-4" />
            War Room (8080)
          </a>
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <Outlet />
      </div>
    </div>
  );
}
