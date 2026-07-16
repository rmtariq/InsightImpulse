import type { DunKeywordRow, PrnWorkbookData, PriorityLevel, UrlSourceRow } from "../types/prn";

/** Compact fallback — full counts match workbook (56 Johor + 36 N9). */
export const prnMockWorkbook: PrnWorkbookData = {
  overview: [
    { metric: "DUN coverage", value: 92, category: "coverage" },
    { metric: "URL source records", value: 180, category: "sources" },
    { metric: "Enabled sources", value: 142, category: "sources" },
    { metric: "Local voice records", value: 48, category: "voices" },
    { metric: "Narrative themes", value: 24, category: "narrative" },
    { metric: "Generated query templates", value: 368, category: "queries" },
  ],
  electionCalendar: [
    {
      state: "Johor",
      assemblySeats: 56,
      assemblyStatus: "DISSOLVED",
      dissolutionDate: "2026-06-01",
      nominationDate: "2026-06-27",
      earlyVotingDate: "2026-07-07",
      pollingDate: "2026-07-11",
      operationalPhaseAsOf20260620: "T-7 nomination / pre-campaign surge",
      recommendedCrawlMode: "realtime Tier 1; hourly Tier 2; daily Tier 3",
      candidateRefreshTrigger: "2026-06-27 after official nominations",
      officialSourceUrl: "https://spr.gov.my",
      lastVerified: "2026-06-20",
    },
    {
      state: "Negeri Sembilan",
      assemblySeats: 36,
      assemblyStatus: "DISSOLVED",
      dissolutionDate: "2026-06-05",
      nominationDate: "2026-07-18",
      earlyVotingDate: "2026-07-28",
      pollingDate: "2026-08-01",
      operationalPhaseAsOf20260620: "pre-nomination / coalition and candidate watch",
      recommendedCrawlMode: "realtime Tier 1; hourly Tier 2; daily Tier 3",
      candidateRefreshTrigger: "2026-07-18 after official nominations",
      officialSourceUrl: "https://spr.gov.my",
      lastVerified: "2026-06-20",
    },
  ],
  dunKeywords: buildMockDuns(),
  urlSources: buildMockSources(),
  localVoiceCount: 48,
  narrativeThemeCount: 24,
  queryTemplateCount: 368,
};

function pri(level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"): PriorityLevel {
  return level;
}

