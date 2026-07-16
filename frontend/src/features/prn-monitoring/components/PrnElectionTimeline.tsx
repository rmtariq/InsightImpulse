import { formatDate } from "../lib/prnFormatters";
import { daysUntil } from "../lib/prnCalculations";
import { StatusBadge } from "./StatusBadge";
import type { ElectionCalendarRow } from "../types/prn";

export function PrnElectionTimeline({ rows }: { rows: ElectionCalendarRow[] }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {rows.map((row) => {
        const tPolling = daysUntil(row.pollingDate);
        return (
          <div key={row.state} className="rounded border border-surface-border bg-surface-raised p-4">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h3 className="font-semibold text-slate-100">{row.state}</h3>
                <p className="text-xs text-slate-500">{row.assemblySeats} DUN seats</p>
              </div>
              <StatusBadge status={row.assemblyStatus} />
            </div>
            <div className="mt-4 space-y-2 text-xs">
              {[
                ["Dissolution", row.dissolutionDate],
                ["Nomination", row.nominationDate],
                ["Early voting", row.earlyVotingDate],
                ["Polling", row.pollingDate],
              ].map(([label, date]) => (
                <div key={String(label)} className="flex justify-between border-b border-surface-border/60 py-1.5">
                  <span className="text-slate-500">{label}</span>
                  <span className={`tabular-nums ${label === "Polling" ? "font-semibold text-sky-300" : "text-slate-300"}`}>
                    {formatDate(date as string | null)}
                    {label === "Polling" && tPolling != null && (
                      <span className="ml-1 text-slate-500">(T{tPolling}d)</span>
                    )}
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[11px] text-slate-400">{row.operationalPhaseAsOf20260620}</p>
            <p className="mt-1 text-[11px] text-slate-500">
              Crawl: {row.recommendedCrawlMode}
            </p>
            <p className="mt-1 text-[10px] text-slate-600">
              Candidate refresh: {row.candidateRefreshTrigger}
            </p>
          </div>
        );
      })}
    </div>
  );
}
