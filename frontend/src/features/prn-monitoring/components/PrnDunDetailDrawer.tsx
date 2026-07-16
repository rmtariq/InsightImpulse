import { X } from "lucide-react";
import { splitKeywords } from "../lib/transformPrnData";
import { PriorityBadge } from "./PriorityBadge";
import type { DunKeywordRow } from "../types/prn";

interface Props {
  dun: DunKeywordRow | null;
  onClose: () => void;
}

function ChipGroup({ label, items }: { label: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="mt-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <div className="mt-1 flex flex-wrap gap-1">
        {items.map((item) => (
          <span key={item} className="rounded border border-surface-border bg-surface px-1.5 py-0.5 text-[10px] text-slate-300">
            {item.length > 48 ? `${item.slice(0, 48)}…` : item}
          </span>
        ))}
      </div>
    </div>
  );
}

function TextBlock({ label, text }: { label: string; text: string | null }) {
  if (!text?.trim()) return null;
  return (
    <div className="mt-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 rounded border border-surface-border bg-surface p-2 font-mono text-[11px] leading-relaxed text-slate-300">
        {text}
      </p>
    </div>
  );
}

export function PrnDunDetailDrawer({ dun, onClose }: Props) {
  if (!dun) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose}>
      <aside
        className="h-full w-full max-w-lg overflow-y-auto border-l border-surface-border bg-surface-raised shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-start justify-between border-b border-surface-border bg-slate-900 px-4 py-3">
          <div>
            <p className="text-xs text-slate-500">{dun.state} · {dun.dunCode}</p>
            <h2 className="text-lg font-semibold text-slate-100">{dun.dunName}</h2>
            <p className="text-xs text-slate-400">{dun.parlimenName} · {dun.district}</p>
          </div>
          <button type="button" onClick={onClose} className="rounded p-1 text-slate-400 hover:bg-slate-800">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-4">
          <div className="flex flex-wrap gap-2">
            <PriorityBadge level={dun.monitoringPriority} />
            <span className="rounded border border-surface-border px-2 py-0.5 text-xs tabular-nums text-slate-300">
              Score {dun.monitoringPriorityScore}
            </span>
            {dun.areaType && (
              <span className="rounded border border-surface-border px-2 py-0.5 text-xs text-slate-400">
                {dun.areaType.replace(/_/g, " ")}
              </span>
            )}
            {dun.electionStatus2026 && (
              <span className="rounded border border-surface-border px-2 py-0.5 text-xs text-slate-400">
                {dun.electionStatus2026.replace(/_/g, " ")}
              </span>
            )}
          </div>
          {dun.sensitivityNotes && (
            <p className="mt-3 rounded border border-amber-900/50 bg-amber-950/30 p-2 text-xs text-amber-200">
              Review-sensitive: {dun.sensitivityNotes}
            </p>
          )}
          <ChipGroup label="Primary keywords" items={splitKeywords(dun.primaryKeywords)} />
          <ChipGroup label="Hashtags" items={splitKeywords(dun.hashtags?.replace(/#/g, " #"))} />
          <ChipGroup label="Local landmarks" items={splitKeywords(dun.localLandmarks)} />
          <ChipGroup label="Local issues" items={splitKeywords(dun.localIssues)} />
          <ChipGroup label="Ethnic mix (review tags)" items={splitKeywords(dun.ethnicMix)} />
          <ChipGroup label="Language mix" items={splitKeywords(dun.languageMix)} />
          <ChipGroup label="Royal / adat entities (classifier tags)" items={splitKeywords(dun.royalEntities)} />
          <ChipGroup label="Party keywords" items={splitKeywords(dun.partyKeywords)} />
          <ChipGroup label="Issue keywords" items={splitKeywords(dun.issueKeywords)} />
          <ChipGroup label="Election keywords 2026" items={splitKeywords(dun.electionKeywords2026)} />
          <ChipGroup label="Development keywords" items={splitKeywords(dun.developmentKeywords2026)} />
          <ChipGroup label="Service keywords" items={splitKeywords(dun.serviceKeywords)} />
          <ChipGroup label="Candidate keywords" items={splitKeywords(dun.candidateKeywords)} />
          <TextBlock label="Query BM" text={dun.queryBm} />
          <TextBlock label="Query ZH" text={dun.queryZh} />
          <TextBlock label="Query TA" text={dun.queryTa} />
          <TextBlock label="Sensitive content rule" text={dun.sensitiveContentRule} />
          {dun.sourceReference && (
            <p className="mt-4 text-[10px] text-slate-600 break-all">Source: {dun.sourceReference}</p>
          )}
        </div>
      </aside>
    </div>
  );
}