function buildMockDuns(): DunKeywordRow[] {
  const johorNames = ["Buloh Kasap", "Jementah", "Skudai", "Kempas", "Permas"];
  const n9Names = ["Chennah", "Pertang", "Sikamat", "Paroi", "Nilai"];
  const rows: DunKeywordRow[] = [];
  for (let i = 1; i <= 56; i++) {
    const code = `N${String(i).padStart(2, "0")}`;
    rows.push({
      state: "Johor" as const,
      dunCode: code,
      dunName: johorNames[i % johorNames.length] + (i > 5 ? ` ${i}` : ""),
      parlimenCode: "P140",
      parlimenName: "Segamat",
      district: "Segamat",
      primaryKeywords: `${code}; DUN ${code}`,
      hashtags: "#PRNJohor #Johor2026",
      localLandmarks: "Pekan; FELDA",
      localIssues: "jalan; banjir; kos sara hidup",
      ethnicMix: "Melayu majoriti",
      languageMix: "BM; EN-MY",
      royalEntities: null,
      partyKeywords: "BN; PH; PN",
      issueKeywords: "subsidi; banjir",
      sensitivityLevel: i % 7 === 0 ? "CRITICAL" : i % 3 === 0 ? "HIGH" : "MEDIUM",
      sensitivityNotes: null,
      electionStatus2026: "DISSOLVED",
      nominationDate: "2026-06-27",
      earlyVotingDate: "2026-07-07",
      pollingDate: "2026-07-11",
      operationalPhase: "T-7 nomination",
      areaType: i % 2 ? "URBAN" : "MIXED",
      monitoringPriorityScore: 60 + (i % 35),
      monitoringPriority: pri(i % 7 === 0 ? "CRITICAL" : i % 3 === 0 ? "HIGH" : "MEDIUM"),
      electionKeywords2026: "PRN Johor 2026",
      developmentKeywords2026: "infrastruktur; ekonomi",
      serviceKeywords: "PBT; sampah; jalan",
      candidateKeywords: "TBD after nomination",
      queryBm: `("${code}" OR "DUN ${code}") AND (jalan OR banjir)`,
      queryZh: null,
      queryTa: null,
      sensitiveContentRule: "Standard editorial verification",
      lastVerified: "2026-06-20",
      sourceReference: "https://spr.gov.my",
    });
  }
  for (let i = 1; i <= 36; i++) {
    const code = `N${String(i).padStart(2, "0")}`;
    rows.push({
      state: "Negeri Sembilan" as const,
      dunCode: code,
      dunName: n9Names[i % n9Names.length] + (i > 5 ? ` ${i}` : ""),
      parlimenCode: "P128",
      parlimenName: "Seremban",
      district: "Jelebu",
      primaryKeywords: `${code}; DUN ${code}`,
      hashtags: "#PRNN9 #NegeriSembilan2026",
      localLandmarks: "Pekan; FELDA",
      localIssues: "luar bandar; jalan rosak",
      ethnicMix: "Melayu majoriti",
      languageMix: "BM; Rojak",
      royalEntities: "Tuanku Muhriz",
      partyKeywords: "PH; BN; PAS",
      issueKeywords: "MVV 2.0; sara hidup",
      sensitivityLevel: i % 5 === 0 ? "HIGH" : "MEDIUM",
      sensitivityNotes: i % 8 === 0 ? "Adat/royal context" : null,
      electionStatus2026: "DISSOLVED",
      nominationDate: "2026-07-18",
      earlyVotingDate: "2026-07-28",
      pollingDate: "2026-08-01",
      operationalPhase: "pre-nomination watch",
      areaType: "MIXED",
      monitoringPriorityScore: 55 + (i % 40),
      monitoringPriority: pri(i % 5 === 0 ? "HIGH" : "MEDIUM"),
      electionKeywords2026: "PRN N9 2026",
      developmentKeywords2026: "MVV 2.0; Port Dickson",
      serviceKeywords: "PBT; air; trafik",
      candidateKeywords: "TBD after nomination",
      queryBm: `("${code}" OR "DUN ${code}") AND (sara hidup OR jalan)`,
      queryZh: null,
      queryTa: null,
      sensitiveContentRule: "Classifier-only where adat context",
      lastVerified: "2026-06-20",
      sourceReference: "https://spr.gov.my",
    });
  }
  return rows;
}

function buildMockSources(): UrlSourceRow[] {
  const platforms = ["News", "Facebook", "X", "TikTok", "Instagram", "OfficialWeb"];
  const rows: UrlSourceRow[] = [];
  let id = 1;
  for (const state of ["Johor", "Negeri Sembilan", "All"] as const) {
    for (const platform of platforms) {
      rows.push({
        sourceId: `MOCK-${String(id++).padStart(4, "0")}`,
        state,
        platform,
        category: "media",
        name: `${platform} — ${state}`,
        url: `https://example.com/${platform.toLowerCase()}`,
        priority: id % 4 === 0 ? "CRITICAL" : id % 3 === 0 ? "HIGH" : "MEDIUM",
        crawlFrequency: id % 2 ? "hourly" : "daily",
        expectedVolume: "medium",
        language: "BM",
        notes: "Mock source",
        coverageLevel: state === "All" ? "national" : "state",
        ownerType: "media",
        enabled: id % 5 !== 0,
        verificationStatus: id % 4 === 0 ? "MANUAL_PLATFORM_CHECK_REQUIRED" : "DOMAIN_ONLY_CHECK",
        lastVerified: "2026-06-20",
        crawlMethod: "RSS/HTML",
        tosRisk: "LOW",
        electionRelevance: "supporting",
        auditNotes: null,
        sourceReference: null,
      });
    }
  }
  return rows;
}
