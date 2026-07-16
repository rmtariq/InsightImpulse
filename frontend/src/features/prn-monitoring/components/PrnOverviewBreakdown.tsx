import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { OverviewBreakdown, StateFilter } from "../types/prn";

const COLORS = ["#38bdf8", "#34d399", "#fbbf24", "#f87171", "#a78bfa"];

interface Props {
  breakdown?: OverviewBreakdown;
  stateFilter: StateFilter;
}

export function PrnOverviewBreakdown({ breakdown, stateFilter }: Props) {
  if (!breakdown?.dunByState.length && !breakdown?.dunByPriority.length) {
    return null;
  }

  const dunByState = breakdown.dunByState.filter((r) => {
    if (stateFilter === "Both") return true;
    if (stateFilter === "Johor") return r.stateCode === "Johor";
    return r.stateCode === "N9";
  });

  const dunByPriority = breakdown.dunByPriority;

  const chartClass = "rounded border border-surface-border bg-surface-raised p-3 h-[220px]";

  return (
    <div className="grid gap-3 lg:grid-cols-2">
      {dunByState.length > 0 && (
        <div className={chartClass}>
          <p className="mb-2 text-xs font-medium text-slate-400">DUN coverage by state</p>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={dunByState.map((r) => ({ name: r.state === "Negeri Sembilan" ? "N9" : r.state, value: r.dunCount }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", fontSize: 11 }} />
              <Bar dataKey="value" fill="#38bdf8" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      {dunByPriority.length > 0 && (
        <div className={chartClass}>
          <p className="mb-2 text-xs font-medium text-slate-400">DUN by monitoring priority</p>
          <ResponsiveContainer width="100%" height="85%">
            <PieChart>
              <Pie
                data={dunByPriority.map((r) => ({ name: r.priority, value: r.dunCount }))}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={70}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {dunByPriority.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", fontSize: 11 }} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
