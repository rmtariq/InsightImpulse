export type PrnState = "Johor" | "Negeri Sembilan";
export type StateFilter = PrnState | "Both";
export type PriorityLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type DashboardTab = "overview" | "sources" | "dun" | "queries" | "operations";

export interface OverviewMetricRow {
  metric: string;
  value: string | number;
  category?: string;
  notes?: string;
}

export interface OverviewBreakdown {
  updatedLabel?: string | null;
  kpis: OverviewMetricRow[];
  dunByState: { state: string; stateCode: string; dunCount: number }[];
  dunByPriority: { priority: PriorityLevel | string; dunCount: number }[];
  operationalNotes: string[];
}

export interface ElectionCalendarRow {
  state: PrnState;
  assemblySeats: number;
  assemblyStatus: string;
  dissolutionDate: string | null;
  nominationDate: string | null;
  earlyVotingDate: string | null;
  pollingDate: string | null;
  operationalPhaseAsOf20260620: string;
  recommendedCrawlMode: string;
  candidateRefreshTrigger: string;
  officialSourceUrl: string | null;
  lastVerified: string | null;
}

export interface DunKeywordRow {
  state: PrnState;
  dunCode: string;
  dunName: string;
  parlimenCode: string | null;
  parlimenName: string | null;
  district: string | null;
  primaryKeywords: string | null;
  hashtags: string | null;
  localLandmarks: string | null;
  localIssues: string | null;
  ethnicMix: string | null;
  languageMix: string | null;
  royalEntities: string | null;
  partyKeywords: string | null;
  issueKeywords: string | null;
  sensitivityLevel: PriorityLevel | string;
  sensitivityNotes: string | null;
  electionStatus2026: string;
  nominationDate: string | null;
  earlyVotingDate: string | null;
  pollingDate: string | null;
  operationalPhase: string | null;
  areaType: string | null;
  monitoringPriorityScore: number;
  monitoringPriority: PriorityLevel;
  electionKeywords2026: string | null;
  developmentKeywords2026: string | null;
  serviceKeywords: string | null;
  candidateKeywords: string | null;
  queryBm: string | null;
  queryZh: string | null;
  queryTa: string | null;
  sensitiveContentRule: string | null;
  lastVerified: string | null;
  sourceReference: string | null;
}

export interface UrlSourceRow {
  sourceId: string;
  state: PrnState | "All";
  platform: string;
  category: string;
  name: string;
  url: string;
  priority: PriorityLevel | string;
  crawlFrequency: string;
  expectedVolume: string | null;
  language: string | null;
  notes: string | null;
  coverageLevel: string | null;
  ownerType: string | null;
  enabled: boolean;
  verificationStatus: string;
  lastVerified: string | null;
  crawlMethod: string | null;
  tosRisk: string | null;
  electionRelevance: string | null;
  auditNotes: string | null;
  sourceReference: string | null;
}

export interface PrnDashboardFilters {
  state: StateFilter;
  platform: string;
  district: string;
  dun: string;
  areaType: string;
  electionStatus: string;
  monitoringPriority: PriorityLevel | "ALL";
  enabledStatus: "ALL" | "ENABLED" | "DISABLED";
  verificationStatus: string;
  search: string;
}

export interface QueryReadinessSummary {
  totalDun: number;
  withQueryBm: number;
  withHashtags: number;
  withLocalLandmarks: number;
  withLocalIssues: number;
  withQueryZh: number;
  withQueryTa: number;
  topPriorityDuns: DunKeywordRow[];
}

export interface PrnOperationalInsight {
  id: string;
  severity: "info" | "warning" | "critical";
  text: string;
}

export interface PrnDashboardSummary {
  lastUpdated: string;
  dataMode: "mock" | "workbook" | "manifest";
  overviewMetrics: OverviewMetricRow[];
  electionCalendar: ElectionCalendarRow[];
  dunKeywords: DunKeywordRow[];
  urlSources: UrlSourceRow[];
  queryReadiness: QueryReadinessSummary;
  operationalInsights: PrnOperationalInsight[];
  kpis: {
    totalDun: number;
    totalUrlSources: number;
    enabledSources: number;
    enabledRate: number;
    localVoiceRecords: number;
    narrativeThemes: number;
    generatedQueryTemplates: number;
    avgMonitoringPriorityScore: number;
    avgMonitoringPriorityScoreByState: Record<PrnState, number>;
  };
  overviewBreakdown?: OverviewBreakdown;
  localVoiceCountByState?: Partial<Record<PrnState, number>>;
  queryTemplateCountByState?: Partial<Record<PrnState, number>>;
  warnings: string[];
}

export interface PrnWorkbookData {
  overview: OverviewMetricRow[];
  overviewBreakdown?: OverviewBreakdown;
  electionCalendar: ElectionCalendarRow[];
  dunKeywords: DunKeywordRow[];
  urlSources: UrlSourceRow[];
  localVoiceCount: number;
  narrativeThemeCount: number;
  queryTemplateCount: number;
  localVoiceCountByState?: Partial<Record<PrnState, number>>;
  queryTemplateCountByState?: Partial<Record<PrnState, number>>;
}
