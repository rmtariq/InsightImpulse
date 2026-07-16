import type { DunKeywordRow, PrnDashboardFilters } from "../types/prn";

interface Props {
  filters: PrnDashboardFilters;
  onChange: (patch: Partial<PrnDashboardFilters>) => void;
  onReset: () => void;
  activeCount: number;
  platforms: string[];
  districts: string[];
  duns: DunKeywordRow[];
  areaTypes: string[];
  electionStatuses: string[];
  showDunFilters?: boolean;
}

export function PrnFilterBar({
  filters,
  onChange,
  onReset,
  activeCount,
  platforms,
  districts,
  duns,
  areaTypes,
  electionStatuses,
  showDunFilters = true,
}: Props) {
  return (
    <div className="border-b border-surface-border bg-surface px-4 py-3 sm:px-6">
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
        <select
          value={filters.platform}
          onChange={(e) => onChange({ platform: e.target.value })}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1.5 text-xs text-slate-200"
        >
          <option value="ALL">All platforms</option>
          {platforms.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <select
          value={filters.district}
          onChange={(e) => onChange({ district: e.target.value })}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1.5 text-xs text-slate-200"
        >
          <option value="ALL">All districts</option>
          {districts.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        <select
          value={filters.dun}
          onChange={(e) => onChange({ dun: e.target.value })}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1.5 text-xs text-slate-200"
        >
          <option value="ALL">All DUN</option>
          {duns.map((d) => (
            <option key={`${d.state}-${d.dunCode}`} value={d.dunCode}>{d.dunCode} {d.dunName}</option>
          ))}
        </select>
        <select
          value={filters.monitoringPriority}
          onChange={(e) => onChange({ monitoringPriority: e.target.value as PrnDashboardFilters["monitoringPriority"] })}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1.5 text-xs text-slate-200"
        >
          <option value="ALL">All priority</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
        {showDunFilters && (
          <>
            <select
              value={filters.areaType}
              onChange={(e) => onChange({ areaType: e.target.value })}
              className="rounded border border-surface-border bg-surface-raised px-2 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All area types</option>
              {areaTypes.map((a) => (
                <option key={a} value={a}>{a.replace(/_/g, " ")}</option>
              ))}
            </select>
            <select
              value={filters.electionStatus}
              onChange={(e) => onChange({ electionStatus: e.target.value })}
              className="rounded border border-surface-border bg-surface-raised px-2 py-1.5 text-xs text-slate-200"
            >
              <option value="ALL">All election status</option>
              {electionStatuses.map((s) => (
                <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
              ))}
            </select>
          </>
        )}
        <select
          value={filters.enabledStatus}
          onChange={(e) => onChange({ enabledStatus: e.target.value as PrnDashboardFilters["enabledStatus"] })}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1.5 text-xs text-slate-200"
        >
          <option value="ALL">Enabled: all</option>
          <option value="ENABLED">Enabled only</option>
          <option value="DISABLED">Disabled only</option>
        </select>
        <select
          value={filters.verificationStatus}
          onChange={(e) => onChange({ verificationStatus: e.target.value })}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1.5 text-xs text-slate-200"
        >
          <option value="ALL">Verification: all</option>
          <option value="VERIFIED">Verified</option>
          <option value="DOMAIN">Domain check</option>
          <option value="MANUAL">Manual pending</option>
        </select>
        <input
          type="search"
          placeholder="Search…"
          value={filters.search}
          onChange={(e) => onChange({ search: e.target.value })}
          className="rounded border border-surface-border bg-surface-raised px-2 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 xl:col-span-2"
        />
      </div>
      {activeCount > 0 && (
        <button type="button" onClick={onReset} className="mt-2 text-xs text-sky-400 hover:text-sky-300">
          Reset {activeCount} filter{activeCount > 1 ? "s" : ""}
        </button>
      )}
    </div>
  );
}
