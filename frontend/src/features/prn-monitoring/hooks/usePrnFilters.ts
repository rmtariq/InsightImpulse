import { useCallback, useMemo, useState } from "react";
import type { PrnDashboardFilters, StateFilter } from "../types/prn";

export const DEFAULT_FILTERS: PrnDashboardFilters = {
  state: "Both",
  platform: "ALL",
  district: "ALL",
  dun: "ALL",
  areaType: "ALL",
  electionStatus: "ALL",
  monitoringPriority: "ALL",
  enabledStatus: "ALL",
  verificationStatus: "ALL",
  search: "",
};

export function usePrnFilters(initial?: Partial<PrnDashboardFilters>) {
  const [filters, setFilters] = useState<PrnDashboardFilters>({ ...DEFAULT_FILTERS, ...initial });

  const setState = useCallback((state: StateFilter) => {
    setFilters((f) => ({ ...f, state, dun: "ALL", district: "ALL" }));
  }, []);

  const update = useCallback((patch: Partial<PrnDashboardFilters>) => {
    setFilters((f) => ({ ...f, ...patch }));
  }, []);

  const reset = useCallback(() => setFilters(DEFAULT_FILTERS), []);

  const activeCount = useMemo(() => {
    let n = 0;
    if (filters.state !== "Both") n++;
    if (filters.platform !== "ALL") n++;
    if (filters.district !== "ALL") n++;
    if (filters.dun !== "ALL") n++;
    if (filters.areaType !== "ALL") n++;
    if (filters.electionStatus !== "ALL") n++;
    if (filters.monitoringPriority !== "ALL") n++;
    if (filters.enabledStatus !== "ALL") n++;
    if (filters.verificationStatus !== "ALL") n++;
    if (filters.search.trim()) n++;
    return n;
  }, [filters]);

  return { filters, setState, update, reset, activeCount };
}
