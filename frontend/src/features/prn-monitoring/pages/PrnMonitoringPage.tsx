import clsx from "clsx";
import { lazy, Suspense, useMemo, useState } from "react";
import { AlertCircle, Loader2 } from "lucide-react";
import { PrnHeader } from "../components/PrnHeader";
import { PrnFilterBar } from "../components/PrnFilterBar";
import { PrnKpiCards } from "../components/PrnKpiCards";
import { PrnElectionTimeline } from "../components/PrnElectionTimeline";
import { PrnDunTable } from "../components/PrnDunTable";
import { PrnDunDetailDrawer } from "../components/PrnDunDetailDrawer";
import { PrnQueryReadiness } from "../components/PrnQueryReadiness";
import { PrnOperationalInsights } from "../components/PrnOperationalInsights";
import { PrnCriticalSources } from "../components/PrnCriticalSources";
import { PrnOverviewBreakdown } from "../components/PrnOverviewBreakdown";
import { usePrnDashboardData } from "../hooks/usePrnDashboardData";
import { usePrnFilters } from "../hooks/usePrnFilters";
import { useTheme } from "../hooks/useTheme";
import { applyDunFilters, applySourceFilters, computeScopedKpis, filterByState, getCriticalSources } from "../lib/prnCalculations";
import { buildQueryReadiness } from "../lib/transformPrnData";
import type { DashboardTab, DunKeywordRow } from "../types/prn";

const PrnSourceCoverageCharts = lazy(() =>
  import("../components/PrnSourceCoverageCharts").then((m) => ({ default: m.PrnSourceCoverageCharts })),
);
const PrnSourceTable = lazy(() =>
  import("../components/PrnSourceTable").then((m) => ({ default: m.PrnSourceTable })),
);

function TabLoader() {
  return (
    <div className="flex items-center justify-center gap-2 py-12 text-slate-500">
      <Loader2 className="h-4 w-4 animate-spin" />
      Loading…
    </div>
  );
}

const TABS: { id: DashboardTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "sources", label: "Sources" },
  { id: "dun", label: "DUN Coverage" },
  { id: "queries", label: "Query Readiness" },
  { id: "operations", label: "Operations" },
];

