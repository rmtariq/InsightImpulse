import { pct } from "../lib/prnFormatters";
import { PriorityBadge } from "./PriorityBadge";
import type { QueryReadinessSummary } from "../types/prn";

export function PrnQueryReadiness({ data }: { data: QueryReadinessSummary }) {
  const items = [
    { label: "BM queries", count: data.withQueryBm },
    { label: "Hashtags", count: data.withHashtags },
    { label: "Local landmarks", count: data.withLocalLandmarks },
    { label: "Local issues", count: data.withLocalIssues },
    { label: "ZH queries", count: data.withQueryZh },
    { label: "TA queries", count: data.withQueryTa },
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {items.map(({ label, count }) => {
          const p = pct(count, data.totalDun);
          return (
            <div key={label} className="rounded border border-surface-border bg-surface-raised p-3">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">{label}</span>
                <span className="tabular-nums text-slate-200">{count}/{data.totalDun}</span>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
                <div className="h-full bg-sky-600 transition-all" style={{ width: `${p}%` }} />
              </div>
              <p className="mt-1 text-[10px] tabular-nums text-slate-500">{p}% ready</p>
            </div>
          );
        })}
      </div>
      <div>
        <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Top 10 priority DUN</h3>
        <div className="rounded border border-surface-border bg-surface-raised divide-y divide-surface-border">
          {data.topPriorityDuns.map((d, i) => (
            <div key={`${d.state}-${d.dunCode}`} className="flex items-center justify-between px-3 py-2 text-xs">
              <span className="text-slate-300">
                <span className="text-slate-500 tabular-nums mr-2">{i + 1}.</span>
                {d.dunCode} {d.dunName}
                <span className="ml-2 text-slate-500">{d.state}</span>
              </span>
              <div className="flex items-center gap-2">
                <span className="tabular-nums text-slate-400">{d.monitoringPriorityScore}</span>
                <PriorityBadge level={d.monitoringPriority} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
