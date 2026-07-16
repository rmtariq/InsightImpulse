import { AlertTriangle, Info } from "lucide-react";
import type { PrnOperationalInsight } from "../types/prn";

export function PrnOperationalInsights({ insights }: { insights: PrnOperationalInsight[] }) {
  if (!insights.length) {
    return <p className="text-sm text-slate-500">No operational insights generated.</p>;
  }

  return (
    <ul className="space-y-2">
      {insights.map((item) => (
        <li
          key={item.id}
          className={`flex gap-2 rounded border px-3 py-2 text-sm ${
            item.severity === "critical"
              ? "border-rose-900/60 bg-rose-950/30 text-rose-100"
              : item.severity === "warning"
                ? "border-amber-900/50 bg-amber-950/20 text-amber-100"
                : "border-surface-border bg-surface-raised text-slate-300"
          }`}
        >
          {item.severity === "critical" ? (
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-400" />
          ) : (
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-sky-400" />
          )}
          <span>{item.text}</span>
        </li>
      ))}
    </ul>
  );
}
