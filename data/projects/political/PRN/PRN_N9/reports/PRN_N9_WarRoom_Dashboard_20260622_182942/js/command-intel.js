/**
 * Command Center — analytics matrix (23 kerusi PAS)
 * Taktikal penuh → DUN Drill-Down drawer (CommandIntel.getSeatPlaybook)
 */
(function () {
  let intelCache = null;
  let socmedCache = null;
  let pasTargetCache = null;
  let lastCulaHub = null;
  let lastSeatsCache = [];

  const TYPE_LABEL = {
    jentera: "Jentera lapangan",
    online: "Online & socmed",
    pantau: "Pantau & intel",
    lapor: "Lapor & HQ",
  };

  function fmt(n) {
    if (n == null || n === "") return "—";
    return Number(n).toLocaleString("en-MY");
  }

  function normCode(id) {
    if (!id) return "";
    return String(id).replace(/\./g, "").replace(/^n/i, "N").toUpperCase();
  }

  function winProbClass(p) {
    if (p == null || p === "") return "prob-muted";
    if (p >= 60) return "prob-high";
    if (p >= 45) return "prob-mid";
    return "prob-low";
  }

  async function loadIntelPack(st) {
    const paths = {
      N9: "data/war_room_intel_N9.json",
      Johor: "data/war_room_intel_Johor.json",
      Melaka: "data/war_room_intel_Melaka.json",
    };
    try {
      const res = await fetch(paths[st] || paths.N9);
      if (res.ok) return await res.json();
    } catch { /* fallback */ }
    return { hari_ini: { date: null, items: [] }, socmed_rollups: {} };
  }

  async function loadSocmedByDun(st) {
    const paths = {
      N9: "data/socmed_by_dun_N9.json",
      Johor: "data/socmed_by_dun_Johor.json",
      Melaka: "data/socmed_by_dun_Melaka.json",
    };
    const path = paths[st];
    if (!path) return null;
    try {
      const res = await fetch(path);
      if (res.ok) return await res.json();
    } catch { /* fallback */ }
    return null;
  }

  async function loadPasTarget(st) {
    if (st !== "N9") return null;
    for (const path of ["data/pas_target_23_N9.json", "data/pas_target_16_N9.json"]) {
      try {
        const res = await fetch(path);
        if (res.ok) return await res.json();
      } catch { /* next */ }
    }
    return null;
  }

  function socFor(code) {
    return socmedCache?.byDun?.[code] || null;
  }

  function warFromTarget(t) {
    if (!t) return {};
    const kategori_pas =
      t.seatRole === "sasaran_flip" ? "winnable" : t.seatRole === "pertahan_pas" ? "defend" : "defend";
    const kategori_label =
      t.kategoriPasLabel ||
      (t.seatRole === "sasaran_flip" ? "Sasaran Menang" : t.seatRole === "pertahan_pas" ? "Pertahan PAS" : "Pertahan PN");
    return {
      kategori_label,
      kategori_pas,
      bkc_cula: t.dpi?.bkcCula,
      cula_pct: t.dpi?.culaPct,
      mn_calon: t.challenger ? null : undefined,
      challenger: t.challenger,
      pas_win_prob: t.pasWinProb,
    };
  }

  function mergePasTargetSeats(culaHub, pack) {
    const byDun = culaHub?.byDun || {};
    const warByCode = {};
    (pack?.hari_ini?.items || []).forEach((w) => {
      warByCode[w.kod_dun] = w;
    });
    const targetByCode = {};
    (pasTargetCache?.seats || []).forEach((t) => {
      targetByCode[t.code] = t;
    });
    const codes = pasTargetCache?.codes || Object.keys(targetByCode);

    return codes
      .map((code) => {
        const t = targetByCode[code] || { code, name: byDun[code]?.name || "" };
        const war = { ...warFromTarget(t), ...(warByCode[code] || {}) };
        return buildSeat(code, t.name || byDun[code]?.name, war, byDun[code] || {}, socFor(code), t);
      })
      .sort((a, b) => a.priority - b.priority);
  }

  function mergeSeats(culaHub, pack) {
    const st = typeof state !== "undefined" ? state : "N9";
    if (st === "N9" && pasTargetCache?.codes?.length) {
      return mergePasTargetSeats(culaHub, pack);
    }

    const byDun = culaHub?.byDun || {};
    const warItems = pack?.hari_ini?.items || [];
    const seen = new Set();
    const seats = [];

    warItems.forEach((w) => {
      const code = w.kod_dun;
      seen.add(code);
      seats.push(buildSeat(code, w.kawasan || byDun[code]?.name, w, byDun[code] || {}, socFor(code)));
    });

    Object.entries(socmedCache?.byDun || {})
      .filter(([code, s]) => !seen.has(code) && (s.mentions_24h > 0 || s.mentions_7d >= 3))
      .sort((a, b) => (b[1].mentions_24h || 0) - (a[1].mentions_24h || 0))
      .slice(0, 2)
      .forEach(([code]) => {
        seen.add(code);
        seats.push(buildSeat(code, byDun[code]?.name, {}, byDun[code] || {}, socFor(code)));
      });

    Object.entries(byDun)
      .filter(([code, c]) => !seen.has(code) && ((c.verified_delta_24h || 0) > 0 || (c.bkc_cula ?? 0) < -8000))
      .sort((a, b) => (a[1].bkc_cula ?? 0) - (b[1].bkc_cula ?? 0))
      .slice(0, 4)
      .forEach(([code, c]) => {
        seats.push(buildSeat(code, c.name, {}, c, socFor(code)));
      });

    return seats.sort((a, b) => a.priority - b.priority).slice(0, 8);
  }

  function simplifyJenteraHint(hint) {
    return hint
      .replace(/^JENTERA:\s*/i, "")
      .replace(/BKC\s*-?\d[\d,]*/gi, "")
      .replace(/SKT\s*\d[\d,]*/gi, "")
      .replace(/\s{2,}/g, " ")
      .trim();
  }

  function buildActionItems(war, code, name, ctx) {
    const { bkc, delta24, mentions24, negPct } = ctx;
    const items = [];
    const calon = war.mn_calon || war.challenger;

    if (war.jentera_hint) {
      items.push({
        type: "jentera",
        urgent: true,
        text: simplifyJenteraHint(war.jentera_hint) || "Intensifkan lawatan pengundi hari ini.",
      });
    } else if (bkc != null && bkc < -8000) {
      items.push({
        type: "jentera",
        urgent: true,
        text: "Lawati pengundi (door-to-door): sasaran minimum 20 rumah setiap PDM — fokus Bulan & Condong Bulan.",
      });
    }

    if (delta24 === 0 && bkc != null && bkc < -8000) {
      items.push({
        type: "lapor",
        urgent: true,
        text: "Hantar laporan cula sebelum 18:00 — guna Modul Culaan Digital (borang lapangan atau upload batch).",
      });
    } else if (delta24 > 0) {
      items.push({
        type: "lapor",
        urgent: false,
        text: `Kekalkan tempo — cula +${delta24} masuk 24j lepas. Teruskan & lapor setiap hari.`,
      });
    }

    if (mentions24 >= 3 && negPct >= 15) {
      items.push({
        type: "online",
        urgent: true,
        text: "Ada tekanan online — sediakan jawapan rasmi, balas komen dalam 4 jam, maklum war room jika viral.",
      });
    } else if (mentions24 >= 3) {
      items.push({
        type: "online",
        urgent: false,
        text: "Semak post & komen berkait kerusi — pastikan mesej selari dengan operasi lapangan.",
      });
    }

    if (calon) {
      items.push({
        type: "pantau",
        urgent: mentions24 >= 5,
        text: `Pantau calon lawan (${calon}) — socmed, ceramah, isu yang dibawa.`,
      });
    }

    const crawlText = war.action_text || `Pantau keyword "PRN ${code} ${name || ""}" — semak 2 kali sehari semasa kempen.`;
    items.push({
      type: "pantau",
      urgent: false,
      text: crawlText.replace(/^Crawl keyword:\s*/i, "Pantau keyword: "),
    });

    if (!items.some((i) => i.type === "jentera")) {
      items.unshift({
        type: "jentera",
        urgent: false,
        text: "Teruskan lawatan pengundi mengikut jadual PDM — catat setiap lawatan dalam sistem cula.",
      });
    }

    const seen = new Set();
    return items.filter((i) => {
      const k = i.type + i.text.slice(0, 40);
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    }).slice(0, 5);
  }

  function buildSituasi(war, ctx) {
    const { bkc, delta24, mentions24, negPct, kategori, alertLevel, seatRole } = ctx;
    const parts = [];

    if (seatRole === "pertahan_pas") {
      parts.push("Kerusi pertahan PAS — kekalkan pengundi sedia ada & halang flip PH/BN.");
    } else if (seatRole === "pertahan_pn") {
      parts.push("Kerusi pertahan PN (Bersatu) — konsolidasi undi, elak 3 penjuru.");
    } else if (seatRole === "sasaran_flip") {
      parts.push("Kerusi sasaran menang — push jentera & naratif calon lawan.");
    }

    if (alertLevel === "critical") {
      parts.push("Keutamaan tinggi — tindakan hari ini diperlukan.");
    }

    if (bkc != null && bkc < -12000 && delta24 === 0) {
      parts.push("Lawatan pengundi masih jauh dari sasaran & tiada kemasukan baru 24j lepas.");
    } else if (bkc != null && bkc < -8000) {
      parts.push("Lawatan pengundi perlu dipercepatkan.");
    } else if (delta24 >= 10) {
      parts.push("Momentum lawatan baik — kekalkan tempo.");
    }

    if (mentions24 >= 5 && negPct >= 20) {
      parts.push("Tekanan naratif online aktif.");
    } else if (mentions24 >= 3) {
      parts.push("Perbincangan online berlangsung — pantau & selaraskan mesej.");
    }

    if (!parts.length) {
      if (kategori === "Pertahan") return "Kerusi pertahanan — kekalkan operasi rutin & pastikan cula dicatat.";
      if (kategori === "Boleh Menang") return "Kerusi boleh menang — push jentera & naratif calon lawan.";
      return "Situasi terkawal — ikut senarai tindakan rutin di bawah.";
    }

    return parts.join(" ");
  }

  function buildSeat(code, name, war, cula, soc, targetMeta) {
    const t = targetMeta || {};
    const bkc = cula.bkc_cula ?? war.bkc_cula ?? t.dpi?.bkcCula ?? null;
    const delta24 = cula.verified_delta_24h || 0;
    const culaPct = cula.digital_cula_pct ?? cula.baseline_cula_pct ?? war.cula_pct ?? t.dpi?.culaPct ?? null;
    const mentions24 = soc?.mentions_24h ?? war.mentions ?? 0;
    const negPct = soc?.neg_pct ?? war.neg_pct ?? 0;
    const socAlert = soc?.alert_level || "ok";
    const kategori = war.kategori_label || t.seatRoleLabel || "Pantau";
    const kategoriClass =
      war.kategori_pas === "target" || t.seatRole === "sasaran_flip"
        ? "target"
        : war.kategori_pas === "winnable"
          ? "winnable"
          : "defend";
    const pasWinProb = t.pasWinProb ?? war.pas_win_prob ?? null;

    let priority = 50;
    if (bkc != null && bkc < -15000) priority -= 30;
    else if (bkc != null && bkc < -8000) priority -= 15;
    if (delta24 === 0 && bkc != null && bkc < -10000) priority -= 10;
    if (mentions24 >= 5 && negPct > 20) priority -= 12;
    else if (mentions24 >= 3) priority -= 5;
    if (socAlert === "critical") priority -= 10;
    else if (socAlert === "warning") priority -= 6;

    let alertLevel = "ok";
    if ((bkc != null && bkc < -15000 && delta24 === 0) || socAlert === "critical") alertLevel = "critical";
    else if ((bkc != null && bkc < -10000) || socAlert === "warning") alertLevel = "warn";

    const ctx = { bkc, delta24, mentions24, negPct, kategori, alertLevel, seatRole: t.seatRole };
    const actionItems = buildActionItems(war, code, name, ctx);
    const situasi = buildSituasi(war, ctx);

    const incumbentLine =
      t.party2023 && t.winnerName2023
        ? `Penyandang PRN 2023: ${t.party2023} (${t.winner2023}) — ${t.winnerName2023}`
        : null;

    return {
      code,
      name: name || cula.name || t.name || "",
      kategori,
      kategoriClass,
      pasTier: t.pasTier || null,
      pasTierLabel: t.pasTierLabel || null,
      seatRole: t.seatRole || null,
      seatRoleLabel: t.seatRoleLabel || null,
      pasWinProb,
      incumbentLine,
      situasi,
      actionItems,
      alertLevel,
      priority,
      mnCalon: war.mn_calon || t.challenger || null,
      challenger: t.challenger || null,
      priorityLabel: alertLevel === "critical" ? "SEGERA" : alertLevel === "warn" ? "PERHATIAN" : "RUTIN",
      priorityCode: alertLevel === "critical" ? "P1" : alertLevel === "warn" ? "P2" : "P3",
      primaryAction: actionItems.find((a) => a.urgent)?.text || actionItems[0]?.text || "—",
      _raw: { bkc, delta24, culaPct, mentions24, negPct },
    };
  }

  function buildExecutiveBrief(seats, culaHub) {
    const s = culaHub?.summary || {};
    const p1 = seats.filter((x) => x.alertLevel === "critical").length;
    const p2 = seats.filter((x) => x.alertLevel === "warn").length;
    const onlineHot = seats.filter((x) => x._raw.mentions24 >= 3 && x._raw.negPct >= 15).length;
    const tm = pasTargetCache?.meta;
    const withCula24 = seats.filter((x) => x._raw.delta24 > 0).length;

    const bullets = [];

    if (tm?.count) {
      const w = tm.wajibCount || 16;
      const im = tm.imbangCount || 7;
      bullets.push({
        level: "ok",
        text: `<strong>${tm.count} kerusi contest PAS</strong> — ${w} wajib + ${im} imbang · ${tm.pasIncumbent2023 || 0} pertahan PAS · ${tm.pnIncumbent2023 || 0} pertahan PN · ${(tm.flipTarget2023 || 0) + (tm.imbangFlip2023 || 0)} sasaran flip.`,
      });
    }

    bullets.push({
      level: p1 ? "critical" : p2 ? "warn" : "ok",
      text: p1
        ? `<strong>${p1} kerusi P1</strong> perlu tindakan segera — klik baris dalam matriks untuk checklist penuh.`
        : p2
          ? `<strong>${p2} kerusi P2</strong> perlu perhatian — jangan tangguh operasi lapangan.`
          : `<strong>${seats.length} kerusi</strong> dalam portfolio — semak matriks keutamaan.`,
    });

    bullets.push({
      level: (s.verified_delta_24h || 0) === 0 ? "warn" : "good",
      text:
        (s.verified_delta_24h || 0) > 0
          ? `Operasi lapangan: <strong>${withCula24}/${seats.length}</strong> kerusi ada cula 24j · negeri +${fmt(s.verified_delta_24h)}.`
          : `Tiada cula baru 24j — <strong>wajib hantar laporan lapangan sebelum 18:00</strong> (Modul Culaan Digital).`,
    });

    if (onlineHot) {
      bullets.push({
        level: "warn",
        text: `<strong>${onlineHot} kerusi</strong> ada tekanan online — lihat lajur Online dalam matriks.`,
      });
    }

    return bullets;
  }

  function buildPortfolioStats(seats) {
    const tm = pasTargetCache?.meta || {};
    const high = seats.filter((s) => s.pasWinProb != null && s.pasWinProb >= 60).length;
    const mid = seats.filter((s) => s.pasWinProb != null && s.pasWinProb >= 45 && s.pasWinProb < 60).length;
    const low = seats.filter((s) => s.pasWinProb != null && s.pasWinProb < 45).length;
    return {
      total: seats.length,
      high,
      mid,
      low,
      pasDef: tm.pasIncumbent2023 || seats.filter((s) => s.seatRole === "pertahan_pas").length,
      pnDef: tm.pnIncumbent2023 || seats.filter((s) => s.seatRole === "pertahan_pn").length,
      flip: seats.filter((s) => s.seatRole === "sasaran_flip").length,
      wajib: tm.wajibCount || seats.filter((s) => s.pasTier === "wajib").length,
      imbang: tm.imbangCount || seats.filter((s) => s.pasTier === "imbang").length,
    };
  }

  function buildTopAlerts(seats, limit = 5) {
    return seats
      .filter((s) => s.alertLevel === "critical" || s.alertLevel === "warn")
      .slice(0, limit)
      .map((s) => ({
        code: s.code,
        name: s.name,
        level: s.alertLevel,
        text: s.primaryAction,
        pasWinProb: s.pasWinProb,
      }));
  }

  function mdBold(s) {
    return s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  }

  function renderActionList(items) {
    return items
      .map(
        (a, i) => `
      <li class="task-item task-${a.type}${a.urgent ? " task-urgent" : ""}">
        <span class="task-num">${i + 1}</span>
        <div class="task-body">
          <span class="task-type">${TYPE_LABEL[a.type] || a.type}</span>
          <span class="task-text">${a.text}</span>
        </div>
      </li>`
      )
      .join("");
  }

  function culaCell(s) {
    const d = s._raw.delta24;
    if (d > 0) return `<span class="cell-good">+${d}</span>`;
    if (d === 0 && s._raw.bkc != null && s._raw.bkc < -8000) return `<span class="cell-warn">⚠ tiada</span>`;
    return `<span class="cell-muted">${d === 0 ? "0" : fmt(d)}</span>`;
  }

  function onlineCell(s) {
    const { mentions24, negPct } = s._raw;
    if (mentions24 >= 3 && negPct >= 15) return `<span class="cell-bad">Tekanan</span>`;
    if (mentions24 >= 3) return `<span class="cell-warn">Aktif</span>`;
    return `<span class="cell-muted">—</span>`;
  }

  function toDunId(code) {
    const c = normCode(code);
    const num = c.replace(/^N/i, "");
    return `N.${num.padStart(2, "0")}`;
  }

  function openDunFromCode(code) {
    const id = normCode(code);
    if (typeof window.openSeatChecklistDrawer === "function") {
      window.openSeatChecklistDrawer(id);
      return;
    }
    if (typeof showPage === "function" && typeof selectDunSeat === "function") {
      showPage("dun");
      setTimeout(() => selectDunSeat(toDunId(code)), 300);
    }
  }

  function renderPortfolioBar(stats) {
    return `
      <div class="pas-portfolio">
        <div class="pas-portfolio-seg pas-seg-def"><span>Pertahan PAS</span><strong>${stats.pasDef}</strong></div>
        <div class="pas-portfolio-seg pas-seg-pn"><span>Pertahan PN</span><strong>${stats.pnDef}</strong></div>
        <div class="pas-portfolio-seg pas-seg-flip"><span>Sasaran flip</span><strong>${stats.flip}</strong></div>
        <div class="pas-portfolio-seg pas-seg-tier"><span>Wajib / Imbang</span><strong>${stats.wajib} / ${stats.imbang}</strong></div>
      </div>
      <div class="pas-prob-summary">
        Peluang menang (model): <strong class="prob-high">${stats.high}</strong> kerusi ≥60%
        · <strong class="prob-mid">${stats.mid}</strong> 45–59%
        · <strong class="prob-low">${stats.low}</strong> &lt;45%
        <span class="pas-prob-note">· rule-based, bukan polling</span>
      </div>`;
  }

  function renderTopAlerts(alerts) {
    if (!alerts.length) return "";
    return `
      <div class="pas-top-alerts" id="pasTopAlerts">
        <h6>Top ${alerts.length} keutamaan hari ini</h6>
        <p class="pas-top-hint">👇 Klik baris kerusi (contoh ${alerts.map((a) => a.code).join(", ")}) → panel checklist terbuka di kanan</p>
        <ul>${alerts.map((a) => `
          <li class="pas-alert pas-alert-${a.level}">
            <button type="button" class="pas-alert-btn" data-dun="${a.code}">
              <span class="pas-alert-code">${a.code}</span>
              <span class="pas-alert-text">${a.text}</span>
              ${a.pasWinProb != null ? `<span class="pas-alert-prob ${winProbClass(a.pasWinProb)}">${a.pasWinProb}%</span>` : ""}
            </button>
          </li>`).join("")}</ul>
      </div>`;
  }

  function renderMatrix(seats) {
    return `
      <div class="pas-matrix-wrap">
        <table class="pas-matrix">
          <thead>
            <tr>
              <th>Kerusi</th>
              <th>Peranan</th>
              <th>% Menang</th>
              <th>Cula 24j</th>
              <th>Online</th>
              <th>P</th>
              <th>Tindakan #1</th>
            </tr>
          </thead>
          <tbody>
            ${seats.map((s) => `
              <tr class="pas-row pas-row-${s.alertLevel}" data-dun="${s.code}" tabindex="0" role="button" title="Klik untuk checklist penuh">
                <td class="pas-cell-seat"><strong>${s.code}</strong> ${s.name}</td>
                <td><span class="task-role task-role-${s.seatRole || "flip"}">${s.seatRoleLabel || s.kategori}</span></td>
                <td><span class="pas-prob ${winProbClass(s.pasWinProb)}">${s.pasWinProb != null ? s.pasWinProb + "%" : "—"}</span></td>
                <td>${culaCell(s)}</td>
                <td>${onlineCell(s)}</td>
                <td><span class="task-priority task-priority-${s.alertLevel}">${s.priorityCode}</span></td>
                <td class="pas-cell-action">${s.primaryAction.slice(0, 72)}${s.primaryAction.length > 72 ? "…" : ""}</td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>
      <div class="pas-matrix-foot">
        <button type="button" class="btn-sm btn-primary" id="cmdOpenDunMap">Buka peta 23 kerusi →</button>
        <span class="pas-matrix-hint">Klik baris kerusi untuk checklist taktikal penuh</span>
      </div>`;
  }

  function bindMatrixEvents(feedEl) {
    feedEl.querySelectorAll(".pas-row, .pas-alert-btn").forEach((el) => {
      el.addEventListener("click", () => openDunFromCode(el.dataset.dun));
      el.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openDunFromCode(el.dataset.dun);
        }
      });
    });
    $("cmdOpenDunMap")?.addEventListener("click", () => {
      if (typeof showPage === "function") {
        dunFilter = "pas23";
        showPage("dun");
      }
    });
  }

  function renderIntelFeed(culaHub) {
    const execEl = $("cmdIntelExec");
    const feedEl = $("cmdIntelFeed");
    const metaEl = $("cmdIntelMeta");

    if (!culaHub) {
      if (execEl) execEl.innerHTML = "";
      if (feedEl) feedEl.innerHTML = `<p class="intel-empty">Memuatkan analitik…</p>`;
      return;
    }

    const seats = mergeSeats(culaHub, intelCache);
    lastSeatsCache = seats;
    const brief = buildExecutiveBrief(seats, culaHub);
    const stats = buildPortfolioStats(seats);
    const alerts = buildTopAlerts(seats, 5);
    const p1 = seats.filter((x) => x.alertLevel === "critical").length;
    const p2 = seats.filter((x) => x.alertLevel === "warn").length;

    if (!execEl && !feedEl && !metaEl) return;

    if (execEl) {
      execEl.innerHTML = brief
        .map(
          (b) => `
        <div class="intel-brief intel-brief-${b.level}">
          <span class="intel-brief-dot"></span>
          <span>${mdBold(b.text)}</span>
        </div>`
        )
        .join("");
    }

    if (metaEl) {
      const date = intelCache?.hari_ini?.date;
      const tm = pasTargetCache?.meta;
      const parts = [];
      if (tm?.count) parts.push(`${tm.count} kerusi PAS`);
      if (date) parts.push(`playbook ${date}`);
      metaEl.textContent = parts.length
        ? `Matriks keutamaan · ${parts.join(" · ")} · klik kerusi = checklist (panel kanan)`
        : "Klik kerusi merah/jingga untuk checklist taktikal · tutup (×) bila selesai";
    }

    if (!feedEl) return;

    if (!seats.length) {
      feedEl.innerHTML = `
        <p class="intel-empty">Belum ada data kerusi.
        <button type="button" class="btn-sm btn-green" onclick="showPage('cula')">Masukkan data cula</button></p>`;
      return;
    }

    feedEl.innerHTML = renderPortfolioBar(stats) + renderTopAlerts(alerts) + renderMatrix(seats);
    bindMatrixEvents(feedEl);
  }

  function getSeatPlaybook(codeOrId) {
    const code = normCode(codeOrId);
    return lastSeatsCache.find((s) => normCode(s.code) === code) || null;
  }

  window.refreshCommandIntel = async function refreshCommandIntel(culaHub) {
    lastCulaHub = culaHub;
    const st = typeof state !== "undefined" ? state : "N9";
    intelCache = await loadIntelPack(st);
    socmedCache = await loadSocmedByDun(st);
    pasTargetCache = await loadPasTarget(st);
    renderIntelFeed(culaHub);
  };

  window.CommandIntel = {
    getSeatPlaybook,
    renderActionListHtml: renderActionList,
    buildSeats: (culaHub) => {
      if (culaHub) lastCulaHub = culaHub;
      return mergeSeats(lastCulaHub, intelCache);
    },
    exportWhatsAppText(seat, playbook) {
      if (!playbook) return "";
      const lines = [
        `*${playbook.code} ${playbook.name}*`,
        playbook.seatRoleLabel || playbook.kategori,
        playbook.pasWinProb != null ? `Peluang menang: ${playbook.pasWinProb}%` : "",
        playbook.incumbentLine || "",
        "",
        playbook.situasi,
        "",
        "*Untuk menang — buat hari ini:*",
        ...playbook.actionItems.map((a, i) => `${i + 1}. [${TYPE_LABEL[a.type]}] ${a.text}`),
      ].filter(Boolean);
      return lines.join("\n");
    },
  };
})();
