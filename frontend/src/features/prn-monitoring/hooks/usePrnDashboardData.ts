import { useCallback, useEffect, useState } from "react";
import { prnMockWorkbook } from "../mock/prnMockData";
import { loadPrnManifestJson } from "../lib/parsePrnWorkbook";
import { loadPrnWorkbook } from "../lib/parsePrnWorkbook";
import { buildPrnDashboardSummary } from "../lib/transformPrnData";
import type { PrnDashboardSummary } from "../types/prn";

const MANIFEST_URL = `${import.meta.env.BASE_URL}data/prn_excel_intel_manifest.json`;

export type DataMode = "auto" | "mock" | "workbook";

export function usePrnDashboardData(mode: DataMode = "auto") {
  const [summary, setSummary] = useState<PrnDashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataMode, setDataMode] = useState<DataMode>(mode);

  const loadMock = useCallback(() => {
    const s = buildPrnDashboardSummary(prnMockWorkbook, "mock", ["Using mock data"]);
    setSummary(s);
    setError(null);
  }, []);

  const loadManifest = useCallback(async () => {
    try {
      const { data, warnings } = await loadPrnManifestJson(MANIFEST_URL);
      setSummary(buildPrnDashboardSummary(data, "manifest", warnings));
      setError(null);
    } catch (e) {
      throw e;
    }
  }, []);

  const loadAuto = useCallback(async () => {
    setLoading(true);
    try {
      if (dataMode === "mock") {
        loadMock();
        return;
      }
      await loadManifest();
    } catch {
      loadMock();
      setError("Workbook/manifest unavailable — showing mock fallback.");
    } finally {
      setLoading(false);
    }
  }, [dataMode, loadManifest, loadMock]);

  useEffect(() => {
    loadAuto();
  }, [loadAuto]);

  const uploadWorkbook = useCallback(async (file: File) => {
    setLoading(true);
    try {
      const { data, warnings } = await loadPrnWorkbook(file);
      setSummary(buildPrnDashboardSummary(data, "workbook", warnings));
      setDataMode("workbook");
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to parse workbook");
      loadMock();
    } finally {
      setLoading(false);
    }
  }, [loadMock]);

  return {
    summary,
    loading,
    error,
    dataMode,
    setDataMode,
    reload: loadAuto,
    uploadWorkbook,
  };
}
