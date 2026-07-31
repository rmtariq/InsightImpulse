/**
 * Production data layer — N9 live + Johor/Melaka state-aware panels
 */
(function () {
  let bundle = null;
  let social = null;
  let socialJohor = null;
  let pasTarget = null;
  let culaPollSummary = null;
  let culaPollFull = null;
  let dailyOps = null;
  let socmedJohor = null;
  let socmedMelaka = null;

  const STATE_CFG = {
    N9: {
      label: "Negeri Sembilan",
      dun: 36,
      majority: 19,
      coalitionTitle: "Peluang Majoriti Kerajaan N9",
      coalitionDesc: "P(capai ≥19/36 kerusi) · 7-bloc · #4 tanpa Bersatu · #7 + Bersatu",
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
    { name: "#3 MN ★", expectedSeats: 22, majorityPct: 72, pct: 72, color: "#a855f7", assumption: "Muafakat PN+BN vs PH (SPR 2023)" },
    { name: "Risiko tiada majoriti", seatLabel: "tiada bloc ≥19", expectedSeats: null, majorityPct: 28, pct: 28, color: "#f59e0b" },
    { name: "#5 PH", expectedSeats: 14, majorityPct: 18, pct: 18, color: "#3b82f6" },
    { name: "#1 PAS Solo", expectedSeats: 12, majorityPct: 24, pct: 24, color: "#22c55e" },
    { name: "#4 PN", expectedSeats: 13, majorityPct: 12, pct: 12, color: "#10b981" },
    { name: "#2 UMNO Solo", expectedSeats: 8, majorityPct: 4, pct: 4, color: "#ef4444" },
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
      const [b, s, sj, pt, smj, cula, culaFull, ops] = await Promise.all([
        fetch("data/n9_production_bundle.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/n9_social_summary.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/johor_social_summary.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/pas_target_23_N9.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/socmed_by_dun_Johor.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/cula_poll_summary_N9.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/cula_poll_by_dun_N9.json").then((r) => (r.ok ? r.json() : null)),
        fetch("data/n9_daily_ops.json").then((r) => (r.ok ? r.json() : null)),
      ]);
      bundle = b;
      social = s;
      socialJohor = sj;
      pasTarget = pt;
      socmedJohor = smj;
      culaPollSummary = cula;
      culaPollFull = culaFull;
      dailyOps = ops;
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

    // Agihan rasmi MN (arahan HQ Kamarol): PAS/PN 13 · UMNO/BN 23
    const MN_PAS = 13;
    const MN_UMNO = 23;
    set("kpiSeatsValue", `<span class="green">${MN_PAS} / ${st.total ?? 36}</span>`);
    set("kpiSeatsSub", `9 wajib + 4 berhasrat · UMNO/BN ${MN_UMNO} kerusi`);
    set("kpiSeatsHint", "Agihan MN HQ · realistik cerah ~3 drpd 4 berhasrat (Chennah terbaik · Nilai stretch)");
    updateSeatsProgress({ ...st, pasTarget: MN_PAS });

    const basePts = m.totalDataPoints ?? m.totalPosts ?? 0;
    const baseEng = m.totalEngagement ?? m.nsEngagement ?? 0;
    const cp = culaPollSummary || social.culaPoll;
    const culaPosts = cp?.meta?.totalPosts || 0;
    const culaComments = cp?.meta?.totalComments || 0;
    const culaEng =
      cp?.meta?.totalEngagement ||
      (cp?.mnVsSolo?.engagement || 0) + (cp?.pasLabu?.engagement || 0) ||
      0;

    const job3 =
      social.signals?.shawnLohChinaPress ||
      social.jobCrawlMetrics?.job3 ||
      social.coalitionFormation?.crawlSignals?.shawnLohChinaPress ||
      null;
    const job3Records = Number(job3?.records || social.dataQuality?.job3ShawnLohRecords || 0);
    const job3Eng = Number(job3?.engagement || social.dataQuality?.job3ShawnLohEngagement || 0);
    const job3ChineseRows = Number(job3?.chinese_rows || social.dataQuality?.job3ShawnLohChineseRows || 0);

    const pengundi = social.pengundiMacPosts || bundle?.pengundiMacPosts || null;
    const pengPosts = pengundi?.summary?.total_posts || 0;
    const pengComments = pengundi?.summary?.total_comments_crawled || 0;
    const pengEng = pengundi?.summary?.total_engagement || 0;

    set("kpiMentionValue", fmt(basePts + culaComments + job3Records + pengComments));
    const demoMix = social.demographics?.stateDemoMix || {};
    const demoNote = demoMix.malay != null
      ? ` · naratif ${demoMix.malay}% Melayu / ${demoMix.urban || 0}% bandar`
      : "";
    const culaNote =
      culaPosts || culaEng
        ? ` · +${culaPosts} post Cula · +${fmt(culaEng)} eng poll · ${culaComments} komen`
        : "";
    const adat = social.signals?.n9IstanaAdat || social.jobCrawlMetrics?.job2;
    const adatEngK5 =
      adat?.engagement ||
      social.jobCrawlMetrics?.totals?.engagement_job2_k5 ||
      social.dataQuality?.istanaAdatEngagementK5 ||
      0;
    const adatEngOverlap = social.jobCrawlMetrics?.totals?.engagement_job2_overlap || 0;
    const adatNote = adatEngK5
      ? ` · Isu adat K5: ${fmt(adatEngK5)} eng${adatEngOverlap ? ` (K1–K5 overlap ${fmt(adatEngOverlap)})` : ""}`
      : "";

    const job3Note = job3Records
      ? ` · +${fmt(job3Records)} Shawn/ChinaPress · +${fmt(job3Eng)} eng${job3ChineseRows ? ` · Chinese rows ${job3ChineseRows}` : ""}`
      : "";
    const pengNote =
      pengPosts
        ? ` · +${pengPosts} post Pengundi MY · +${fmt(pengComments)} komen · +${fmt(pengEng)} eng`
        : "";
    set("kpiMentionSub", `${fmt(baseEng + culaEng + job3Eng + pengEng)} engagement (master + Cula + Job3 + Pengundi 4-post)${culaNote}${pengNote}${job3Note}${adatNote}${demoNote}`);

    const syncA = document.getElementById("syncAnalytics");
    if (syncA && (social.analytics?.totalPosts || basePts)) {
      syncA.textContent = `${fmt(basePts + culaComments + job3Records + pengComments)} data points (hybrid + Cula + Job3 + Pengundi 4-post)`;
    }
  }

  function renderPengundiMacPostsPanel(block) {
    const panel = document.getElementById("cmdPengundiPostsPanel");
    if (!panel) return;
    const data = block || social?.pengundiMacPosts || bundle?.pengundiMacPosts;
    if (!data?.posts?.length) {
      panel.classList.add("hidden");
      return;
    }
    panel.classList.remove("hidden");
    const s = data.summary || {};
    const esc = (v) =>
      String(v ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    const rows = data.posts
      .map(
        (p, i) => `<tr>
          <td><strong>${esc(p.id || `P${i + 1}`)}</strong></td>
          <td>${esc((p.title || "").slice(0, 56))}…</td>
          <td>${fmt(p.crawled_comments)}</td>
          <td>${fmt(p.likes)}</td>
          <td>${p.negative_pct != null ? p.negative_pct + "%" : "—"}</td>
          <td style="max-width:280px;font-size:11px">${esc((p.insight || "").slice(0, 120))}…</td>
        </tr>
        <tr class="pengundi-detail-row"><td colspan="6" style="font-size:11px;line-height:1.45;padding:8px 12px;background:rgba(0,0,0,0.15)">
          <strong>Analitik:</strong> ${esc(p.analytics_line || "")}<br/>
          <strong>Insight:</strong> ${esc(p.insight || "")}<br/>
          ${p.insight_exco ? `<strong>EXCO:</strong> ${esc(p.insight_exco)}<br/>` : ""}
          <strong>Tema:</strong> ${esc(p.tema_komen || "")} · <strong>Bloc:</strong> ${esc(p.impak_bloc || "")}
        </td></tr>`
      )
      .join("");
    panel.innerHTML = `
      <h4>Pengundi Malaysia · 4 Post URL Batch (Mac1 + Mac2 · Jul 2026)</h4>
      <p class="desc" style="margin:-2px 0 8px">${esc(data.strategic_headline || data.label || "")} · Sync ${esc(data.updated || "")}</p>
      <div class="cula-kpi-row" style="margin-bottom:12px">
        <div class="cula-kpi-mini"><div class="v">${fmt(s.total_posts)}</div><div class="l">Post</div></div>
        <div class="cula-kpi-mini"><div class="v">${fmt(s.total_comments_crawled)}</div><div class="l">Komen crawled</div></div>
        <div class="cula-kpi-mini"><div class="v">${fmt(s.total_likes)}</div><div class="l">Likes</div></div>
        <div class="cula-kpi-mini"><div class="v">${fmt(s.total_engagement)}</div><div class="l">Engagement</div></div>
      </div>
      <table class="data-table" style="width:100%;font-size:12px">
        <thead><tr><th>ID</th><th>Soalan</th><th>Komen</th><th>Likes</th><th>Neg%</th><th>Insight</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <p class="desc" style="margin-top:8px">Master CSV: <code>${esc(data.master_csv || "")}</code> · DOCX: <code>${esc(data.insight_docx_file || "reports/pengundi_4posts/Pengundi_4Posts_Insight_*.docx")}</code></p>
      ${data.kesimpulan_gabungan ? `<p class="desc"><strong>Kesimpulan:</strong> ${esc(data.kesimpulan_gabungan)}</p>` : ""}
    `;
  }

  function renderN9NarrativeCommunityPanel(nc, narrData) {
    const panel = document.getElementById("cmdNarrativeN9Panel");
    if (!panel) return;
    const block = nc || social?.narrativeCommunity || bundle?.narrativeCommunity;
    const n9 = narrData || (typeof DATA !== "undefined" ? DATA.N9 : null);
    if (!block && !n9) {
      panel.classList.add("hidden");
      return;
    }
    panel.classList.remove("hidden");
    const esc = (v) =>
      String(v ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    const ch = n9?.chinese || {};
    const ind = n9?.indian || {};
    const issues = n9?.issues || {};
    const chIssues = (issues.chinese || []).slice(0, 4);
    const indIssues = (issues.indian || []).slice(0, 4);
    const dunRows = (n9?.dunRows || [])
      .map(
        (r) =>
          `<tr><td><strong>${esc(r[0])}</strong></td><td>${esc(r[1])}</td><td>${esc(r[2])}</td><td>${esc(r[3])}</td><td>${esc(r[4])}</td></tr>`
      )
      .join("");
    const p1 = (n9?.actions || []).filter((a) => a.p === "p1").slice(0, 4);
    const actRows = p1
      .map(
        (a) =>
          `<li style="margin-bottom:6px"><strong>${esc(a.comm)}</strong> · ${esc(a.title)} <span style="color:var(--muted)">(${esc((a.meta || [])[0] || "")})</span></li>`
      )
      .join("");
    panel.innerHTML = `
      <h4>Naratif Komuniti Cina &amp; India · 36 DUN N9</h4>
      <p class="desc" style="margin:-2px 0 8px">Modul #6 · dikemas ${esc(block?.updated || (typeof narrativeMeta !== "undefined" && narrativeMeta?.generated_at) || "—")} · Pengundi sync ${esc(block?.pengundi_sync || "—")}</p>
      <div class="cula-kpi-row" style="margin-bottom:12px">
        <div class="cula-kpi-mini"><div class="v">${fmt(ch.posts || block?.chinese_posts)}</div><div class="l">Post Cina</div></div>
        <div class="cula-kpi-mini"><div class="v">${fmt(ind.posts || block?.indian_posts)}</div><div class="l">Post India</div></div>
        <div class="cula-kpi-mini"><div class="v">${block?.dun_with_narrative ?? (n9?.dunRows || []).length}</div><div class="l">DUN pantau</div></div>
        <div class="cula-kpi-mini"><div class="v">36</div><div class="l">Jumlah DUN</div></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div><strong style="color:var(--rose)">Isu Cina</strong><ul style="margin:4px 0 0;padding-left:16px;font-size:12px">${chIssues.map(([n, p]) => `<li>${esc(n)} (${p}%)</li>`).join("")}</ul></div>
        <div><strong style="color:var(--purple)">Isu India</strong><ul style="margin:4px 0 0;padding-left:16px;font-size:12px">${indIssues.map(([n, p]) => `<li>${esc(n)} (${p}%)</li>`).join("")}</ul></div>
      </div>
      ${dunRows ? `<table class="data-table" style="width:100%;font-size:11px;margin-bottom:10px"><thead><tr><th>DUN</th><th>Nama</th><th>Tier</th><th>Isu</th><th>Sentimen</th></tr></thead><tbody>${dunRows}</tbody></table>` : ""}
      ${actRows ? `<p class="desc" style="margin:0 0 4px"><strong>Tindakan P1 (naratif):</strong></p><ul style="margin:0;padding-left:16px;font-size:12px;line-height:1.5">${actRows}</ul>` : ""}
      <p class="desc" style="margin-top:8px">Kemas kini: <code>./scripts/update_narrative.sh pagi</code> · pautan penuh: <a href="?module=narrative" style="color:var(--cyan)">Modul Naratif</a></p>
    `;
  }

  function renderN9OpsBriefPanel() {
    const panel = document.getElementById("cmdOpsBriefPanel");
    if (!panel) return;
    if (!dailyOps?.keputusan && !social) return;

    const set = (id, html) => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = html;
    };

    if (dailyOps?.keputusan) {
      const k = dailyOps.keputusan;
      set("opsDecisionMain", k.headline || "MN kekal laluan utama");
      set("opsDecisionText", k.ringkasan || "");
      set(
        "opsActionList",
        (dailyOps.tindakan_72jam || [])
          .map((a) => {
            const diff = a.kesukaran === "segera" ? "hard" : a.kesukaran === "sukar" ? "hard" : a.kesukaran === "sederhana" ? "med" : "easy";
            return `<li><span class="cmd-ops-pill ${diff}">${a.label || "Tindakan"}</span><span>${a.teks || ""}</span></li>`;
          })
          .join("")
      );
      set(
        "opsFocusDuns",
        (dailyOps.fokus_kawasan || [])
          .map((f) => `<button type="button" class="cmd-ops-dun" data-ops-dun="${f.code}" title="${f.sebab || ""}">${f.code}</button>`)
          .join("")
      );
      set(
        "opsFocusText",
        "Fokus bukan semua 36 kerusi serentak. Gerak dahulu DUN yang ada isyarat CULA + ML."
      );
      set(
        "opsFocusNote",
        `KPI 72 jam: 30 balasan komen · 1 poster MN · 1 aktiviti Labu · 1 laporan ringkas ke HQ. · Sync ${dailyOps.generated_at || ""}`
      );
      return;
    }

    const cp = culaPollSummary || social.culaPoll || {};
    const mn = cp.mnVsSolo || {};
    const labu = cp.pasLabu || {};
    const topCoalition = (social.coalition || [])[0] || {};
    const topIssue = (social.issues?.top || [])[0] || {};
    const proPasPct = mn.pct?.["Pro-PAS"];
    const mnClearPct = mn.bucketsExpanded?.MN && mn.bucketsExpanded?.Solo
      ? Math.round((mn.bucketsExpanded.MN / (mn.bucketsExpanded.MN + mn.bucketsExpanded.Solo)) * 100)
      : 68;
    const labuPct = labu.pct?.["Sokong PAS"];

    set(
      "opsDecisionMain",
      "MN kekal laluan utama"
    );
    set(
      "opsDecisionText",
      `Data menunjukkan laluan paling mudah difahami: <strong>kekalkan naratif MN</strong>, bukan buka perdebatan solo. ` +
      `A/B jelas condong MN (${mnClearPct}%), naratif Pro-PAS ${proPasPct ?? "—"}%, ` +
      `dan Labu sokong PAS ${labuPct ?? "—"}%. ` +
      `Model majoriti juga masih letak <strong>${topCoalition.name || "MN"}</strong> sebagai lead (${topCoalition.pct ?? "—"}%).`
    );

    const actions = [
      {
        diff: "easy",
        label: "Mudah",
        text: "Hari ini: semua admin FB guna skrip sama — 'pilih MN (A), elak pecah undi, PH kalah'.",
      },
      {
        diff: "easy",
        label: "Mudah",
        text: `Labu N20: gerak mesej 'Labu for PAS' + 50 rumah / 1 lokaliti kerana sokongan digital ${labuPct ?? "—"}%.`,
      },
      {
        diff: "med",
        label: "Sederhana",
        text: `Rembau N26/N27: balas 30 komen Pro-PH/kritik dengan fakta tempatan, bukan debat panjang.`,
      },
      {
        diff: "hard",
        label: "Sukar",
        text: `War room: selaraskan naratif MN dengan UMNO/BN supaya isu ${topIssue.label || "perpaduan kaum"} tidak pecahkan momentum.`,
      },
    ];
    set(
      "opsActionList",
      actions
        .map((a) => `<li><span class="cmd-ops-pill ${a.diff}">${a.label}</span><span>${a.text}</span></li>`)
        .join("")
    );

    const focus = [
      ["N20", "Labu: sokongan PAS"],
      ["N27", "Rembau: post paling panas"],
      ["N26", "Chembong/Inche: balas kritik"],
      ["N28", "Kota: ulang poll"],
      ["N33", "PD: naikkan volume"],
    ];
    set(
      "opsFocusDuns",
      focus
        .map(([code, title]) => `<button type="button" class="cmd-ops-dun" data-ops-dun="${code}" title="${title}">${code}</button>`)
        .join("")
    );
    set(
      "opsFocusText",
      "Fokus bukan semua 36 kerusi serentak. Gerak dahulu DUN yang ada isyarat Cula dan boleh cepat ditindak."
    );
    set(
      "opsFocusNote",
      `KPI 72 jam: 30 balasan komen · 1 poster MN · 1 aktiviti Labu · 1 laporan ringkas ke HQ.`
    );

    panel.querySelectorAll("[data-ops-dun]").forEach((btn) => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = "1";
      btn.addEventListener("click", () => {
        const code = btn.getAttribute("data-ops-dun");
        if (typeof showPage === "function") showPage("dun");
        if (typeof selectDunSeat === "function") selectDunSeat(code);
      });
    });
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

  function liveBloc7Coalition() {
    if (currentState() !== "N9") return null;
    if (!window.N9Bloc7?.coalitionScenarios) return null;
    const seats = typeof DUN_SEATS !== "undefined" ? DUN_SEATS : [];
    if (!seats.length || !seats.some((s) => s.spr2023)) return null;
    const sliders =
      typeof bloc7Sliders !== "undefined" ? bloc7Sliders : window.N9Bloc7.DEFAULT_SLIDERS;
    const nudges = window.stateDemoHybrid?.bloc7Nudges || null;
    return window.N9Bloc7.coalitionScenarios(seats, sliders, nudges);
  }

  const DEMO_BAR_COLORS = {
    dpi: "#6366f1",
    socmed: "#22c55e",
  };

  function bucketLine(buckets, issue, expanded) {
    if (!buckets) return "—";
    if (issue === "PAS Labu") {
      const s = buckets["Sokong PAS"] || 0;
      const t = buckets["Tak Sokong PAS"] || 0;
      const m = expanded ? ` · Masih ${buckets["Masih Tidak Jelas"] || 0}` : "";
      return `Sokong ${s} · Tak ${t}${m}`;
    }
    const m = expanded ? ` · Masih ${buckets["Masih Tidak Jelas"] || 0}` : "";
    return `MN ${buckets.MN || 0} · Solo ${buckets.Solo || 0} · Pro-PAS ${buckets["Pro-PAS"] || 0} · Pro-PH ${buckets["Pro-PH"] || 0}${m}`;
  }

  function assumptionLine(assumption) {
    if (!assumption || !Object.keys(assumption).length) return "—";
    return Object.entries(assumption)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([k, v]) => `${k.replace(/^Assume→/, "")} ${v}`)
      .join(" · ");
  }

  function demoLine(demo) {
    if (!demo || !Object.keys(demo).length) return "—";
    return Object.entries(demo)
      .map(([k, v]) => `${k} ${v}%`)
      .join(" · ");
  }

  function renderCulaPollPostTable(posts) {
    if (!posts?.length) return "";
    const rows = posts
      .map((p) => {
        const unclear = (p.commentsCrawled || 0) - (p.buckets?.reported_total || 0);
        return `<tr>
          <td><strong>${p.page || "—"}</strong><br/><span style="color:var(--muted)">${p.primaryDun || "—"} · ${p.district || ""}</span></td>
          <td>${p.issue === "PAS Labu" ? "Labu" : "MN/Solo"}<br/><span style="color:var(--muted)">${p.commentsCrawled || 0} komen · ${unclear > 0 ? unclear + " tidak jelas" : "—"}</span></td>
          <td>${bucketLine(p.bucketsExpanded || p.buckets, p.issue, true)}<br/><span style="color:var(--muted);font-size:10px">Keyword: ${bucketLine(p.buckets, p.issue, false)}</span><br/><span style="color:var(--amber)">${p.insight || ""}</span></td>
          <td>${fmt(p.engagement)} eng<br/>${demoLine(p.demographic)}</td>
          <td style="font-size:10px;color:var(--muted)">${assumptionLine(p.assumption)}</td>
          <td><a href="${p.url || "#"}" target="_blank" rel="noopener">FB ↗</a></td>
        </tr>`;
      })
      .join("");
    return `<details class="cula-poll-details" open>
      <summary>Pecahan per post (7) — klik baris FB untuk post asal</summary>
      <table class="cula-poll-post-table">
        <thead><tr><th>Halaman / DUN</th><th>Soalan</th><th>Semua komen (inc. assumption)</th><th>Engagement · demo</th><th>Assumption breakdown</th><th></th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </details>`;
  }

  function renderCulaPollPanel(summary) {
    const panel = document.getElementById("cmdCulaPollPanel");
    if (!panel) return;
    const cp = summary || social?.culaPoll;
    if (!cp?.mnVsSolo?.headline && !cp?.pasLabu?.headline) {
      panel.classList.add("hidden");
      return;
    }
    panel.classList.remove("hidden");

    const mkPctBar = (pct, colors) => {
      const entries = Object.entries(pct || {});
      const segs = entries
        .map(([k, v]) => `<span class="seg" style="width:${v}%;background:${colors[k] || "var(--primary)"}" title="${k} ${v}%"></span>`)
        .join("");
      return `<div class="socmed-bar" style="margin:6px 0">${segs}</div>`;
    };

    const mnColors = { MN: "#a855f7", Solo: "#f59e0b", "Pro-PAS": "#22c55e", "Pro-PH": "#3b82f6" };
    const labuColors = { "Sokong PAS": "#22c55e", "Tak Sokong PAS": "#ef4444" };

    const full = culaPollFull || {};
    const byDun = full.byDun || {};
    const duns = (cp.dunsWithData || Object.keys(byDun)).slice(0, 8);
    const dunCards = duns
      .map((code) => {
        const dun = byDun[code] || {};
        const label = dun.pasLabu ? "Labu" : dun.mnVsSolo ? "MN/Solo" : "—";
        const n = (dun.pasLabu || dun.mnVsSolo || {}).commentsReported || 0;
        const posts = (dun.posts || []).length;
        return `<button type="button" class="cula-poll-dun-card clickable" data-cula-dun="${code}" title="Buka drawer ${code}">
          <strong>${code}</strong>${label} · ${n} jawapan · ${posts} post
        </button>`;
      })
      .join("");

    panel.innerHTML = `
      <h4>Cula Digital 204813 · Poll FB (7 post WhatsApp)</h4>
      <p class="desc">${cp.meta?.note || "Semua komen · Tidak Jelas dipecahkan sentiment+emotion"} · ${(cp.meta?.generated || "").slice(0, 16)}</p>
      <div class="cula-kpi-row" style="margin-bottom:12px">
        <div class="cula-kpi-mini"><div class="v">${fmt(full.meta?.totalComments || cp.mnVsSolo?.commentsTotal || 526)}</div><div class="l">Komen</div></div>
        <div class="cula-kpi-mini"><div class="v">${full.meta?.totalPosts || 7}</div><div class="l">Post</div></div>
        <div class="cula-kpi-mini"><div class="v">${fmt((cp.mnVsSolo?.engagement || 0) + (cp.pasLabu?.engagement || 0))}</div><div class="l">Engagement</div></div>
        <div class="cula-kpi-mini"><div class="v">${fmt((cp.mnVsSolo?.tidakJelasResolved || 0) + (cp.pasLabu?.tidakJelasResolved || 0))}</div><div class="l">Tidak jelas → assumption</div></div>
      </div>
      <p class="desc" style="margin:-4px 0 10px;font-size:11px">3-tier: <strong>Jelas</strong> + <strong>Debat→condong</strong> + <strong>Tidak Jelas→assumption</strong> · debat ≠ atas pagar</p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div>
          <div class="socmed-head"><h6 style="color:#c4b5fd">MN vs Solo — semua 458 komen (6 post)</h6></div>
          <div style="font-size:17px;font-weight:800;margin:4px 0;line-height:1.35">${cp.mnVsSolo?.headline || "—"}</div>
          ${mkPctBar(cp.mnVsSolo?.pct, { ...mnColors, "Masih Tidak Jelas": "#64748b" })}
          <p class="desc" style="margin:4px 0 0">${cp.mnVsSolo?.insight || ""}</p>
          <p class="desc" style="margin:2px 0 0;font-size:10px;color:var(--muted)">Keyword sahaja: ${cp.mnVsSolo?.headlineKeyword || "—"}</p>
        </div>
        <div>
          <div class="socmed-head"><h6 style="color:var(--green)">PAS Labu — semua 68 komen (N20)</h6></div>
          <div style="font-size:17px;font-weight:800;margin:4px 0;line-height:1.35">${cp.pasLabu?.headline || "—"}</div>
          ${mkPctBar(cp.pasLabu?.pct, { ...labuColors, "Masih Tidak Jelas": "#64748b" })}
          <p class="desc" style="margin:4px 0 0">${cp.pasLabu?.insight || ""}</p>
          <p class="desc" style="margin:2px 0 0;font-size:10px;color:var(--muted)">Keyword sahaja: ${cp.pasLabu?.headlineKeyword || "—"}</p>
        </div>
      </div>
      ${dunCards ? `<div class="cula-poll-dun-grid">${dunCards}</div>` : ""}
      ${renderCulaPollPostTable(full.byPost)}
      <p class="desc demo-footnote" style="margin-top:10px">↑ Jadual = 7 post penuh · klik kad DUN = drawer kerusi · assumption = sentiment+emotion untuk Tidak Jelas</p>`;

    panel.querySelectorAll("[data-cula-dun]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const code = btn.getAttribute("data-cula-dun");
        if (typeof showPage === "function") showPage("dun");
        if (typeof selectDunSeat === "function") selectDunSeat(code);
      });
    });
  }

  function renderDemographicHybridPanel(demo) {
    const panel = document.getElementById("cmdDemoHybridPanel");
    if (!panel) return;
    const hybrid = demo?.hybrid || demo;
    if (!hybrid?.dpi || currentState() !== "N9") {
      panel.classList.add("hidden");
      return;
    }
    panel.classList.remove("hidden");

    const rows = [
      { key: "malay", label: "Melayu / Bumiputera" },
      { key: "chinese", label: "Cina" },
      { key: "indian", label: "India" },
      { key: "urban", label: "Bandar / Campuran", socOnly: true },
    ];

    const bars = rows
      .filter((r) => !r.socOnly || hybrid.socmed?.[r.key] != null)
      .map((r) => {
        const dpi = r.socOnly ? 0 : (hybrid.dpi[r.key] ?? 0);
        const soc = hybrid.socmed?.[r.key] ?? 0;
        const delta = r.socOnly ? soc : (hybrid.delta?.[r.key] ?? soc - dpi);
        const deltaStr =
          r.key === "urban"
            ? `${soc}% naratif`
            : `${delta >= 0 ? "+" : ""}${typeof delta === "number" ? delta.toFixed(1) : delta}pp`;
        return `
        <div class="demo-hybrid-row">
          <span class="demo-hybrid-label">${r.label}</span>
          <div class="demo-hybrid-bars">
            ${r.socOnly ? "" : `<div class="demo-bar-wrap" title="DPI pengundi ${dpi}%"><span class="demo-bar-tag">DPI</span><div class="demo-bar-track"><i style="width:${Math.min(100, dpi)}%;background:${DEMO_BAR_COLORS.dpi}"></i></div><span class="demo-bar-pct">${dpi}%</span></div>`}
            <div class="demo-bar-wrap" title="Socmed proxy ${soc}%"><span class="demo-bar-tag">SOC</span><div class="demo-bar-track"><i style="width:${Math.min(100, soc)}%;background:${DEMO_BAR_COLORS.socmed}"></i></div><span class="demo-bar-pct">${soc}%</span></div>
          </div>
          <span class="demo-hybrid-delta ${delta > 3 ? "delta-up" : delta < -3 ? "delta-down" : ""}">${deltaStr}</span>
        </div>`;
      })
      .join("");

    const nudges = (hybrid.adjustmentNotes || []).slice(0, 3);
    const nudgeHtml = nudges.length
      ? `<ul class="demo-nudge-list">${nudges.map((n) => `<li>${n}</li>`).join("")}</ul>`
      : "";

    const conf = hybrid.confidenceScale != null && hybrid.confidenceScale < 1
      ? `<p class="desc" style="color:var(--amber);margin-top:6px">Keyakinan nudge ×${Math.round(hybrid.confidenceScale * 100)}% — ${hybrid.dunMentionsWeighted ?? "—"} mention dikait per-DUN (lebih crawl = lebih tepat)</p>`
      : "";

    panel.innerHTML = `
      <h4>Demografi N9 · DPI vs Naratif Socmed</h4>
      <p class="desc">${hybrid.insight || ""} · ${hybrid.disclaimer || ""}</p>
      <div class="demo-hybrid-legend">
        <span><i style="background:${DEMO_BAR_COLORS.dpi}"></i> DPI Dec 2025 (pengundi)</span>
        <span><i style="background:${DEMO_BAR_COLORS.socmed}"></i> Socmed (proxy bahasa · ${hybrid.mentionsWeighted ?? "—"} post N9)</span>
      </div>
      <div class="demo-hybrid-grid">${bars}</div>
      ${nudgeHtml}${conf}
      <p class="desc demo-footnote">Penyesuaian demografi dipaparkan pada bar <strong>Peluang Majoriti</strong> (#1 PAS · #3 MN · #4/#7 PN · #5 PH) — selari slider 7-bloc.</p>`;
  }

  function renderCoalitionBars(items, isProd, socialSummary) {
    const el = document.getElementById("coalitionBars");
    if (!el) return;
    const live = liveBloc7Coalition();
    const src = socialSummary || social;
    const formation = src?.coalitionFormation;
    const raw = live || formation?.scenarios || items || MOCK_COALITION;
    const sorted = [...raw].sort(
      (x, y) => (y.majorityPct ?? y.pct ?? 0) - (x.majorityPct ?? x.pct ?? 0)
    );
    const total = formation?.totalSeats || cfg().dun || 36;
    const descEl = document.getElementById("cmdCoalitionDesc");
    if (descEl && live) {
      const b = typeof bloc7Sliders !== "undefined" ? bloc7Sliders : window.N9Bloc7.DEFAULT_SLIDERS;
      const jobFx = window.stateDemoHybrid?.jobBloc7Effects;
      const demoNote = window.stateDemoHybrid?.bloc7Nudges
        ? " · nudge demografi + Job1/2"
        : "";
      const jobNote = jobFx?.effects?.length
        ? ` · Job poll MN +${jobFx.nudges_pp?.mn || 0}pp`
        : "";
      descEl.textContent =
        `${cfg().coalitionDesc} · Bersama −${b.bersamaPct}% PH${demoNote}${jobNote}`;
    } else if (descEl) {
      const peng = src?.pengundiMacPosts?.post3_poll;
      const pengNote =
        peng?.sokong_bn_pn_pct != null
          ? ` · Pengundi MY poll BN+PN ${peng.sokong_bn_pn_pct}%`
          : "";
      descEl.textContent = cfg().coalitionDesc + pengNote;
    }
    el.innerHTML = sorted
      .map((c) => {
        const isHungRisk = /risiko tiada majoriti/i.test(c.name || "");
        const isImpact = c.blocId === "bersama";
        let seatText;
        if (isHungRisk) seatText = c.seatLabel || `tiada bloc ≥${cfg().majority || 19}`;
        else if (c.seatLabel && isImpact) seatText = c.seatLabel;
        else if (c.expectedSeats != null) seatText = `~${c.expectedSeats}/${total}`;
        else seatText = "—";
        const mp = c.majorityPct != null ? c.majorityPct : c.pct;
        const barW = Math.max(4, Math.min(100, mp));
        const color = c.color || "var(--primary)";
        return `
      <div class="coal-row" title="${(c.assumption || "").replace(/"/g, "&quot;")}">
        <span class="name">${c.name}</span>
        <span class="seats">${seatText}</span>
        <div class="coal-bar"><div style="width:${barW}%;background:${color}"></div></div>
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
      window.stateDemoHybrid = social.demographics?.hybrid || null;
      renderCommandKpisN9();
      renderN9OpsBriefPanel();
      renderDemographicHybridPanel(social.demographics);
      renderCulaPollPanel(culaPollSummary || social.culaPoll);
      renderPengundiMacPostsPanel(social.pengundiMacPosts || bundle?.pengundiMacPosts);
      renderN9NarrativeCommunityPanel(social.narrativeCommunity, typeof DATA !== "undefined" ? DATA.N9 : null);
      renderCoalitionBars(social.coalition || MOCK_COALITION, true, social);
      const note = social?.issues?.windowNote || "24 jam sebelum tarikh crawl terakhir";
      const narrIssues = narrativeIssueRows("N9");
      const combined = narrIssues
        ? [...(social.issues?.top || []).slice(0, 3), ...narrIssues.slice(0, 3)]
        : social.issues?.top || MOCK_ISSUES;
      renderIssueHeatmap(
        combined,
        narrIssues
          ? `Hybrid: master crawl + naratif Cina/India · ${note}`
          : `Issue heatmap — ${note} · master crawl N9`
      );
    } else if (st === "N9" && dailyOps?.keputusan) {
      renderN9OpsBriefPanel();
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

  window.refreshProductionCoalition = function refreshProductionCoalition() {
    if (currentState() !== "N9") return;
    renderCoalitionBars(social?.coalition || MOCK_COALITION, true, social);
  };
})();