export function PrnMonitoringPage() {
  const { summary, loading, error, dataMode, uploadWorkbook } = usePrnDashboardData("auto");
  const { filters, setState, update, reset, activeCount } = usePrnFilters();
  const { theme, toggleTheme } = useTheme();
  const [tab, setTab] = useState<DashboardTab>("overview");
  const [selectedDun, setSelectedDun] = useState<DunKeywordRow | null>(null);

  const platforms = useMemo(() => {
    if (!summary) return [];
    return [...new Set(summary.urlSources.map((s) => s.platform))].sort();
  }, [summary]);

  const districts = useMemo(() => {
    if (!summary) return [];
    return [...new Set(summary.dunKeywords.map((d) => d.district).filter(Boolean) as string[])].sort();
  }, [summary]);

  const areaTypes = useMemo(() => {
    if (!summary) return [];
    return [...new Set(summary.dunKeywords.map((d) => d.areaType).filter(Boolean) as string[])].sort();
  }, [summary]);

  const electionStatuses = useMemo(() => {
    if (!summary) return [];
    return [...new Set(summary.dunKeywords.map((d) => d.electionStatus2026).filter(Boolean))].sort();
  }, [summary]);

  const scopedKpis = useMemo(() => {
    if (!summary) return null;
    return computeScopedKpis(
      {
        overview: summary.overviewMetrics,
        overviewBreakdown: summary.overviewBreakdown,
        electionCalendar: summary.electionCalendar,
        dunKeywords: summary.dunKeywords,
        urlSources: summary.urlSources,
        localVoiceCount: summary.kpis.localVoiceRecords,
        narrativeThemeCount: summary.kpis.narrativeThemes,
        queryTemplateCount: summary.kpis.generatedQueryTemplates,
        localVoiceCountByState: summary.localVoiceCountByState,
        queryTemplateCountByState: summary.queryTemplateCountByState,
      },
      filters.state,
    );
  }, [summary, filters.state]);

  const criticalSources = useMemo(
    () => (summary ? getCriticalSources(applySourceFilters(summary.urlSources, { ...filters, platform: "ALL", enabledStatus: "ALL", verificationStatus: "ALL", monitoringPriority: "ALL", search: "" })) : []),
    [summary, filters.state],
  );
  const filteredSources = useMemo(
    () => (summary ? applySourceFilters(summary.urlSources, filters) : []),
    [summary, filters],
  );

  const filteredDuns = useMemo(
    () => (summary ? applyDunFilters(summary.dunKeywords, filters) : []),
    [summary, filters],
  );

  const scopedQueryReadiness = useMemo(() => {
    if (!summary) return null;
    const duns = filterByState(summary.dunKeywords, filters.state);
    return buildQueryReadiness(duns);
  }, [summary, filters.state]);

  if (loading && !summary) {
    return (
      <div className="flex h-full items-center justify-center gap-2 text-slate-400">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading PRN intelligence…
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PrnHeader
        lastUpdated={summary.lastUpdated}
        state={filters.state}
        onStateChange={setState}
        dataMode={dataMode}
        onUpload={uploadWorkbook}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      <PrnFilterBar
        filters={filters}
        onChange={update}
        onReset={reset}
        activeCount={activeCount}
        platforms={platforms}
        districts={districts}
        duns={filteredDuns.slice(0, 200)}
        areaTypes={areaTypes}
        electionStatuses={electionStatuses}
        showDunFilters={tab === "dun"}
      />

      {(error || summary.warnings.length > 0) && (
        <div className="border-b border-amber-900/50 bg-amber-950/30 px-4 py-2 text-xs text-amber-200 sm:px-6">
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              {error && <p>{error}</p>}
              {summary.warnings.map((w) => (
                <p key={w}>{w}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      <nav className="flex shrink-0 gap-1 border-b border-surface-border bg-surface px-4 sm:px-6">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={clsx(
              "border-b-2 px-3 py-2.5 text-xs font-medium transition",
              tab === t.id
                ? "border-sky-500 text-sky-300"
                : "border-transparent text-slate-500 hover:text-slate-300",
            )}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="flex-1 overflow-y-auto px-4 py-4 sm:px-6">
        {tab === "overview" && (
          <div className="space-y-4">
            {scopedKpis && <PrnKpiCards kpis={scopedKpis} stateFilter={filters.state} />}
            <PrnOverviewBreakdown breakdown={summary.overviewBreakdown} stateFilter={filters.state} />
            <div className="grid gap-4 lg:grid-cols-2">
              <section>
                <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Election timeline</h2>
                <PrnElectionTimeline rows={summary.electionCalendar.filter((c) => filters.state === "Both" || c.state === filters.state)} />
              </section>
              <section>
                <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Critical sources</h2>
                <PrnCriticalSources sources={criticalSources} />
              </section>
            </div>
            <section>
              <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Operational insights</h2>
              <PrnOperationalInsights insights={summary.operationalInsights} />
            </section>
          </div>
        )}

        {tab === "sources" && (
          <div className="space-y-4">
            <PrnCriticalSources sources={criticalSources} maxItems={8} />
            <Suspense fallback={<TabLoader />}>
              <PrnSourceCoverageCharts sources={summary.urlSources} filters={filters} />
              <PrnSourceTable data={filteredSources} />
            </Suspense>
          </div>
        )}

        {tab === "dun" && <PrnDunTable data={filteredDuns} onSelect={setSelectedDun} />}

        {tab === "queries" && scopedQueryReadiness && <PrnQueryReadiness data={scopedQueryReadiness} />}

        {tab === "operations" && (
          <div className="space-y-4">
            <PrnOperationalInsights insights={summary.operationalInsights} />
            {summary.overviewBreakdown?.operationalNotes.length ? (
              <section>
                <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Operational notes (workbook)</h2>
                <ol className="list-decimal space-y-2 pl-4 text-xs text-slate-300">
                  {summary.overviewBreakdown.operationalNotes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ol>
              </section>
            ) : null}
            <section>
              <h2 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Overview metrics</h2>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {summary.overviewMetrics.map((m) => (
                  <div key={m.metric} className="rounded border border-surface-border bg-surface-raised p-3">
                    <p className="text-[10px] text-slate-500">{m.metric}</p>
                    <p className="tabular-nums text-lg font-semibold text-slate-100">{m.value}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </main>

      <PrnDunDetailDrawer dun={selectedDun} onClose={() => setSelectedDun(null)} />
    </div>
  );
}
