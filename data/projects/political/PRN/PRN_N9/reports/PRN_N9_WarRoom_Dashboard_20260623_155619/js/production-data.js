/**
 * Production data layer — N9 live + Johor/Melaka state-aware panels
 */
(function () {
  let bundle = null;
  let social = null;
  let socialJohor = null;
  let pasTarget = null;
  let socmedJohor = null;
  let socmedMelaka = null;

  const STATE_CFG = {
    N9: {
      label: "Negeri Sembilan",
      dun: 36,
      majority: 19,
      coalitionTitle: "Peluang Majoriti Kerajaan N9",
      coalitionDesc: "P(capai ≥19/36 kerusi) · bukan % undi · hybrid crawl + pasWinProb · SPR",
      issueTitle: "Isu Panas (Semua Platform)",
    },
    Johor: {
      label: "Johor",
      dun: 56,
      majority: 29,
      coalitionTitle: "Peluang Majoriti Kerajaan Johor",
      coalitionDesc: "P(capai ≥29/56 kerusi) · bukan % undi · hybrid crawl + pasWinProb · SPR",
      issueTitle: "Isu Panas (Semua Platform)",
    },
    Melaka: {
      label: "Melaka",
      dun: 28,
      majority: 15,
      coalitionTitle: "Aktiviti Socmed PRN Melaka",
      coalitionDesc: "Kerusi paling aktif · 28 DUN · data socmed + naratif",
      issueTitle: "Isu Panas — Naratif Cina & India",
    },
  };

  const MOCK_COALITION = [
    { name: "MN (PAS+BN)", expectedSeats: 20, majorityPct: 68, pct: 68, color: "var(--purple)", assumption: "PAS & BN berunding selepas undi" },
    { name: "PH (Madani)", expectedSeats: 17, majorityPct: 32, pct: 32, color: "var(--red)" },
    { name: "BN Solo (UMNO-led)", expectedSeats: 11, majorityPct: 8, pct: 8, color: "var(--primary)" },
    { name: "PAS Solo", expectedSeats: 10, majorityPct: 6, pct: 6, color: "var(--green)" },
    { name: "Risiko tiada majoriti", seatLabel: "tiada bloc ≥19", expectedSeats: null, majorityPct: 15, pct: 15, color: "var(--amber)" },
  ];

  const MOCK_ISSUES = [
    { label: "Kos Sara Hidup", pct: 34, color: "var(--amber)" },
    { label: "Pendidikan / SJKT-SJKC", pct: 22, color: "var(--purple)" },
    { label: "Perkhidmatan Kerajaan Tempatan", pct: 18, color: "var(--cyan)" },
    { label: "Ekonomi & Pekerjaan", pct: 16, color: "var(--primary)" },
  ];

  const ISSUE_COLORS = ["var(--amber)", "var(--purple)", "var(--cyan)", "var(--primary)", "var(--rose)", "var(--green)"];

  function currentState() {
    return typeof state !== "undefined" ? state : "N9";
  }

  function cfg() {
    return STATE_CFG[currentState()] || STATE_CFG.N9;
  }

  async function loadProductionMeta() {
    try {
      const [b, s, sj, pt, smj] = await Promise.all([
        fetch("data/n9_production_bundle.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/n9_social_summary.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/johor_social_summary.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/pas_target_23_N9.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/socmed_by_dun_Johor.json").then((r) => (r.ok ? r.json() : null)),
      ]);
      bundle = b;
      social = s;
      socialJohor = sj;
      pasTarget = pt;
      socmedJohor = smj;
      return bundle?.meta?.mode === "production";
    } catch {
      return false;
    }
  }

  function fmt(n) {
    if (n == null || n === "") return "—";
    return Number(n).toLocaleString("en-MY");
  }

  function updatePanelTitles() {
    const c = cfg();
    const set = (id, text) => {
      const el = document.getElementById(id);
      if (el) el.textContent = text;
    };
    set("cmdCoalitionTitle", c.coalitionTitle);
    set("cmdCoalitionDesc", c.coalitionDesc);
    set("cmdIssueTitle", c.issueTitle);
  }

  function narrativeIssueRows(st) {
    const d = typeof DATA !== "undefined" ? DATA[st] : null;
    if (!d?.issues) return null;
    const acc = {};
    for (const comm of ["chinese", "indian"]) {
      for (const [name, pct] of d.issues[comm] || []) {
        acc[name] = (acc[name] || 0) + Number(pct);
      }
    }
    const entries = Object.entries(acc).sort((a, b) => b[1] - a[1]).slice(0, 6);
    if (!entries.length) return null;
    const total = entries.reduce((s, [, p]) => s + p, 0) || 1;
    return entries.map(([label, pct], i) => ({
      label,
      pct: Math.round((pct / total) * 100),
      color: ISSUE_COLORS[i % ISSUE_COLORS.length],
    }));
  }

  function renderJohorActivityBars(socmed) {
    const el = document.getElementById("coalitionBars");
    if (!el) return;
    const byDun = socmed?.byDun || {};
    const rows = Object.entries(byDun)
      .map(([code, d]) => ({ code, ...d }))
      .sort(
        (a, b) =>
          (b.mentions_24h || 0) - (a.mentions_24h || 0) ||
          (b.mentions_total || 0) - (a.mentions_total || 0)
      )
      .slice(0, 5);
    if (!rows.length) {
      el.innerHTML = `<div class="post-card" style="color:var(--muted);font-size:13px">Tiada data socmed Johor — jalankan master crawl + build bundle.</div>`;
      return;
    }
    const maxM = Math.max(...rows.map((r) => r.mentions_total || 0), 1);
    el.innerHTML = rows
      .map((r) => {
        const m24 = r.mentions_24h || 0;
        const mt = r.mentions_total || 0;
        const barW = Math.max(8, Math.round((mt / maxM) * 100));
        const alert = r.alert_level === "critical" ? "var(--red)" : r.alert_level === "warn" ? "var(--amber)" : "var(--primary)";
        return `
      <div class="coal-row" title="24j: ${m24} mention · engagement ${fmt(r.engagement_total)}">
        <span class="name">${r.code}</span>
        <span class="seats">${mt} post</span>
        <div class="coal-bar"><div style="width:${barW}%;background:${alert}"></div></div>
        <span class="coal-pct">${m24} (24j)</span>
      </div>`;
      })
      .join("");
  }

  function renderCommandKpisN9() {
    if (!social) return;
    const m = social.meta || {};
    const a = social.analytics || {};
    const st = social.seats || {};

    const set = (id, html) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = html;
    };

    const posPct = m.posPct ?? "—";
    const negPct = m.negPct ?? "—";
    set("kpiSentimentValue", `<span class="${Number(posPct) >= 50 ? "green" : "amber"}">${posPct}%</span>`);
    set("kpiSentimentSub", `positif · neg ${negPct}% · master crawl NS`);

    const ptMeta = pasTarget?.meta || {};
    const pasContest = ptMeta.count ?? st.pasTarget ?? 23;
    const pasWajib = ptMeta.wajibCount ?? st.pasWajib ?? 16;
    const pasImbang = ptMeta.imbangCount ?? st.pasImbang ?? 7;
    const pasProjected = (pasTarget?.seats || []).filter((s) => (s.pasWinProb || 0) >= 50).length;

    set("kpiSeatsValue", `<span class="green">${pasContest} / ${st.total ?? 36}</span>`);
    set("kpiSeatsSub", `${pasWajib} keutamaan · ${pasImbang} peluang tambahan · ${pasProjected || st.pnProjected || "—"} dijangka menang`);
    set("kpiSeatsHint", "Keutamaan = sasaran teras PAS · Peluang tambahan = kerusi stretch · Dijangka menang = pasWinProb ≥50%");
    updateSeatsProgress({ ...st, pasTarget: pasContest });

    set("kpiMentionValue", fmt(m.totalDataPoints ?? m.totalPosts));
    set("kpiMentionSub", `${fmt(m.totalEngagement ?? m.nsEngagement)} engagement · arkib + PRN hybrid`);

    const syncA = document.getElementById("syncAnalytics");
    if (syncA && a.totalPosts) {
      syncA.textContent = `${fmt(a.totalDataPoints || a.totalPosts)} data points (hybrid)`;
    }
  }

  function renderCommandKpisJohor() {
    const sm = socmedJohor;
    const js = socialJohor;
    const meta = js?.meta || sm?.meta || {};
    const analytics = js?.analytics || {};
    const st = js?.seats || {};

    const set = (id, html) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = html;
    };

    const posPct = js?.meta?.posPct ?? "—";
    const negPct = js?.meta?.negPct ?? "—";
    set(
      "kpiSentimentValue",
      js ? `<span class="${Number(posPct) >= 50 ? "green" : "amber"}">${posPct}%</span>` : `<span class="green">LIVE</span>`
    );
    set(
      "kpiSentimentSub",
      js ? `positif · neg ${negPct}% · master crawl Johor` : `Johor · ${fmt(meta.state_rows_scanned)} baris master crawl`
    );

    const pnProj = st.pnProjected ?? "—";
    const pasFlip = st.pasFlip50 ?? "—";
    set("kpiSeatsValue", `<span class="green">${st.total ?? 56} DUN</span>`);
    set(
      "kpiSeatsSub",
      js
        ? `${pnProj} dijangka PN/PAS≥50% · ${pasFlip} kerusi PAS solo≥50%`
        : `56 DUN · majoriti 29 kerusi`
    );
    set("kpiSeatsHint", "Majoriti Johor = 29/56 · model hybrid PRN2022 + socmed · SPR");

    const bar = document.querySelector("#cmdKpiGrid .kpi:nth-child(2) .progress div");
    if (bar) {
      const pct = st.total ? Math.round(((pnProj || 0) / st.total) * 100) : 56;
      bar.style.width = Math.min(100, pct) + "%";
      bar.style.background = (pnProj || 0) >= (st.majority || 29) ? "var(--green)" : "var(--amber)";
    }

    set("kpiMentionValue", fmt(analytics.totalDataPoints ?? js?.meta?.totalDataPoints ?? js?.meta?.johorPosts ?? meta.state_rows_scanned));
    set(
      "kpiMentionSub",
      js
        ? `${fmt(js?.meta?.johorEngagement ?? analytics.johorEngagement)} engagement Johor · master hybrid`
        : `post Johor · kemas ${(meta.generated || "").slice(0, 16)}`
    );

    const syncA = document.getElementById("syncAnalytics");
    if (syncA) {
      const pts = analytics.totalDataPoints ?? js?.meta?.totalDataPoints ?? analytics.totalPosts;
      syncA.textContent = pts ? `${fmt(pts)} data points (hybrid)` : `Johor · ${fmt(meta.state_rows_scanned)} rows`;
    }
  }

  function renderCoalitionBars(items, isProd, socialSummary) {
    const el = document.getElementById("coalitionBars");
    if (!el) return;
    const src = socialSummary || social;
    const formation = src?.coalitionFormation;
    const raw = formation?.scenarios || items || MOCK_COALITION;
    const sorted = [...raw].sort(
      (x, y) => (y.majorityPct ?? y.pct ?? 0) - (x.majorityPct ?? x.pct ?? 0)
    );
    const rows = sorted.slice(0, 4);
    const bnSolo = sorted.find((c) => /bn solo|umno-led/i.test(c.name || ""));
    if (bnSolo && !rows.some((c) => c.name === bnSolo.name)) rows.push(bnSolo);
    const total = formation?.totalSeats || cfg().dun || 36;
    el.innerHTML = rows
      .map((c) => {
        const isHungRisk = /risiko tiada majoriti/i.test(c.name || "");
        const seats = c.seatLabel || (c.expectedSeats != null ? c.expectedSeats : "—");
        const seatText = isHungRisk ? seats : `~${seats}/${total}`;
        const mp = c.majorityPct != null ? c.majorityPct : c.pct;
        const barW = Math.max(4, Math.min(100, mp));
        return `
      <div class="coal-row" title="${c.assumption || ""}">
        <span class="name">${c.name}</span>
        <span class="seats">${seatText}</span>
        <div class="coal-bar"><div style="width:${barW}%;background:${c.color}"></div></div>
        <span class="coal-pct">${mp}%</span>
      </div>`;
      })
      .join("");
  }

  function renderIssueHeatmap(items, note) {
    const el = document.getElementById("cmdIssueHeatmap");
    const desc = document.getElementById("issueHeatmapDesc");
    if (!el) return;
    const rows = (items || MOCK_ISSUES).slice(0, 6);
    el.innerHTML = rows
      .map(
        (i) => `
      <li>
        <span>${i.label}</span>
        <div class="issue-right">
          <strong>${i.pct}%</strong>
          <div class="issue-bar"><div style="width:${i.pct}%;background:${i.color || "var(--amber)"}"></div></div>
        </div>
      </li>`
      )
      .join("");
    if (desc) desc.textContent = note || "Issue heatmap";
  }

  function updateSeatsProgress(st) {
    const bar = document.querySelector("#cmdKpiGrid .kpi:nth-child(2) .progress div");
    if (!bar || !st) return;
    const total = st.total || 36;
    const seats = st.pasTarget ?? st.pnProjected ?? 0;
    const pct = total ? Math.round((seats / total) * 100) : 0;
    bar.style.width = pct + "%";
    bar.style.background = seats >= (st.majority || 19) ? "var(--green)" : "var(--amber)";
  }

  function updateProductionLinks(isProd) {
    const showN9 = isProd && currentState() === "N9";
    const fullLink = document.getElementById("fullDashboardLink");
    if (fullLink) fullLink.style.display = showN9 ? "" : "none";
    const sideFull = document.querySelector('a[href="/dashboard/n9-full"]');
    if (sideFull) sideFull.style.display = showN9 ? "" : "none";
  }

  function renderAllCommandPanels(isProd) {
    const st = currentState();
    updatePanelTitles();

    if (st === "N9" && isProd && social) {
      renderCommandKpisN9();
      renderCoalitionBars(social.coalition || MOCK_COALITION, true, social);
      const note = social?.issues?.windowNote || "24 jam sebelum tarikh crawl terakhir";
      renderIssueHeatmap(social.issues?.top || MOCK_ISSUES, `Issue heatmap — ${note} · master crawl N9`);
    } else if (st === "Johor" && socialJohor) {
      renderCommandKpisJohor();
      renderCoalitionBars(socialJohor.coalition || MOCK_COALITION, true, socialJohor);
      const note = socialJohor?.issues?.windowNote || "24 jam sebelum tarikh crawl terakhir";
      renderIssueHeatmap(
        socialJohor.issues?.top || MOCK_ISSUES,
        `Issue heatmap — ${note} · master crawl Johor`
      );
    } else if (st === "Johor") {
      renderCommandKpisJohor();
      renderJohorActivityBars(socmedJohor);
      const narrIssues = narrativeIssueRows("Johor");
      renderIssueHeatmap(
        narrIssues || MOCK_ISSUES,
        narrIssues
          ? `Naratif live · Cina+India · dikemas ${typeof narrativeMeta !== "undefined" && narrativeMeta?.generated_at ? narrativeMeta.generated_at : "—"}`
          : "Naratif Johor — jalankan ./scripts/update_narrative.sh johor"
      );
    } else if (st === "Melaka") {
      const nd = typeof DATA !== "undefined" ? DATA.Melaka : null;
      const set = (id, html) => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
      };
      set("kpiSentimentValue", `<span class="green">LIVE</span>`);
      set("kpiSentimentSub", `Melaka · naratif Cina & India`);
      set("kpiSeatsValue", `<span class="green">28 DUN</span>`);
      set("kpiSeatsSub", `Naratif Cina ${nd?.chinese?.posts ?? "—"} · India ${nd?.indian?.posts ?? "—"} post`);
      set("kpiMentionValue", fmt((nd?.chinese?.posts || 0) + (nd?.indian?.posts || 0)));
      set("kpiMentionSub", `jumlah post naratif Melaka`);
      document.getElementById("coalitionBars").innerHTML =
        `<div class="post-card" style="color:var(--muted);font-size:13px">Melaka — model coalisi N9 tidak dipapar. Guna Modul #6 naratif + Modul DUN.</div>`;
      const narrIssues = narrativeIssueRows("Melaka");
      renderIssueHeatmap(narrIssues || MOCK_ISSUES, narrIssues ? "Naratif live · Melaka" : "Naratif Melaka — jalankan update_narrative.sh");
    } else {
      renderCoalitionBars(MOCK_COALITION, false);
      renderIssueHeatmap(MOCK_ISSUES, `Mock data — pilih N9 (production) atau Johor (naratif live)`);
    }
  }

  window.initProductionData = async function initProductionData() {
    const ok = await loadProductionMeta();
    const st = currentState();
    window.PRN_PRODUCTION_MODE =
      (ok && st === "N9") || (st === "Johor" && !!socialJohor?.coalition?.length);
    renderAllCommandPanels(window.PRN_PRODUCTION_MODE);
    updateProductionLinks(ok && st === "N9");
    return window.PRN_PRODUCTION_MODE;
  };

  window.refreshProductionData = async function refreshProductionData() {
    await loadProductionMeta();
    const st = currentState();
    window.PRN_PRODUCTION_MODE =
      (bundle?.meta?.mode === "production" && st === "N9") ||
      (st === "Johor" && !!socialJohor?.coalition?.length);
    renderAllCommandPanels(window.PRN_PRODUCTION_MODE);
    updateProductionLinks(bundle?.meta?.mode === "production" && st === "N9");
  };
})();
