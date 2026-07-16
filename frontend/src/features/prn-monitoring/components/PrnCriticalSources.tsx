import { ExternalLink } from "lucide-react";
import { PriorityBadge } from "./PriorityBadge";
import { EnabledBadge } from "./StatusBadge";
import type { UrlSourceRow } from "../types/prn";

interface Props {
  sources: UrlSourceRow[];
  maxItems?: number;
}

export function PrnCriticalSources({ sources, maxItems = 12 }: Props) {
  if (!sources.length) {
    return (
      <div className="rounded border border-surface-border bg-surface-raised p-4 text-xs text-slate-500">
        No CRITICAL or HIGH priority sources in current scope.
      </div>
    );
  }

  const visible = sources.slice(0, maxItems);

  return (
    <div className="rounded border border-surface-border bg-surface-raised">
      <div className="border-b border-surface-border px-3 py-2">
        <p className="text-xs font-medium text-slate-300">Critical & high-priority sources</p>
        <p className="text-[10px] text-slate-500">{sources.length} sources — Tier 1 realtime candidates</p>
      </div>
      <ul className="divide-y divide-surface-border">
        {visible.map((s) => (
          <li key={s.sourceId || s.url} className="flex items-start gap-2 px-3 py-2">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-1.5">
                <PriorityBadge level={String(s.priority)} />
                <EnabledBadge enabled={s.enabled} />
                <span className="text-[10px] text-slate-500">{s.state} · {s.platform}</span>
              </div>
              <p className="mt-0.5 truncate text-xs font-medium text-slate-200">{s.name}</p>
              <p className="truncate text-[10px] text-slate-500">{s.crawlFrequency} · {s.verificationStatus.replace(/_/g, " ")}</p>
            </div>
            <a
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 rounded p-1 text-slate-500 hover:bg-slate-800 hover:text-sky-400"
              title="Open source"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </li>
        ))}
      </ul>
      {sources.length > maxItems && (
        <p className="border-t border-surface-border px-3 py-2 text-[10px] text-slate-500">
          +{sources.length - maxItems} more in Sources tab
        </p>
      )}
    </div>
  );
}
