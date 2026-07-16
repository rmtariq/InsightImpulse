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
import { countBy, filterByState } from "../lib/prnCalculations";
import type { PrnDashboardFilters, UrlSourceRow } from "../types/prn";

const COLORS = ["#38bdf8", "#34d399", "#fbbf24", "#f87171", "#a78bfa", "#94a3b8"];

interface Props {
  sources: UrlSourceRow[];
  filters: PrnDashboardFilters;
}

export function PrnSourceCoverageCharts({ sources, filters }: Props) {
  const scoped = filterByState(sources, filters.state);

  const byState = [
    { name: "Johor", value: sources.filter((s) => s.state === "Johor" || s.state === "All").length },
    { name: "N9", value: sources.filter((s) => s.state === "Negeri Sembilan" || s.state === "All").length },
  ].filter((row) => row.value > 0);

  const enabledByState = ["Johor", "Negeri Sembilan"].map((st) => {
    const rows = sources.filter((s) => s.state === st || s.state === "All");
    return {
      name: st === "Negeri Sembilan" ? "N9" : st,
      enabled: rows.filter((s) => s.enabled).length,
      disabled: rows.filter((s) => !s.enabled).length,
    };
  }).filter((r) => r.enabled + r.disabled > 0);

  const byPlatform = Object.entries(countBy(scoped, (r) => r.platform)).map(([name, value]) => ({ name, value }));
  const enabledData = [
    { name: "Enabled", value: scoped.filter((s) => s.enabled).length },
    { name: "Disabled", value: scoped.filter((s) => !s.enabled).length },
  ];
  const byPriority = Object.entries(countBy(scoped, (r) => String(r.priority).toUpperCase())).map(([name, value]) => ({
    name,
    value,
  }));
  const byVerification = Object.entries(countBy(scoped, (r) => r.verificationStatus || "Unknown")).map(([name, value]) => ({
    name: name.replace(/_/g, " ").slice(0, 24),
    value,
  }));
  const byFrequency = Object.entries(countBy(scoped, (r) => r.crawlFrequency || "unknown")).map(([name, value]) => ({
    name,
    value,
  }));

  const chartClass = "rounded border border-surface-border bg-surface-raised p-3 h-[220px]";

  return (
    <div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-3">
      {filters.state === "Both" && enabledByState.length > 0 && (
        <div className={`${chartClass} xl:col-span-2`}>
          <p className="mb-2 text-xs font-medium text-slate-400">Enabled vs disabled by state</p>
          <ResponsiveContainer width="100%" height="85%">
            <BarChart data={enabledByState} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", fontSize: 11 }} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="enabled" stackId="a" fill="#34d399" name="Enabled" radius={[0, 0, 0, 0]} />
              <Bar dataKey="disabled" stackId="a" fill="#64748b" name="Disabled" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      {filters.state === "Both" && byState.length > 0 && (
        <ChartBlock title="Sources by state (Johor vs N9)" data={byState} className={chartClass} />
      )}
      <ChartBlock title="Sources by platform" data={byPlatform} className={chartClass} />
      <ChartBlock title="Enabled vs disabled" data={enabledData} className={chartClass} pie />
      <ChartBlock title="By priority" data={byPriority} className={chartClass} />
      <ChartBlock title="Verification status" data={byVerification} className={chartClass} />
      <ChartBlock title="Crawl frequency" data={byFrequency} className={`${chartClass} xl:col-span-2`} horizontal />
    </div>
  );
}

function ChartBlock({
  title,
  data,
  className,
  pie,
  horizontal,
}: {
  title: string;
  data: { name: string; value: number }[];
  className: string;
  pie?: boolean;
  horizontal?: boolean;
}) {
  return (
    <div className={className}>
      <p className="mb-2 text-xs font-medium text-slate-400">{title}</p>
      <ResponsiveContainer width="100%" height="85%">
        {pie ? (
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", fontSize: 11 }} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
          </PieChart>
        ) : (
          <BarChart data={data} layout={horizontal ? "vertical" : "horizontal"} margin={{ top: 4, right: 8, left: horizontal ? 60 : 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            {horizontal ? (
              <>
                <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <YAxis type="category" dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} width={56} />
              </>
            ) : (
              <>
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={50} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
              </>
            )}
            <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", fontSize: 11 }} />
            <Bar dataKey="value" fill="#38bdf8" radius={[2, 2, 0, 0]} />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
