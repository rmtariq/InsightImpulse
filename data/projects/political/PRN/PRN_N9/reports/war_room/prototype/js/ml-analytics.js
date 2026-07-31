/**
 * InsightPulse ML Analytics — PRN N9 war room panel
 * Selari dengan Keputusan & Tindakan Hari Ini via n9_daily_ops.json
 */
(function () {
  const ML_DATA_PATH = "data/n9_ml_predictions.json";
  const DAILY_OPS_PATH = "data/n9_daily_ops.json";
  const MN_PRODUCTION_PATH = "data/warroom_dun_N9_production.json";
  const API_PATH = "/api/ml/predict/prn_n9";
  const MN_MAJORITY = 19;

  let mlCache = null;
  let dailyOpsCache = null;
  let mnSeatCodes = null;

  function pct(v) {
    if (v == null || v === "") return "—";
    const n = Number(v);
    if (Number.isNaN(n)) return "—";
    if (n > 1) return `${Math.round(n)}%`;
    return `${Math.round(n * 100)}%`;
  }

  function seatMlPct(seat) {
    if (seat.peluang_ml_pct != null) return `${seat.peluang_ml_pct}%`;
    if (seat.ml_competitive_prob != null) return pct(seat.ml_competitive_prob);
    return "—";
  }

  function tierBadge(tier) {
    const map = {
      descriptive: { cls: "ml-tier-desc", label: "Deskriptif" },
      predictive: { cls: "ml-tier-pred", label: "Ramalan" },
      prescriptive: { cls: "ml-tier-presc", label: "Tindakan" },
    };
    const t = map[tier] || map.descriptive;
    return `<span class="ml-tier ${t.cls}">${t.label}</span>`;
  }

  async function fetchDailyOps() {
    if (dailyOpsCache) return dailyOpsCache;
    try {
      const res = await fetch(DAILY_OPS_PATH + "?_=" + Date.now());
      if (res.ok) {
        dailyOpsCache = await res.json();
        return dailyOpsCache;
      }
    } catch { /* fallback */ }
    return null;
  }

  async function fetchMlData() {
    if (mlCache) return mlCache;

    const origins = [""];
    if (window.location.port !== "8001") {
      origins.push("http://127.0.0.1:8001");
    }

    for (const origin of origins) {
      try {
        const res = await fetch(`${origin}${API_PATH}`);
        if (res.ok) {
          const body = await res.json();
          if (body.success && body.result) {
            mlCache = body.result;
            return mlCache;
          }
        }
      } catch { /* next */ }
    }

    try {
      const res = await fetch(ML_DATA_PATH);
      if (res.ok) {
        mlCache = await res.json();
        return mlCache;
      }
    } catch { /* fallback */ }

    return null;
  }

  function renderModels(predictive, dailyOps) {
    const cv = dailyOps?.model_cv;
    if (cv && Object.keys(cv).length) {
      return Object.entries(cv)
        .map(([name, s]) => {
          const label = name.replace(/_/g, " ").toUpperCase();
          return `<div class="ml-model-row">
            <span class="ml-model-name">${label}</span>
            <span class="ml-model-metric">Ketepatan <strong>${pct(s.accuracy)}</strong></span>
            <span class="ml-model-metric">F1 <strong>${pct(s.f1)}</strong></span>
          </div>`;
        })
        .join("");
    }
    if (!predictive?.models) return "<p class='ml-muted'>Model belum dilatih — data tidak mencukupi.</p>";
    return Object.entries(predictive.models)
      .filter(([, s]) => s.cv_accuracy_mean != null)
      .map(([name, s]) => {
        const label = name.replace(/_/g, " ").toUpperCase();
        return `<div class="ml-model-row">
          <span class="ml-model-name">${label}</span>
          <span class="ml-model-metric">Ketepatan <strong>${pct(s.cv_accuracy_mean)}</strong></span>
          <span class="ml-model-metric">F1 <strong>${pct(s.cv_f1_mean)}</strong></span>
        </div>`;
      })
      .join("") || "<p class='ml-muted'>Tiada metrik CV.</p>";
  }

  async function fetchMnSeatCodes(dailyOps) {
    if (dailyOps?.mn20_codes?.length) {
      mnSeatCodes = new Set(dailyOps.mn20_codes);
      return mnSeatCodes;
    }
    if (mnSeatCodes) return mnSeatCodes;
    try {
      const res = await fetch(MN_PRODUCTION_PATH);
      if (!res.ok) return new Set();
      const seats = await res.json();
      const codes = new Set();
      (Array.isArray(seats) ? seats : []).forEach((seat) => {
        const bv = seat?.spr2023?.blocVotes;
        if (!bv) return;
        const mn = (bv.PN || 0) + (bv.BN || 0);
        const ph = bv.PH || 0;
        if (mn <= ph) return;
        const m = String(seat.id || "").match(/N0*(\d+)/i);
        if (m) codes.add(`N${String(parseInt(m[1], 10)).padStart(2, "0")}`);
      });
      mnSeatCodes = codes;
      return codes;
    } catch {
      return new Set();
    }
  }

  const MN_OPS_GROUPS = [
    { id: "A", label: "JANGAN GAGAL", kategori: "defend", cls: "mn-a", effort: "Tinggi" },
    { id: "B", label: "PUSH MENANG", kategori: "winnable", cls: "mn-b", effort: "Tinggi", mnOnly: true },
    { id: "C", label: "JUJUR & TIPIS", kategori: "tough", cls: "mn-c", effort: "Sederhana" },
    { id: "D", label: "MAINTAIN MN", kategori: "not_priority", cls: "mn-d", effort: "Rendah" },
  ];

  function groupAction(group, dailyOps) {
    const meta = dailyOps?.kumpulan?.[group.kategori]?.meta;
    return meta?.hari_ini || {
      defend: "Jentera penuh — jangan kurang staf",
      winnable: "Digital + ground — kejar undi",
      tough: "Kempen minimum konsisten",
      not_priority: "WhatsApp + monitor sahaja",
    }[group.kategori];
  }

  function sortSeats(seats) {
    return [...(seats || [])].sort((a, b) => {
      const probDiff = (b.ml_competitive_prob || 0) - (a.ml_competitive_prob || 0);
      if (probDiff !== 0) return probDiff;
      return String(a.code || "").localeCompare(String(b.code || ""));
    });
  }

  function renderSeatRow(seat, compact, opts = {}) {
    const prob = seatMlPct(seat);
    const probVal = seat.ml_competitive_prob ?? (seat.peluang_ml_pct != null ? seat.peluang_ml_pct / 100 : 0);
    const cls = probVal >= 0.55 ? "high" : probVal >= 0.4 ? "mid" : "low";
    const mnTag = opts.inMn ? `<span class="ml-mn-tag">MN</span>` : "";
    const pasPct = seat.model_pas_pct ?? seat.pasWinProb ?? "—";
    if (compact) {
      return `<span class="ml-tier-chip ${cls}" title="${seat.name || ""} · Peluang ML ${prob} · Model PAS ${pasPct}%">
        ${mnTag}<strong>${seat.code}</strong> ${seat.name || ""}
      </span>`;
    }
    return `<tr class="ml-tier-row ${cls}">
      <td class="ml-tier-code">${seat.code}${mnTag}</td>
      <td>${seat.name || "—"}</td>
      <td class="ml-tier-num ml-col-peluang"><strong>${prob}</strong></td>
      <td class="ml-tier-num">${pasPct}%</td>
      <td class="ml-tier-num" title="Majoriti PRN 2023">${seat.majoriti_2023 ?? seat.majority != null ? Number(seat.majoriti_2023 ?? seat.majority).toLocaleString("en-MY") : "—"}</td>
    </tr>`;
  }

  function annotateMn(seats, mnCodes) {
    return (seats || []).map((seat) => ({
      ...seat,
      inMnTarget: mnCodes.has(seat.code),
    }));
  }

  function seatsFromDailyOps(dailyOps, kategori) {
    return dailyOps?.kumpulan?.[kategori]?.seats || [];
  }

  function renderMnKpis(seats, mnCodes, dailyOps) {
    const kpi = dailyOps?.kpi;
    const mnSeats = seats.filter((s) => s.inMnTarget);
    const pushSeats = mnSeats.filter((s) => s.kategoriPas !== "not_priority");
    const maintainSeats = mnSeats.filter((s) => s.kategoriPas === "not_priority");
    const outsideSeats = seats.filter((s) => !s.inMnTarget);
    const stretchSeats = outsideSeats.filter((s) => s.kategoriPas === "winnable");

    return {
      mnSeats,
      pushSeats,
      maintainSeats,
      outsideSeats,
      stretchSeats,
      html: `
        <div class="ml-mn-banner">
          <div class="ml-mn-banner-title">Sasaran MN #3 · ${kpi?.sasaran_mn ?? mnSeats.length} kerusi · majoriti ${MN_MAJORITY}</div>
          <div class="ml-mn-banner-sub">MN tentukan <em>mana</em> bermain · ML tentukan <em>berapa kuat</em> push</div>
        </div>
        <div class="ml-kpi-row">
          <div class="ml-kpi ml-kpi-mn"><span class="ml-kpi-label">Sasaran MN</span><strong>${kpi?.sasaran_mn ?? mnSeats.length}</strong></div>
          <div class="ml-kpi ml-kpi-push"><span class="ml-kpi-label">Push kuat (A+B+C)</span><strong>${kpi?.push_abc ?? pushSeats.length}</strong></div>
          <div class="ml-kpi ml-kpi-maintain"><span class="ml-kpi-label">Maintain (D)</span><strong>${kpi?.maintain_d ?? maintainSeats.length}</strong></div>
          <div class="ml-kpi"><span class="ml-kpi-label">Luar MN</span><strong>${outsideSeats.length}</strong></div>
          <div class="ml-kpi"><span class="ml-kpi-label">Stretch</span><strong>${stretchSeats.length}</strong></div>
        </div>`,
    };
  }

  function renderKeputusanSync(dailyOps) {
    if (!dailyOps?.keputusan) return "";
    const k = dailyOps.keputusan;
    const tindakan = (dailyOps.tindakan_72jam || []).slice(0, 7);
    return `
      <div class="ml-sync-banner">
        <div class="ml-sync-head">
          <span class="ml-sync-badge">SAMA DENGAN COMMAND CENTER</span>
          <strong>${k.headline || "Keputusan hari ini"}</strong>
        </div>
        <p class="ml-sync-text">${k.ringkasan || ""}</p>
        <ul class="ml-sync-actions">
          ${tindakan.map((a) => `
            <li>
              <span class="ml-action-urgency ${a.kesukaran === "segera" ? "immediate" : "monitor"}">${a.label || "Tindakan"}</span>
              <span>${a.teks || ""}</span>
            </li>`).join("")}
        </ul>
      </div>`;
  }

  function renderMnFocusMatrix(seats, mnCodes, dailyOps) {
    if (!seats?.length && !dailyOps) return "";
    const annotated = annotateMn(seats, mnCodes);
    const mnSeats = sortSeats(annotated.filter((s) => s.inMnTarget));
    const outsideSeats = sortSeats(annotated.filter((s) => !s.inMnTarget));
    const stretchSeats = outsideSeats.filter((s) => s.kategoriPas === "winnable");

    const tableHead = `<thead><tr>
      <th>DUN</th><th>Nama</th>
      <th title="Gabungan SVM+RF+DT — tinggi = lebih kompetitif">Peluang ML</th>
      <th title="Anggaran menang PAS (peraturan HQ)">Model PAS</th>
      <th>Maj'23</th>
    </tr></thead>`;

    const mnBlocks = MN_OPS_GROUPS.map((group) => {
      let rows = dailyOps
        ? seatsFromDailyOps(dailyOps, group.kategori)
        : mnSeats.filter((s) => s.kategoriPas === group.kategori);
      if (!dailyOps && group.mnOnly && group.kategori === "winnable") {
        rows = rows.filter((s) => s.inMnTarget);
      }
      const compact = group.kategori === "not_priority";
      const body = compact
        ? `<div class="ml-tier-chip-grid">${rows.map((s) => renderSeatRow(s, true, { inMn: true })).join("")}</div>`
        : `<table class="ml-tier-table">${tableHead}
            <tbody>${rows.map((s) => renderSeatRow(s, false, { inMn: true })).join("")}</tbody>
          </table>`;
      return `<section class="ml-tier-block mn-group ${group.cls}">
        <div class="ml-tier-head">
          <div>
            <span class="ml-tier-pill">Kumpulan ${group.id}</span>
            <strong class="ml-tier-title">${group.label}</strong>
            <span class="ml-tier-count">${rows.length} DUN · ${group.effort}</span>
          </div>
          <span class="ml-tier-action">Hari ini: ${groupAction(group, dailyOps)}</span>
        </div>
        ${body || "<p class='ml-muted'>Tiada DUN dalam kumpulan ini.</p>"}
      </section>`;
    }).join("");

    const stretchBlock = stretchSeats.length
      ? `<section class="ml-tier-block mn-stretch">
          <div class="ml-tier-head">
            <div><strong class="ml-tier-title">STRETCH</strong><span class="ml-tier-count">${stretchSeats.length} DUN · luar bloc MN</span></div>
            <span class="ml-tier-action">Opsyen jika ada lebihan tenaga</span>
          </div>
          <table class="ml-tier-table">${tableHead}
            <tbody>${stretchSeats.map((s) => renderSeatRow(s, false)).join("")}</tbody>
          </table>
        </section>`
      : "";

    const outsideBlock = `<section class="ml-tier-block mn-outside">
      <div class="ml-tier-head">
        <div><strong class="ml-tier-title">LUAR SASARAN MN</strong><span class="ml-tier-count">${outsideSeats.length - stretchSeats.length} DUN</span></div>
        <span class="ml-tier-action">Monitor minimum — jangan habiskan tenaga</span>
      </div>
      <div class="ml-tier-chip-grid">${outsideSeats.filter((s) => s.kategoriPas !== "winnable").map((s) => renderSeatRow(s, true)).join("")}</div>
    </section>`;

    return `
      <p class="ml-legend">📌 <strong>Peluang ML</strong> = kekuatan push (gabungan 3 model) · <strong>Model PAS</strong> = anggaran menang ikut peraturan HQ · Klik Command Center untuk tindakan 72 jam penuh.</p>
      <div class="ml-tier-matrix">${mnBlocks}${stretchBlock}${outsideBlock}</div>`;
  }

  function renderActions(dailyOps, mlActions) {
    const items = dailyOps?.ml_actions_top5?.length
      ? dailyOps.ml_actions_top5
      : (mlActions || []).map((a) => ({
          title_bm: a.title,
          detail_bm: a.detail,
          urgency: a.urgency,
        }));
    if (!items?.length) {
      return "<p class='ml-muted'>Tiada tindakan ML — jalankan build_n9_daily_ops_sync.py</p>";
    }
    return `<ul class="ml-action-list">${items.map((a) => `
      <li>
        <span class="ml-action-urgency ${a.urgency || "immediate"}">SEGERA</span>
        <div>
          <strong>${a.title_bm || a.title || ""}</strong>
          <div class="ml-action-detail">${a.detail_bm || a.detail || ""}</div>
        </div>
      </li>`).join("")}</ul>`;
  }

  function renderJobCrawlImpact(jobImpact) {
    if (!jobImpact) return "";
    const j1 = jobImpact.job1_poll || {};
    const j2 = jobImpact.job2_monarki || {};
    const risks = jobImpact.seat_risk || [];
    const fmtN = (n) => Number(n || 0).toLocaleString("en-MY");
    const kwLines = (j2.per_keyword || [])
      .slice(0, 5)
      .map((k) => `${k.id} ${fmtN(k.records)} rek · ${fmtN(k.engagement)} eng · ${Number(k.neg_pct || 0).toFixed(0)}% neg`)
      .join(" · ");
    const riskLines = risks
      .map((r) => `<li><strong>${r.code}</strong> (${r.risk}) — ${r.action}</li>`)
      .join("");
    return `
      <div class="ml-section ml-job-impact">
        <h5>Kesan Crawl · Isyarat ML</h5>
        <p class="desc" style="margin:0 0 8px">${jobImpact.summary || ""}</p>
        <div class="ml-kpi-row">
          <div class="ml-kpi"><span class="ml-kpi-label">Job1 Post</span><strong>1</strong></div>
          <div class="ml-kpi"><span class="ml-kpi-label">Komen</span><strong>${fmtN(j1.comments)}</strong></div>
          <div class="ml-kpi"><span class="ml-kpi-label">Engagement</span><strong>${fmtN(j1.engagement)}</strong></div>
          <div class="ml-kpi"><span class="ml-kpi-label">Sokong MN</span><strong>${j1.sokong_mn_pct || "—"}%</strong></div>
        </div>
        <p class="desc" style="font-size:11px;margin:6px 0">${kwLines || "Job 2 keyword data —"}</p>
        <ul class="ml-action-list">${riskLines}</ul>
      </div>`;
  }

  async function renderPanel(containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;

    el.innerHTML = `<p class="desc">Memuatkan analitik ML (mudah faham · selari Keputusan Hari Ini)…</p>`;

    const [data, dailyOps] = await Promise.all([fetchMlData(), fetchDailyOps()]);
    if (!data && !dailyOps) {
      el.innerHTML = `<p class="desc">Data ML tidak tersedia. Jalankan <code>python3 scripts/build_n9_ml_predictions.py</code></p>`;
      return;
    }

    const mnCodes = await fetchMnSeatCodes(dailyOps);
    const seats = data?.seat_predictions || [];
    const mnKpis = renderMnKpis(annotateMn(seats, mnCodes), mnCodes, dailyOps);
    const tier = data?.analytics_tier || "prescriptive";

    el.innerHTML = `
      <div class="ml-panel-head">
        <h4>ML Analytics · InsightPulse</h4>
        ${tierBadge(tier)}
      </div>
      <p class="desc">Panduan operasi <strong>20 kerusi MN</strong> — majoriti ${MN_MAJORITY}. Nombor sama dengan panel <em>Keputusan & Tindakan Hari Ini</em>.</p>
      ${renderKeputusanSync(dailyOps)}
      ${mnKpis.html}
      <div class="ml-section">
        <h5>Prestasi Model (ujian silang)</h5>
        ${renderModels(data?.predictive, dailyOps)}
      </div>
      <div class="ml-section">
        <h5>Sasaran MN — 20 Kerusi · Kumpulan Operasi</h5>
        ${renderMnFocusMatrix(seats, mnCodes, dailyOps)}
      </div>
      <div class="ml-section">
        <h5>Tindakan Segera · Top 5 ML (sama Keputusan)</h5>
        ${renderActions(dailyOps, data?.prescriptive_actions)}
      </div>
      ${renderJobCrawlImpact(data?.job_crawl_impact)}
      <p class="ml-footnote">${dailyOps?.kpi?.formula || `Formula: 80% tenaga → ${mnKpis.pushSeats.length} push · 20% → ${mnKpis.maintainSeats.length} maintain`} · ${dailyOps?.generated_at || (data?.generated_at ? new Date(data.generated_at).toLocaleString("en-MY") : "")}</p>
    `;
  }

  function init() {
    renderPanel("cmdMlAnalyticsPanel");
  }

  window.MLAnalytics = {
    fetchMlData,
    fetchDailyOps,
    renderPanel,
    init,
  };

  document.addEventListener("DOMContentLoaded", () => {
    setTimeout(init, 400);
  });
})();
