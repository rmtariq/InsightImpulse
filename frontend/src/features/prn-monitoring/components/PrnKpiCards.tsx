import { formatNumber, formatPercent } from "../lib/prnFormatters";
import type { PrnDashboardSummary, StateFilter } from "../types/prn";

interface Props {
  kpis: PrnDashboardSummary["kpis"];
  stateFilter: StateFilter;
}

export function PrnKpiCards({ kpis, stateFilter }: Props) {
  const stateLabel =
    stateFilter === "Both"
      ? "Johor + N9"
      : stateFilter === "Johor"
        ? "Johor only"
        : "N9 only";

  const avgSubtitle =
    stateFilter === "Both"
      ? `Johor ${kpis.avgMonitoringPriorityScoreByState.Johor} · N9 ${kpis.avgMonitoringPriorityScoreByState["Negeri Sembilan"]}`
      : `${stateFilter} avg`;

  const cards: {
    key: keyof PrnDashboardSummary["kpis"];
    title: string;
    subtitle?: string;
    fmt?: (n: number) => string;
    skip?: boolean;
  }[] = [
    { key: "totalDun", title: "Total DUN", subtitle: stateLabel },
    { key: "totalUrlSources", title: "URL Sources", subtitle: stateLabel },
    { key: "enabledSources", title: "Enabled Sources" },
    { key: "enabledRate", title: "Enabled Rate", fmt: formatPercent },
    { key: "localVoiceRecords", title: "Local Voice Records" },
    { key: "narrativeThemes", title: "Narrative Themes" },
    { key: "generatedQueryTemplates", title: "Query Templates" },
    { key: "avgMonitoringPriorityScore", title: "Avg Priority Score", subtitle: avgSubtitle },
    { key: "avgMonitoringPriorityScoreByState", title: "", skip: true },
  ];

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-8">
      {cards.filter((c) => !c.skip).map(({ key, title, subtitle, fmt }) => (
        <div key={key} className="rounded border border-surface-border bg-surface-raised p-3">
          <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500">{title}</p>
          <p className="mt-1 tabular-nums text-xl font-semibold text-slate-100">
            {fmt ? fmt(kpis[key] as number) : formatNumber(kpis[key] as number)}
          </p>
          {subtitle && <p className="mt-0.5 text-[10px] text-slate-500">{subtitle}</p>}
        </div>
      ))}
    </div>
  );
}
