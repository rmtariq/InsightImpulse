/**
 * Johor war-room scenario sliders — mirrors scripts/johor_seat_analytics.py
 */
(function (global) {
  const MADANI_MALAY_BACKLASH_MAX = 0.28;
  const PH_TRUST_COLLAPSE_SIGNAL = 0.18;
  const ECON_UNCERTAINTY_PH_BASE = 0.10;
  const ECON_UNCERTAINTY_CHINESE_EXTRA = 0.10;
  const MAJORITY_JOHOR = 29;
  const UMNO_SOLO_PAS = 55;
  const UMNO_SOLO_BN = 45;

  const MULT = {
    madani: { rendah: 0.6, sederhana: 1.0, tinggi: 1.35 },
    phTrust: { rendah: 0.65, sederhana: 1.0, tinggi: 1.4 },
  };

  const STORAGE_KEY = "johorScenarioSettings";

  function clamp(v, lo = 8, hi = 92) {
    return Math.round(Math.max(lo, Math.min(hi, v)) * 10) / 10;
  }

  function loadSettings() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return { madaniLevel: "sederhana", phTrustLevel: "sederhana", ...JSON.parse(raw) };
    } catch (_) {}
    return { madaniLevel: "sederhana", phTrustLevel: "sederhana" };
  }

  function saveSettings(s) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); } catch (_) {}
  }

  function getMultipliers(settings) {
    const s = settings || loadSettings();
    return {
      madani: MULT.madani[s.madaniLevel] ?? 1,
      phTrust: MULT.phTrust[s.phTrustLevel] ?? 1,
    };
  }

  function pasSoloVsBnEdge(pasSoloPct, bnPct) {
    const gap = Math.round((pasSoloPct - bnPct) * 10) / 10;
    if (Math.abs(gap) <= 3.0) return { edge: "close", gap };
    return gap > 0 ? { edge: "pas_lead", gap } : { edge: "bn_lead", gap };
  }

  function umnoSoloDataAdj(km, maj, malay, chinese, sm, madaniMult = 1) {
    const malayW = Math.max(0, Math.min(1, (malay - 42) / 48));
    const adjTable = { ultra_marginal: 2, super_marginal: 1.5, marginal: 1, semi_safe: -0.5, safe: -1 };
    let adj = (adjTable[km] ?? 0) + (malayW - 0.5) * 2;
    if (maj <= 400) adj += 1;
    else if (maj <= 800) adj += 0.5;
    adj += Math.min(0.8, chinese / 100 * 0.6) - 0.2;
    const mentions = sm?.mentions_total || 0;
    if (mentions >= 2) adj += Math.max(-1, Math.min(1, ((sm.neg_pct || 0) - 40) * 0.05));
    adj = Math.max(-3, Math.min(3, adj * madaniMult));
    return adj;
  }

  function umnoSoloSplit(seat, meta, madaniMult) {
    const sm = { mentions_total: seat?.socmedMentions || 0, neg_pct: seat?.socmedNegPct || 0 };
    const adj = umnoSoloDataAdj(
      meta.kategoriMargin || "marginal",
      meta.majority2022 ?? seat?.majority2022 ?? 0,
      meta.malayPct ?? 55,
      meta.chinesePct ?? 30,
      sm,
      madaniMult,
    );
    let pasPp = Math.max(52, Math.min(58, UMNO_SOLO_PAS + adj));
    const bnPp = 100 - pasPp;
    return { pasSolo: pasPp, bn: bnPp, adj, gap: pasPp - bnPp };
  }

  function applyPostMadani(base, meta, madaniMult, phTrustMult, seat) {
    const party = (meta.party2022 || "").toUpperCase();
    const bloc = (meta.bloc2022 || "").toUpperCase();
    const km = meta.kategoriMargin || "marginal";
    const malay = meta.malayPct ?? 55;
    const chinese = meta.chinesePct ?? 30;
    const malayW = Math.max(0, Math.min(1, (malay - 42) / 48));

    let pPas = (base.pasWinProb || 0) / 100;
    let bn = (base.bnSoloWinProb || 0) / 100;
    let ph = (base.phWinProb || 0) / 100;
    let pasSolo = (base.pasSoloWinProb || 0) / 100;
    let pasMn = (base.pasMnWinProb || 0) / 100;
    const ctx = { madaniBnPenaltyPct: 0, phTrustPenaltyPct: 0, econPhPenaltyPct: 0, malayPct: malay };

    if (party === "UMNO") {
      const split = umnoSoloSplit(seat, meta, madaniMult);
      pasSolo = split.pasSolo / 100;
      bn = split.bn / 100;
      ctx.soloScenarioBase = `${UMNO_SOLO_PAS}/${UMNO_SOLO_BN}`;
      ctx.soloDataAdjPct = split.adj;
      ctx.hybridGapTargetPct = split.gap;
      ctx.hybridModel = true;
    }

    if (bloc === "BN" || ["UMNO", "MCA", "MIC"].includes(party)) {
      let pen = (0.08 + malayW * MADANI_MALAY_BACKLASH_MAX) * madaniMult;
      if (party === "UMNO") pen += 0.03 * madaniMult;
      if (km === "ultra_marginal" || km === "super_marginal") pen += 0.04 * madaniMult;
      const bnBefore = bn;
      const bnAfter = bn * Math.max(0.38, 1 - pen);
      const swing = bnBefore - bnAfter;
      if (party === "UMNO") {
        pPas = Math.min(0.72, pPas + swing * 0.55);
        pasMn = Math.min(0.96, pasMn + swing * 0.72 + malayW * 0.02);
      } else {
        bn = bnAfter;
        pasSolo = Math.min(0.72, pasSolo + swing * 0.40);
        pPas = Math.min(0.72, pPas + swing * 0.55);
        pasMn = Math.min(0.96, pasMn + swing * 0.72 + malayW * 0.02);
      }
      ctx.madaniBnPenaltyPct = Math.round(pen * 1000) / 10;
    }

    if (["DAP", "PKR", "AMANAH"].includes(party) || bloc === "PH") {
      let phPen = PH_TRUST_COLLAPSE_SIGNAL * phTrustMult;
      if (party === "DAP") phPen += 0.06 * phTrustMult;
      if (malay >= 35) phPen += 0.04 * phTrustMult;
      let econPen = ECON_UNCERTAINTY_PH_BASE;
      if (chinese >= 30) econPen += ECON_UNCERTAINTY_CHINESE_EXTRA * Math.min(1, chinese / 55);
      if (party === "DAP" && chinese >= 40) econPen += 0.04;
      phPen += econPen * phTrustMult;
      if (chinese >= 45 && malay < 42) phPen *= 0.85;
      const phBefore = ph;
      ph *= Math.max(0.20, 1 - phPen);
      const swingPh = phBefore - ph;
      if (party !== "UMNO") {
        pasSolo += swingPh * 0.30;
        bn += swingPh * 0.25;
      }
      pPas = Math.min(0.68, pPas + swingPh * 0.22);
      ctx.phTrustPenaltyPct = Math.round(phPen * 1000) / 10;
      ctx.econPhPenaltyPct = Math.round(econPen * 1000) / 10;
    }

    if (["MCA", "MIC"].includes(party)) {
      bn *= 0.96;
      ph = Math.max(ph, 0.02);
    }

    const pasSoloPct = party === "UMNO" ? Math.round(pasSolo * 1000) / 10 : clamp(pasSolo * 100);
    const bnPct = party === "UMNO" ? Math.round(bn * 1000) / 10 : clamp(bn * 100);
    const { edge, gap } = pasSoloVsBnEdge(pasSoloPct, bnPct);
    ctx.pasSoloVsBn = edge;
    ctx.pasSoloBnGapPct = gap;

    return {
      pasWinProb: clamp(pPas * 100),
      pasSoloWinProb: pasSoloPct,
      pasMnWinProb: clamp(pasMn * 100),
      bnSoloWinProb: bnPct,
      phWinProb: clamp(ph * 100),
      pasSoloVsBn: edge,
      pasSoloBnGapPct: gap,
      modelContext: ctx,
    };
  }

  function seatScenarios(seat, settings) {
    if (!seat) return null;
    const base = seat.scenarioBase || {
      pasWinProb: seat.pasWinProb,
      pasSoloWinProb: seat.pasSoloWinProb,
      pasMnWinProb: seat.pasMnWinProb,
      bnSoloWinProb: seat.bnSoloWinProb,
      phWinProb: seat.phWinProb,
    };
    const meta = seat.scenarioMeta || {
      party2022: seat.party2022 || seat.semasaParti,
      bloc2022: seat.winner2022 || seat.party,
      kategoriMargin: seat.kategoriMargin,
      malayPct: seat.census?.districtEthnicityPct?.malay ?? seat.modelContext?.malayPct ?? 55,
      chinesePct: seat.census?.districtEthnicityPct?.chinese ?? 55,
      majority2022: seat.majority2022 ?? seat.majority,
    };
    const { madani, phTrust } = getMultipliers(settings);
    const adj = applyPostMadani(base, meta, madani, phTrust, seat);
    return { ...seat, ...adj, _fromSlider: true };
  }

  function aggregateTotals(seats, settings) {
    const rows = (seats || []).map((s) => seatScenarios(s, settings));
    const sum = (k) => rows.reduce((a, s) => a + (s[k] || 0), 0) / 100;
    const umno = rows.filter((s) => (s.party2022 || s.semasaParti || "").toUpperCase() === "UMNO");
    const umnoFlipExp = Math.round(umno.reduce((a, s) => a + (s.pasSoloWinProb || 0) / 100, 0) * 10) / 10;
    return {
      pasSolo: Math.round(sum("pasSoloWinProb") * 10) / 10,
      pasMn: Math.round(sum("pasMnWinProb") * 10) / 10,
      bnSolo: Math.round(sum("bnSoloWinProb") * 10) / 10,
      ph: Math.round(sum("phWinProb") * 10) / 10,
      pasFlip50: rows.filter((s) => (s.pasSoloWinProb || 0) >= 50).length,
      mn50: rows.filter((s) => (s.pasMnWinProb || 0) >= 50).length,
      umnoFlipExpected: umnoFlipExp,
      umnoTotal: umno.length,
    };
  }

  function computeMbInsight(seats, settings) {
    const tot = aggregateTotals(seats, settings);
    const rows = (seats || []).map((s) => seatScenarios(s, settings));
    const pasMnExp = tot.pasMn;
    const pasSoloExp = tot.pasSolo;
    const mnMajority = pasMnExp >= MAJORITY_JOHOR;
    return {
      expectedPasSoloSeats: pasSoloExp,
      expectedMnBlocSeats: pasMnExp,
      umnoSoloInsight: {
        soloScenarioBase: `PAS ${UMNO_SOLO_PAS}% vs UMNO ${UMNO_SOLO_BN}%`,
        expectedFlipsFromUmno: tot.umnoFlipExpected,
        notAll33Wins: `Dijangka ~${tot.umnoFlipExpected}/${tot.umnoTotal} flip dari kerusi UMNO — bukan 33/33 menang.`,
      },
      mnReachesMajority: mnMajority,
      pasMbEligibility: mnMajority && tot.umnoFlipExpected >= 8 ? "layak_runding" : "perlu_flip_lagi",
      mbNote: `MB Johor ≥${MAJORITY_JOHOR}/56. MN ~${pasMnExp} kerusi. Flip UMNO dijangka ~${tot.umnoFlipExpected}/33 (bukan 33/33). MB = rundingan MN.`,
    };
  }

  global.JohorScenarioModel = {
    MULT,
    UMNO_SOLO_PAS,
    UMNO_SOLO_BN,
    loadSettings,
    saveSettings,
    getMultipliers,
    seatScenarios,
    aggregateTotals,
    computeMbInsight,
    pasSoloVsBnEdge,
    levelLabels: {
      madani: { rendah: "Rendah", sederhana: "Sederhana", tinggi: "Tinggi" },
      phTrust: { rendah: "Rendah", sederhana: "Sederhana", tinggi: "Tinggi" },
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
