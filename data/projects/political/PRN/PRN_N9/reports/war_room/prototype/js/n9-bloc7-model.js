/**
 * N9 — 7 Blok Senario (PAS N9 HQ · Jun 2026)
 * Hybrid: SPR Helaian Mata 2023 + model PAS23 (pasSoloWinProb dll.)
 *
 * Logik (Jun 2026):
 *   #1 PAS Solo / #2 UMNO Solo → model win-prob (Σ/100 kerusi dijangka)
 *   #3 MN / #4 PN / #5 PH / #7 PN+ → SPR 2-penjuru
 *   #4 PN = Team PN (PAS+Pejuang+Wawasan+Gerakan+PRIM) — TANPA Bersatu
 *   #7 PN+ = Team PN penuh + Bersatu (bloc SPR PN 2023)
 *   #6 Bersama → pecah undi PH (kerusi flip ke MN)
 */
(function (global) {
  const MAJORITY_N9 = 19;
  const TOTAL_DUN = 36;
  /** Pecah PH ke Bersama — majoriti kekal lawan MN */
  const BERSAMA_ANTI_MN = 0.85;
  /** Penalti undi PN bila Bersatu tiada dalam roster (#4 vs #7) */
  const PN_SANS_PENALTY = 2;
  const PN_SANS_BERSATU_SEAT_PENALTY = 7;

  const PN_ROSTER = ["PAS", "Pejuang", "Wawasan", "Gerakan", "PRIM"];
  const PN_ROSTER_PLUS = [...PN_ROSTER, "Bersatu"];
  const PN_LABEL = "PN (PAS+Pejuang+Wawasan+Gerakan · tanpa Bersatu)";
  const PN_PLUS_LABEL = "PN (PAS+Pejuang+Wawasan+Gerakan + Bersatu + …)";

  const BLOCS = [
    { id: "pas_solo", num: 1, label: "PAS Solo", color: "#22c55e", source: "model" },
    { id: "umno_solo", num: 2, label: "UMNO Solo", color: "#ef4444", source: "model" },
    { id: "mn", num: 3, label: "MN", color: "#a855f7", source: "spr", default: true },
    {
      id: "pn", num: 4, label: PN_LABEL, color: "#10b981", source: "spr",
      note: "Team PN 2026: PAS · Pejuang · Wawasan · Gerakan · PRIM — bukan Bersatu",
      roster: PN_ROSTER,
    },
    { id: "ph", num: 5, label: "PH", color: "#3b82f6", source: "spr" },
    {
      id: "bersama", num: 6, label: "Bersama", color: "#f59e0b",
      source: "impact", slider: "bersamaPct",
      note: "Pecah undi PH — bukan kerusi Bersama menang",
    },
    {
      id: "pn_plus", num: 7, label: PN_PLUS_LABEL, color: "#059669", source: "spr",
      note: "Team PN penuh + Bersatu — bloc undi SPR PN 2023 (jentera Bersatu N20/N34)",
      roster: PN_ROSTER_PLUS,
    },
  ];

  const DEFAULT_SLIDERS = { bersamaPct: 3 };

  let factionBrief = null;

  function applyFactionBrief(brief) {
    if (!brief?.bloc_labels) return;
    factionBrief = brief;
    BLOCS.forEach((b) => {
      if (brief.bloc_labels[b.id]) b.label = brief.bloc_labels[b.id];
    });
    if (brief.slider_hints?.bersamaPct?.default != null) {
      DEFAULT_SLIDERS.bersamaPct = brief.slider_hints.bersamaPct.default;
    }
  }

  async function loadFactionBrief(url) {
    try {
      const res = await fetch(url || "data/n9_bloc_faction_brief.json");
      if (res.ok) applyFactionBrief(await res.json());
    } catch (_) {}
    return factionBrief;
  }

  function bersatuHeld2023(seat) {
    const p = String(seat?.party2023 || seat?.party || "").toUpperCase();
    return p === "BERSATU";
  }

  function computeVotes(seat, sliders) {
    const sl = { ...DEFAULT_SLIDERS, ...sliders };
    const bv = seat?.spr2023?.blocVotes || { PH: 0, PN: 0, BN: 0, Bebas: 0 };
    const ph0 = bv.PH || 0;
    const pn0 = bv.PN || 0;
    const bn0 = bv.BN || 0;

    const bersama = Math.round(ph0 * sl.bersamaPct / 100);
    const phNet = ph0 - bersama;

    const sansPct = bersatuHeld2023(seat) ? PN_SANS_BERSATU_SEAT_PENALTY : PN_SANS_PENALTY;
    const pnPlus = pn0;
    const pnNet = Math.round(pn0 * (1 - sansPct / 100));
    const pasSolo = pn0;
    const umnoSolo = bn0;
    const mn = pnPlus + bn0;

    return {
      pasSolo,
      umnoSolo,
      mn,
      pn: pnNet,
      pn_plus: pnPlus,
      ph: phNet,
      bersama,
      raw: { ph0, pn0, bn0 },
    };
  }

  function modelExpected(seats, key) {
    const alt = key === "umno_solo" ? "bnSoloWinProb" : null;
    let sum = 0;
    (seats || []).forEach((s) => {
      const k = key === "pas_solo" ? "pasSoloWinProb" : key === "umno_solo" ? "umnoSoloWinProb" : key === "mn" ? "pasMnWinProb" : "phWinProb";
      sum += (s[k] ?? (alt ? s[alt] : 0) ?? 0) / 100;
    });
    return Math.round(sum * 10) / 10;
  }

  function sprSeatWin(blocId, v) {
    switch (blocId) {
      case "mn":
        return v.mn > v.ph;
      case "pn":
        return v.pn > v.ph;
      case "pn_plus":
        return v.pn_plus > v.ph;
      case "ph":
        return v.ph > v.mn;
      default:
        return false;
    }
  }

  function bersamaFlipCount(seats, sliders) {
    let flips = 0;
    (seats || []).filter((s) => s.spr2023).forEach((s) => {
      const base = computeVotes(s, { ...DEFAULT_SLIDERS, ...sliders, bersamaPct: 0 });
      const adj = computeVotes(s, sliders);
      if (base.ph > base.mn && adj.mn > adj.ph) flips += 1;
    });
    return flips;
  }

  function aggregate(seats, blocId, sliders) {
    const rows = (seats || []).filter((s) => s.spr2023);
    const sl = { ...DEFAULT_SLIDERS, ...sliders };

    if (blocId === "pas_solo" || blocId === "umno_solo") {
      const exp = modelExpected(seats, blocId);
      const probKey = blocId === "pas_solo" ? "pasSoloWinProb" : "umnoSoloWinProb";
      const codes = [];
      rows.forEach((s) => {
        const p = s[probKey] ?? s.bnSoloWinProb ?? 0;
        if (p >= 50) codes.push(normalizeCode(s.id));
      });
      return {
        blocId,
        seatsWon: Math.round(exp),
        seatsWonClear: codes.length,
        expectedSeats: exp,
        total: rows.length,
        majority: exp >= MAJORITY_N9,
        votePct: exp / TOTAL_DUN * 100,
        winCodes: codes,
        source: "model",
        metricLabel: "Σ model",
      };
    }

    if (blocId === "bersama") {
      const flips = bersamaFlipCount(seats, sl);
      const phSeats = aggregateSpr(seats, "ph", sl).seatsWon;
      return {
        blocId,
        seatsWon: phSeats,
        flipToMn: flips,
        total: rows.length,
        majority: false,
        votePct: sl.bersamaPct,
        winCodes: [],
        source: "impact",
        metricLabel: `pecah ${sl.bersamaPct}% PH · +${flips} flip MN`,
      };
    }

    return aggregateSpr(seats, blocId, sl);
  }

  function aggregateSpr(seats, blocId, sliders) {
    const rows = (seats || []).filter((s) => s.spr2023);
    let wins = 0;
    let voteShare = 0;
    let totalValid = 0;
    const codes = [];
    rows.forEach((s) => {
      const v = computeVotes(s, sliders);
      const valid = v.raw.ph0 + v.raw.pn0 + v.raw.bn0;
      totalValid += valid;
      const key = blocId === "pas_solo" ? "pasSolo" : blocId === "umno_solo" ? "umnoSolo" : blocId;
      if (v[key] != null) voteShare += v[key];
      if (sprSeatWin(blocId, v)) {
        wins += 1;
        codes.push(normalizeCode(s.id));
      }
    });
    return {
      blocId,
      seatsWon: wins,
      total: rows.length,
      majority: wins >= MAJORITY_N9,
      votePct: totalValid ? Math.round((voteShare / totalValid) * 1000) / 10 : 0,
      winCodes: codes,
      source: "spr",
      metricLabel: blocId === "pn" ? "SPR − penalti Bersatu" : "SPR+slider",
    };
  }

  function winsSeat(blocId, votes) {
    if (blocId === "pas_solo") {
      return votes.pasSolo > votes.ph && votes.pasSolo > votes.umnoSolo;
    }
    if (blocId === "umno_solo") {
      return votes.umnoSolo > votes.ph && votes.umnoSolo > votes.pasSolo;
    }
    return sprSeatWin(blocId, votes);
  }

  function seatMargin(blocId, votes) {
    switch (blocId) {
      case "mn": return votes.mn - votes.ph;
      case "pn": return votes.pn - votes.ph;
      case "pn_plus": return votes.pn_plus - votes.ph;
      case "ph": return votes.ph - votes.mn;
      case "pas_solo": return votes.pasSolo - Math.max(votes.ph, votes.umnoSolo);
      case "umno_solo": return votes.umnoSolo - Math.max(votes.ph, votes.pasSolo);
      default: return 0;
    }
  }

  function normalizeCode(id) {
    if (!id) return "";
    const m = String(id).match(/N0*(\d+)/i);
    return m ? `N${parseInt(m[1], 10)}` : String(id).toUpperCase();
  }

  function allBlocTotals(seats, sliders) {
    return BLOCS.reduce((acc, b) => {
      acc[b.id] = aggregate(seats, b.id, sliders);
      return acc;
    }, {});
  }

  function formatAggVal(agg) {
    if (agg.flipToMn != null) return `${agg.seatsWon}/${TOTAL_DUN} · +${agg.flipToMn} flip`;
    if (agg.expectedSeats != null) return `${agg.seatsWon}/${TOTAL_DUN} (Σ${agg.expectedSeats})`;
    return `${agg.seatsWon}/${TOTAL_DUN}`;
  }

  function activeBlocInsight(seats, blocId, sliders) {
    const agg = aggregate(seats, blocId, sliders);
    const sl = { ...DEFAULT_SLIDERS, ...sliders };
    const bloc = BLOCS.find((b) => b.id === blocId) || BLOCS[2];
    const brief = factionBrief;
    let lines = [];

    if (blocId === "pas_solo") {
      lines.push(
        `<strong>#1 PAS Solo:</strong> Σ model <strong>${agg.expectedSeats}/${TOTAL_DUN}</strong> kerusi dijangka` +
        ` (${agg.seatsWonClear ?? "—"} kerusi ≥50% prob).`
      );
    } else if (blocId === "umno_solo") {
      lines.push(
        `<strong>#2 UMNO Solo:</strong> Σ model <strong>${agg.expectedSeats}/${TOTAL_DUN}</strong>` +
        ` (${agg.seatsWonClear ?? "—"} kerusi ≥50%).`
      );
    } else if (blocId === "mn") {
      lines.push(
        `Muafakat PN+BN vs PH (SPR 2023). Menang <strong>${agg.seatsWon}/${TOTAL_DUN}</strong>` +
        `${agg.majority ? " · <span style='color:#22c55e'>majoriti ≥19</span>" : ""}.`
      );
    } else if (blocId === "pn") {
      lines.push(
        `<strong>#4 PN</strong> (Team PN · <em>tanpa Bersatu</em>) vs PH: ` +
        `<strong>${agg.seatsWon}/${TOTAL_DUN}</strong> kerusi SPR (−${PN_SANS_PENALTY}%/` +
        `${PN_SANS_BERSATU_SEAT_PENALTY}% penalti jentera Bersatu).`
      );
      lines.push(`<br>Komponen: ${PN_ROSTER.join(" · ")}`);
    } else if (blocId === "pn_plus") {
      lines.push(
        `<strong>#7 PN+</strong> (Team PN · <em>dengan Bersatu</em>) vs PH: ` +
        `<strong>${agg.seatsWon}/${TOTAL_DUN}</strong> kerusi — bloc SPR PN 2023 penuh.`
      );
      lines.push(`<br>Komponen: ${PN_ROSTER_PLUS.join(" · ")}`);
    } else if (blocId === "ph") {
      lines.push(`<strong>#5 PH</strong> vs MN: <strong>${agg.seatsWon}/${TOTAL_DUN}</strong> kerusi.`);
    } else if (blocId === "bersama") {
      lines.push(
        `<strong>#6 Bersama:</strong> pecah <strong>${sl.bersamaPct}%</strong> undi PH →` +
        ` <strong>+${agg.flipToMn ?? 0} kerusi</strong> flip ke MN jika pecahan real.`
      );
    }

    if (blocId === "pn" && brief?.team_pn_bullet?.length) {
      lines.push(`<br>Roster #4: ${brief.team_pn_bullet.join(" · ")}`);
    }
    if (blocId === "pn_plus" && brief?.team_pn_plus_bullet?.length) {
      lines.push(`<br>Roster #7: ${brief.team_pn_plus_bullet.join(" · ")}`);
    }

    return { agg, lines: lines.join(" "), bloc };
  }

  function getFactionBrief() {
    return factionBrief;
  }

  function majorityProb(expected, majority = MAJORITY_N9, scale = 3) {
    const x = (expected ?? 0) - majority;
    const pct = 100 / (1 + Math.exp(-x / scale));
    return Math.round(Math.max(2, Math.min(97, pct)));
  }

  function hungMajorityProb(scenarios, majority = MAJORITY_N9) {
    const main = (scenarios || []).filter((s) => s.expectedSeats != null && !/risiko/i.test(s.name || ""));
    if (!main.length) return 25;
    const sorted = [...main].sort((a, b) => (b.expectedSeats || 0) - (a.expectedSeats || 0));
    const maxExp = sorted[0].expectedSeats || 0;
    const topMp = sorted[0].majorityPct || 0;
    let hung;
    if (maxExp < majority - 2) hung = 25 + (majority - maxExp) * 5;
    else if (topMp < 55) hung = Math.max(10, 35 - Math.max(0, topMp - 40));
    else hung = Math.max(10, 20 - (maxExp - majority) * 6);
    return Math.round(Math.max(10, Math.min(42, hung)));
  }

  function applyDemographicNudges(rows, nudges) {
    if (!nudges || !rows?.length) return rows;
    return rows.map((r) => {
      const key = r.blocId;
      const d = key ? nudges[key] : null;
      if (d == null || d === 0) return r;
      const mp = Math.round(Math.max(2, Math.min(97, (r.majorityPct ?? r.pct ?? 0) + d)));
      return { ...r, majorityPct: mp, pct: mp, demoNudged: true };
    });
  }

  /** Command Center — 7 bloc + risiko hung */
  function coalitionScenarios(seats, sliders, demoNudges) {
    const sl = { ...DEFAULT_SLIDERS, ...sliders };
    const all = allBlocTotals(seats, sl);
    const rows = [];

    BLOCS.forEach((b) => {
      const agg = all[b.id];
      if (!agg) return;
      let expectedSeats = agg.expectedSeats != null ? agg.expectedSeats : agg.seatsWon;
      let seatLabel = null;
      let majorityPct;

      if (b.id === "bersama") {
        seatLabel = `+${agg.flipToMn ?? 0} flip MN`;
        expectedSeats = agg.flipToMn ?? 0;
        majorityPct = Math.min(12, (agg.flipToMn ?? 0) * 2);
      } else if (b.id === "pn") {
        const plus = all.pn_plus;
        const voteGap = plus ? Math.max(0, (plus.votePct || 0) - (agg.votePct || 0)) : 0;
        expectedSeats = Math.round((agg.seatsWon - 0.4 - voteGap / 2) * 10) / 10;
        majorityPct = majorityProb(expectedSeats);
      } else {
        majorityPct = majorityProb(expectedSeats);
      }

      rows.push({
        name: `#${b.num} ${b.label}${b.default ? " ★" : ""}`,
        expectedSeats,
        seatLabel,
        majorityPct,
        pct: majorityPct,
        color: b.color,
        assumption: b.note || `${b.source} · ${agg.metricLabel || ""}`,
        blocId: b.id,
      });
    });

    const hungMp = hungMajorityProb(rows);
    rows.push({
      name: "Risiko tiada majoriti",
      expectedSeats: null,
      seatLabel: `tiada bloc ≥${MAJORITY_N9}`,
      majorityPct: hungMp,
      pct: hungMp,
      color: "#f59e0b",
      assumption: "Tiada bloc capai 19 kerusi dengan selesa · perlu rundingan selepas undi",
      blocId: "hung",
    });

    rows.sort((a, b) => (b.majorityPct ?? 0) - (a.majorityPct ?? 0));
    return applyDemographicNudges(rows, demoNudges);
  }

  global.N9Bloc7 = {
    MAJORITY_N9,
    TOTAL_DUN,
    PN_ROSTER,
    PN_ROSTER_PLUS,
    PN_LABEL,
    PN_PLUS_LABEL,
    BLOCS,
    DEFAULT_SLIDERS,
    computeVotes,
    winsSeat,
    seatMargin,
    aggregate,
    allBlocTotals,
    activeBlocInsight,
    formatAggVal,
    modelExpected,
    normalizeCode,
    loadFactionBrief,
    applyFactionBrief,
    getFactionBrief,
    majorityProb,
    hungMajorityProb,
    coalitionScenarios,
    applyDemographicNudges,
  };
})(typeof window !== "undefined" ? window : globalThis);
