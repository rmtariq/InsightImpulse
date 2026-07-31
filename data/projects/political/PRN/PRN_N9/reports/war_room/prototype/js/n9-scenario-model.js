/**
 * N9 Command Center scenario — mirrors scripts/n9_seat_scenario_model.py
 */
(function (global) {
  const MAJORITY_N9 = 19;
  const PAS_SOLO_LEAD_BASE = 55;
  const UMNO_SOLO_BASE = 45;

  function aggregateTotals(seats) {
    const rows = seats || [];
    const sum = (k) => rows.reduce((a, s) => a + (s[k] || 0), 0) / 100;
    const contest = rows.filter((s) => s.scenarioMeta?.pasSoloContest27 || s.modelContext?.pasSoloContest27);
    const lead = rows.filter((s) => s.scenarioMeta?.pasSoloLead13 || s.modelContext?.pasSoloLead13);
    const leadFlip = lead.reduce((a, s) => a + (s.pasSoloWinProb || 0) / 100, 0);
    return {
      pasSolo: Math.round(sum("pasSoloWinProb") * 10) / 10,
      pasMn: Math.round(sum("pasMnWinProb") * 10) / 10,
      umnoSolo: Math.round(sum("umnoSoloWinProb") * 10) / 10,
      ph: Math.round(sum("phWinProb") * 10) / 10,
      pasLead13: lead.length,
      contest27: contest.length,
      leadFlipExpected: Math.round(leadFlip * 10) / 10,
      pasFlip50: rows.filter((s) => (s.pasSoloWinProb || 0) >= 50).length,
    };
  }

  function computeMnInsight(seats) {
    const tot = aggregateTotals(seats);
    const leadCodes = (seats || [])
      .filter((s) => s.scenarioMeta?.pasSoloLead13 || s.modelContext?.pasSoloLead13)
      .map((s) => s.id);
    return {
      pasMn23: 23,
      umnoMn13: 13,
      pasSoloContest27: tot.contest27 || 27,
      pasSoloLead13: tot.pasLead13,
      pasSoloLeadCodes: leadCodes,
      expectedFlipsFromLead13: tot.leadFlipExpected,
      expectedMnBlocSeats: tot.pasMn,
      mnReachesMajority: tot.pasMn >= MAJORITY_N9,
      mbNote: `Agihan MN (HQ): PAS/PN 13 kerusi (9 wajib + 4 berhasrat) · UMNO/BN 23 kerusi. Jangkaan bloc PAS+MN ~${tot.pasMn} kerusi. PAS realistik cerah ~3 drpd 4 berhasrat (Chennah terbaik · Nilai stretch).`,
      soloInsight: {
        contest27Note: `Senario solo Melayu (27 kerusi): PAS dijangka lebih tinggi daripada UMNO — ${tot.pasLead13} jelas, ${Math.max(0, (tot.contest27 || 27) - tot.pasLead13)} rapat.`,
        notAll27Wins: `Bukan 27/27 menang — % model ≠ kemenangan pasti.`,
      },
    };
  }

  global.N9ScenarioModel = {
    MAJORITY_N9,
    PAS_SOLO_LEAD_BASE,
    UMNO_SOLO_BASE,
    aggregateTotals,
    computeMnInsight,
  };
})(typeof window !== "undefined" ? window : globalThis);
