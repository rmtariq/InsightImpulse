/**
 * InsightPulse PRN N9 V2 — action layer
 * Converts dashboard signals into clear, owner-based actions.
 */
(function () {
  let actionData = null;
  let liveMode = false;
  const actionStatus = {};
  const filters = { priority: "all", category: "all", status: "all", scope: "mn20", mlGroup: "all" };

  const MN_PRODUCTION_PATH = "data/warroom_dun_N9_production.json";
  const ML_DATA_PATH = "data/n9_ml_predictions.json";
  const MN_MAJORITY = 19;

  let mnSeatCodes = null;
  let mnSeatMeta = {};
  let mlSeatMap = null;
  let selectedSeat = null;

  const ML_GROUPS = {
    defend: { id: "A", label: "Jangan Gagal", chip: "chip-red" },
    winnable: { id: "B", label: "Push Menang", chip: "chip-amber" },
    tough: { id: "C", label: "Jujur & Tipis", chip: "chip-purple" },
    not_priority: { id: "D", label: "Maintain MN", chip: "chip-green" },
  };

  const PRIORITY_LABEL = { p1: "P1 Segera", p2: "P2 Perhatian", p3: "P3 Pantau" };
  const PRIORITY_CHIP = { p1: "chip-red", p2: "chip-amber", p3: "chip-green" };
  const CATEGORY_LABEL = {
    lapangan: "Lapangan",
    digital: "Digital",
    rapid_response: "Rapid Response",
    program: "Program",
    influencer: "Influencer",
    koordinasi: "Koordinasi",
    gotv: "GOTV",
  };
  const STATUS_LABEL = {
    baru: "Baru",
    sedang_dibuat: "Sedang dibuat",
    siap: "Siap",
    ditangguh: "Ditangguh",
  };

  function $(id) {
    return document.getElementById(id);
  }

  function esc(v) {
    return String(v ?? "").replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[ch]));
  }

  function currentState() {
    return typeof state !== "undefined" ? state : "N9";
  }

  async function loadActionData() {
    if (actionData) return actionData;
    try {
      const api = await fetch(`/api/action-center?state=${encodeURIComponent(currentState())}&_=${Date.now()}`);
      if (api.ok) {
        const payload = await api.json();
        if (payload.ok && payload.data) {
          actionData = payload.data;
          liveMode = true;
          return actionData;
        }
      }
      const res = await fetch("data/n9_actions_v2.json?_=" + Date.now());
      if (!res.ok) throw new Error("HTTP " + res.status);
      actionData = await res.json();
      liveMode = false;
    } catch (e) {
      actionData = fallbackActionData();
      liveMode = false;
      console.warn("Action Center fallback:", e);
    }
    return actionData;
  }

  function fallbackActionData() {
    return {
      meta: { state: "N9", generated: new Date().toISOString(), version: "2.0" },
      actions: [
        {
          id: "ACT-N9-FB1",
          title: "Semak data lapangan kerusi sasaran",
          category: "lapangan",
          priority: "p2",
          status: "baru",
          owner: "HQ Operasi",
          due: "Hari ini",
          dun: "N9",
          seat: "Negeri Sembilan",
          locality: "Semua DUN",
          reason: "Data action V2 belum dimuatkan; gunakan fallback operasi.",
          evidence: ["Fallback UI aktif"],
          recommended_steps: ["Semak fail data/n9_actions_v2.json", "Refresh dashboard"],
          impact_metric: "Data action kembali aktif",
        },
      ],
      pulseDigital: [],
      programOps: [],
      dailyBriefing: { headline: "Data action belum dimuatkan.", what_changed: [], next_24h: [], risk: "Semak fail data." },
    };
  }

  function currentActions() {
    return (actionData?.actions || []).map((a) => ({ ...a, status: actionStatus[a.id] || a.status || "baru" }));
  }

  async function updateActionStatus(id, status) {
    actionStatus[id] = status;
    if (actionData?.actions) {
      actionData.actions = actionData.actions.map((a) => a.id === id ? { ...a, status } : a);
    }
    if (!liveMode) return false;
    try {
      const res = await fetch("/api/action-center/action", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: currentState(), id, status, updated_by: "war-room" }),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const payload = await res.json();
      if (!payload.ok) throw new Error(payload.error || "Gagal simpan status");
      return true;
    } catch (e) {
      console.warn("Action status API:", e);
      return false;
    }
  }

  function normalizeDun(code) {
    const m = String(code || "").match(/N0*(\d+)/i);
    return m ? `N${String(parseInt(m[1], 10)).padStart(2, "0")}` : String(code || "").toUpperCase();
  }

  async function loadMnMlContext() {
    if (mnSeatCodes && mlSeatMap) {
      return { mnSeatCodes, mlSeatMap, mnSeatMeta };
    }
    mnSeatCodes = new Set();
    mnSeatMeta = {};
    mlSeatMap = {};

    try {
      const prodRes = await fetch(MN_PRODUCTION_PATH);
      if (prodRes.ok) {
        const seats = await prodRes.json();
        (Array.isArray(seats) ? seats : []).forEach((seat) => {
          const bv = seat?.spr2023?.blocVotes;
          if (!bv) return;
          if ((bv.PN || 0) + (bv.BN || 0) <= (bv.PH || 0)) return;
          const code = normalizeDun(seat.id);
          if (code.startsWith("N")) {
            mnSeatCodes.add(code);
            mnSeatMeta[code] = { name: seat.name || code, code };
          }
        });
      }
    } catch { /* optional */ }

    try {
      const mlRes = await fetch(ML_DATA_PATH);
      if (mlRes.ok) {
        const ml = await mlRes.json();
        (ml.seat_predictions || []).forEach((seat) => {
          mlSeatMap[normalizeDun(seat.code)] = seat;
        });
      }
    } catch { /* optional */ }

    return { mnSeatCodes, mlSeatMap, mnSeatMeta };
  }

  function sortedMnCodes() {
    return [...(mnSeatCodes || [])].sort(
      (a, b) => parseInt(a.slice(1), 10) - parseInt(b.slice(1), 10)
    );
  }

  function seatActionSummary(code, actions) {
    const dun = normalizeDun(code);
    const rows = actions.filter((a) => normalizeDun(a.dun) === dun);
    const active = rows.filter((a) => a.status !== "siap");
    return {
      total: rows.length,
      active: active.length,
      p1: active.filter((a) => a.priority === "p1").length,
      p2: active.filter((a) => a.priority === "p2").length,
      done: rows.filter((a) => a.status === "siap").length,
    };
  }

  function seatContext(code) {
    const dun = normalizeDun(code);
    const ml = mlSeatMap?.[dun];
    const inMn = mnSeatCodes?.has(dun) || false;
    const kategori = ml?.kategoriPas || "not_priority";
    const group = inMn ? (ML_GROUPS[kategori] || ML_GROUPS.not_priority) : null;
    const isStretch = !inMn && kategori === "winnable";
    return { dun, inMn, kategori, group, isStretch, ml };
  }

  function actionMatches(a) {
    const ctx = seatContext(a.dun);
    const scopeOk = (
      filters.scope === "all" ||
      (filters.scope === "mn20" && ctx.inMn) ||
      (filters.scope === "mn_push" && ctx.inMn && ctx.kategori !== "not_priority") ||
      (filters.scope === "stretch" && ctx.isStretch)
    );
    const groupOk = (
      filters.mlGroup === "all" ||
      (ctx.group && ctx.group.id === filters.mlGroup)
    );
    const seatOk = !selectedSeat || normalizeDun(a.dun) === normalizeDun(selectedSeat);
    return (
      scopeOk &&
      groupOk &&
      seatOk &&
      (filters.priority === "all" || a.priority === filters.priority) &&
      (filters.category === "all" || a.category === filters.category) &&
      (filters.status === "all" || a.status === filters.status)
    );
  }

  function prioritySort(a, b) {
    const rank = { p1: 0, p2: 1, p3: 2 };
    return (rank[a.priority] ?? 9) - (rank[b.priority] ?? 9);
  }

  function actionCard(a, compact = false) {
    const pri = PRIORITY_LABEL[a.priority] || a.priority || "P";
    const cat = CATEGORY_LABEL[a.category] || a.category || "Tindakan";
    const status = STATUS_LABEL[a.status] || a.status || "Baru";
    const ctx = seatContext(a.dun);
    const mlChip = ctx.group
      ? `<span class="chip ${ctx.group.chip}">MN · ${esc(ctx.group.label)}</span>`
      : ctx.isStretch
        ? `<span class="chip chip-purple">Stretch</span>`
        : `<span class="chip">Luar MN</span>`;
    const culaChip = (a.source === "cula_auto" || String(a.id || "").includes("-CULA-"))
      ? `<span class="chip chip-green">Cula</span>`
      : "";
    const evidence = (a.evidence || []).slice(0, compact ? 2 : 4);
    const steps = (a.recommended_steps || []).slice(0, compact ? 2 : 4);
    const mlHint = ctx.ml?.ml_competitive_prob != null
      ? ` · ML ${Math.round(ctx.ml.ml_competitive_prob * 100)}%`
      : "";
    return `
      <div class="action-card ${esc(a.priority)}" data-action-id="${esc(a.id)}">
        <div class="action-top">
          <span class="chip ${PRIORITY_CHIP[a.priority] || "chip-amber"}">${esc(pri)}</span>
          <span class="chip chip-purple">${esc(cat)}</span>
          <span class="chip">${esc(status)}</span>
          ${mlChip}
          ${culaChip}
          <span class="action-id">${esc(a.id)}</span>
        </div>
        <div class="action-title">${esc(a.title)}</div>
        <div class="action-body">
          <strong>Apa perlu dibuat:</strong> ${esc(a.reason)}<br>
          <strong>DUN:</strong> ${esc(a.dun)} ${esc(a.seat)}${mlHint} · <strong>Owner:</strong> ${esc(a.owner)} · <strong>Due:</strong> ${esc(a.due)}
        </div>
        ${evidence.length ? `<div class="action-evidence"><strong>Bukti:</strong><ul>${evidence.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : ""}
        ${steps.length ? `<div class="action-steps"><strong>Langkah:</strong><ol>${steps.map((x) => `<li>${esc(x)}</li>`).join("")}</ol></div>` : ""}
        <div class="action-footer">
          <button class="btn btn-primary btn-sm" data-action-status="${esc(a.id)}" data-status="sedang_dibuat">Mula</button>
          <button class="btn btn-ghost btn-sm" data-action-status="${esc(a.id)}" data-status="siap">Siap</button>
          <button class="btn btn-ghost btn-sm" data-action-dun="${esc(a.dun)}">Lihat DUN</button>
          <button class="btn btn-ghost btn-sm" data-content-action="${esc(a.id)}">Jana kandungan</button>
          <span style="font-size:10px;color:var(--muted)">Sasaran: ${esc(a.impact_metric || "rekod impak selepas tindakan")}</span>
        </div>
      </div>`;
  }

  function bindActionButtons(root = document) {
    root.querySelectorAll("[data-action-status]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const persisted = await updateActionStatus(btn.dataset.actionStatus, btn.dataset.status);
        if (typeof showToast === "function") {
          const label = btn.dataset.status === "siap" ? "Tindakan siap" : "Tindakan dimulakan";
          showToast(persisted ? `✓ ${label} · disimpan live` : `⚠ ${label} · sementara sahaja`);
        }
        renderActionCenter();
        renderCommandActions();
      });
    });
    root.querySelectorAll("[data-action-dun]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const code = btn.dataset.actionDun;
        if (code && code !== "N9" && typeof openDunSeat === "function") {
          openDunSeat(code);
        } else if (typeof showPage === "function") {
          showPage("dun");
        }
      });
    });
    root.querySelectorAll("[data-content-action]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = currentActions().find((a) => String(a.id) === btn.dataset.contentAction);
        if (item && typeof window.openContentStudio === "function") {
          window.openContentStudio(item);
        } else if (typeof showToast === "function") {
          showToast("Content Studio belum sedia.");
        }
      });
    });
  }

  function renderCommandActions() {
    const el = $("cmdTopActions");
    if (!el || !actionData) return;
    const mnPush = (dun) => {
      const ctx = seatContext(dun);
      return ctx.inMn && ctx.kategori !== "not_priority";
    };
    const top = currentActions()
      .filter((a) => mnPush(a.dun))
      .sort(prioritySort)
      .slice(0, 3);
    const scoped = currentActions().filter((a) => seatContext(a.dun).inMn);
    const p1 = scoped.filter((a) => a.priority === "p1" && a.status !== "siap").length;
    const p2 = scoped.filter((a) => a.priority === "p2" && a.status !== "siap").length;
    el.innerHTML = `
      <div class="cmd-action-head">
        <div>
          <h4>Top Actions Today · MN Push</h4>
          <p class="desc" style="margin:2px 0 0">Fokus 11 kerusi A+B+C · ${p1} P1 · ${p2} P2 · ${liveMode ? "LIVE API" : "fail statik"}</p>
        </div>
        <button type="button" class="btn-sm btn-green" id="cmdOpenActionCenter">Buka Action Center</button>
      </div>
      <div class="cmd-actions-grid">
        ${top.map((a) => actionCard(a, true)).join("") || `<p class="desc">Tiada tindakan MN push aktif.</p>`}
      </div>`;
    $("cmdOpenActionCenter")?.addEventListener("click", () => typeof showPage === "function" && showPage("action"));
    bindActionButtons(el);
  }

  function renderMn20Board(actions) {
    const codes = sortedMnCodes();
    if (!codes.length) {
      return `<div class="panel"><p class="desc">Data 20 kerusi MN belum dimuatkan.</p></div>`;
    }

    const mnActions = actions.filter((a) => seatContext(a.dun).inMn);
    const p1Seats = codes.filter((c) => seatActionSummary(c, mnActions).p1 > 0).length;
    const activeSeats = codes.filter((c) => seatActionSummary(c, mnActions).active > 0).length;

    const tiles = codes.map((code) => {
      const meta = mnSeatMeta[code] || { name: code };
      const ctx = seatContext(code);
      const sum = seatActionSummary(code, mnActions);
      const group = ctx.group;
      const groupCls = group ? `mn-${group.id.toLowerCase()}` : "mn-d";

      let urgencyCls = "ac-seat-ok";
      let statusLine = group?.id === "D" ? "Maintain" : "Pantau";
      if (sum.p1 > 0) {
        urgencyCls = "ac-seat-p1";
        statusLine = `${sum.p1} P1 segera`;
      } else if (sum.active > 0) {
        urgencyCls = "ac-seat-active";
        statusLine = `${sum.active} tindakan aktif`;
      } else if (sum.done > 0) {
        urgencyCls = "ac-seat-done";
        statusLine = "Siap";
      }

      const isSelected = selectedSeat === code ? " selected" : "";
      return `
        <button type="button" class="ac-seat-tile ${groupCls} ${urgencyCls}${isSelected}" data-ac-seat="${esc(code)}">
          <div class="ac-seat-code">${esc(code)}</div>
          <div class="ac-seat-name">${esc(meta.name)}</div>
          <div class="ac-seat-group">${group ? esc(`${group.id} · ${group.label}`) : "—"}</div>
          <div class="ac-seat-status">${esc(statusLine)}</div>
        </button>`;
    }).join("");

    return `
      <div class="ac-seat-board-wrap">
        <div class="ac-seat-board-head">
          <div>
            <div class="ml-mn-banner-title">20 Kerusi MN · majoriti ${MN_MAJORITY}</div>
            <div class="ml-mn-banner-sub">Klik kerusi → faham situasi → ambil tindakan · ${p1Seats} kerusi P1 · ${activeSeats} ada tindakan aktif</div>
          </div>
          <div class="ac-seat-legend">
            <span class="ac-legend-p1">● P1</span>
            <span class="ac-legend-active">● Aktif</span>
            <span class="ac-legend-ok">● Pantau</span>
          </div>
        </div>
        <div class="ac-seat-board">${tiles}</div>
        ${selectedSeat ? `<button type="button" class="btn btn-ghost btn-sm ac-seat-clear" id="acClearSeat">← Semua 20 kerusi</button>` : ""}
      </div>`;
  }

  function renderStatewideActions(actions) {
    if (selectedSeat) return "";
    const rows = actions
      .filter((a) => normalizeDun(a.dun) === "N9")
      .filter((a) =>
        (filters.priority === "all" || a.priority === filters.priority) &&
        (filters.category === "all" || a.category === filters.category) &&
        (filters.status === "all" || a.status === filters.status)
      )
      .sort(prioritySort);
    if (!rows.length) return "";
    return `
      <div class="ac-statewide">
        <h4 class="ac-seat-detail-head">Tindakan Negeri (semua DUN)</h4>
        <div class="action-queue">${rows.map((a) => actionCard(a)).join("")}</div>
      </div>`;
  }

  function renderActionCenter() {
    const root = $("actionCenterRoot");
    if (!root || !actionData) return;
    filters.scope = "mn20";
    const actions = currentActions();
    const mnActions = actions.filter((a) => seatContext(a.dun).inMn || normalizeDun(a.dun) === "N9");
    const rows = mnActions.filter(actionMatches).sort(prioritySort);
    const seatRows = rows.filter((a) => seatContext(a.dun).inMn);
    const detailTitle = selectedSeat
      ? `${selectedSeat} ${mnSeatMeta[selectedSeat]?.name || ""} — Tindakan`
      : "Tindakan kerusi MN (ikut filter)";
    root.innerHTML = `
      ${renderMn20Board(actions)}
      <div class="sync-line" style="margin-bottom:10px">● Action Center ${liveMode ? "LIVE" : "offline fallback"} · 20 kerusi MN sahaja · status ${liveMode ? "disimpan ke backend" : "sementara di browser"}</div>
      <div class="panel action-toolbar">
        <div>
          <label>Kumpulan ML</label>
          <select data-action-filter="mlGroup">
            ${option("all", "Semua kumpulan", filters.mlGroup)}
            ${option("A", "A — Jangan Gagal", filters.mlGroup)}
            ${option("B", "B — Push Menang", filters.mlGroup)}
            ${option("C", "C — Jujur & Tipis", filters.mlGroup)}
            ${option("D", "D — Maintain MN", filters.mlGroup)}
          </select>
        </div>
        <div>
          <label>Priority</label>
          <select data-action-filter="priority">
            ${option("all", "Semua", filters.priority)}
            ${option("p1", "P1 Segera", filters.priority)}
            ${option("p2", "P2 Perhatian", filters.priority)}
            ${option("p3", "P3 Pantau", filters.priority)}
          </select>
        </div>
        <div>
          <label>Kategori</label>
          <select data-action-filter="category">
            ${option("all", "Semua", filters.category)}
            ${Object.entries(CATEGORY_LABEL).map(([k, v]) => option(k, v, filters.category)).join("")}
          </select>
        </div>
        <div>
          <label>Status</label>
          <select data-action-filter="status">
            ${option("all", "Semua", filters.status)}
            ${Object.entries(STATUS_LABEL).map(([k, v]) => option(k, v, filters.status)).join("")}
          </select>
        </div>
      </div>
      <div class="action-layout">
        <div>
          <h4 class="ac-seat-detail-head">${esc(detailTitle)}</h4>
          <div class="action-queue">${seatRows.map((a) => actionCard(a)).join("") || `<div class="panel"><p class="desc">${selectedSeat ? "Tiada tindakan direkod untuk kerusi ini." : "Tiada tindakan aktif untuk filter ini — klik kerusi P1 di atas."}</p></div>`}</div>
          ${renderStatewideActions(actions)}
        </div>
        <div class="panel action-side">
          <h4>Cara guna</h4>
          <ol>
            <li><strong>Pilih kerusi</strong> dari papan 20 MN di atas.</li>
            <li><strong>Baca tindakan</strong> — owner, due, langkah.</li>
            <li><strong>Mula / Siap</strong> — rekod status sebelum war room malam.</li>
          </ol>
          <h4 style="margin-top:14px">Keutamaan ML</h4>
          <ol>
            <li><strong>A & B</strong> — selesaikan P1 hari ini.</li>
            <li><strong>C</strong> — P2 mingguan, jujur margin.</li>
            <li><strong>D</strong> — maintain, pantau sahaja.</li>
          </ol>
          <h4 style="margin-top:14px">Program Ops</h4>
          ${(actionData.programOps || []).filter((p) => !selectedSeat || normalizeDun(p.dun) === normalizeDun(selectedSeat)).filter((p) => mnSeatCodes?.has(normalizeDun(p.dun))).map((p) => `
            <div class="post-card">
              <strong>${esc(p.title)}</strong><br>
              ${esc(p.dun)} ${esc(p.seat)} · ${esc(p.owner)} · ${esc(p.date)}<br>
              <span style="color:var(--muted)">${esc(p.target)}</span>
            </div>`).join("") || `<p class="desc">Tiada program ops untuk kerusi ini.</p>`}
        </div>
      </div>`;
    root.querySelectorAll("[data-action-filter]").forEach((sel) => {
      sel.addEventListener("change", () => {
        filters[sel.dataset.actionFilter] = sel.value;
        renderActionCenter();
      });
    });
    root.querySelectorAll("[data-ac-seat]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const code = btn.dataset.acSeat;
        selectedSeat = selectedSeat === code ? null : code;
        renderActionCenter();
      });
    });
    $("acClearSeat")?.addEventListener("click", () => {
      selectedSeat = null;
      renderActionCenter();
    });
    bindActionButtons(root);
  }

  function option(value, label, selected) {
    return `<option value="${esc(value)}" ${value === selected ? "selected" : ""}>${esc(label)}</option>`;
  }

  function renderPulseDigital() {
    const root = $("pulseDigitalRoot");
    if (!root || !actionData) return;
    const rows = actionData.pulseDigital || [];
    root.innerHTML = `
      <div class="pulse-note">
        <strong>Pulse Digital / Signal Detection</strong> ialah bacaan reaksi online. Ini <strong>bukan culaan lapangan</strong> dan tidak menggantikan data rumah/PDM. Status: ${liveMode ? "LIVE API" : "offline fallback"}.
      </div>
      <div class="kpi-grid action-kpis">
        <div class="kpi"><div class="kpi-label">Signal Direkod</div><div class="kpi-value">${rows.length}</div><div class="kpi-sub">seed / URL / crawl</div></div>
        <div class="kpi"><div class="kpi-label">Engagement</div><div class="kpi-value">${rows.reduce((s, r) => s + Number(r.engagement || 0), 0).toLocaleString("en-MY")}</div><div class="kpi-sub">jumlah sample</div></div>
        <div class="kpi"><div class="kpi-label">Perlu Crawl</div><div class="kpi-value amber">${rows.filter((r) => /due|registered/i.test(r.status || "")).length}</div><div class="kpi-sub">susulan digital</div></div>
      </div>
      <div class="grid-2">
        ${rows.map((r) => `
          <div class="panel pulse-card">
            <div class="action-top">
              <span class="chip chip-purple">Pulse Digital</span>
              <span class="chip">${esc(r.platform)}</span>
              <span class="action-id">${esc(r.id)}</span>
            </div>
            <h4>${esc(r.dun)} ${esc(r.seat)} — ${esc(r.issue_cluster)}</h4>
            <p class="desc">${esc(r.stimulus)}</p>
            <div class="action-body">
              <strong>Post/Komen:</strong> ${Number(r.posts || 0)} post · ${Number(r.comments || r.records || 0).toLocaleString("en-MY")} komen/rekod<br>
              <strong>Sentimen:</strong> ${esc(r.sentiment_summary)}<br>
              <strong>Emosi:</strong> ${esc(r.emotion_summary)}<br>
              <strong>Engagement:</strong> ${Number(r.engagement || 0).toLocaleString("en-MY")}${r.likes ? ` · ${Number(r.likes).toLocaleString("en-MY")} likes` : ""} · confidence ${(Number(r.confidence || 0) * 100).toFixed(0)}%
            </div>
            <div class="action-steps"><strong>Tindakan digital:</strong><ol><li>${esc(r.recommended_action)}</li></ol></div>
            <div class="action-footer">
              <button class="btn btn-primary btn-sm" data-content-id="${esc(r.id)}">Jana kandungan (copy &amp; paste)</button>
            </div>
          </div>`).join("")}
      </div>`;
    bindContentButtons(root, rows);
  }

  function bindContentButtons(root, rows) {
    if (!root) return;
    root.querySelectorAll("[data-content-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = (rows || []).find((x) => String(x.id) === btn.dataset.contentId);
        if (item && typeof window.openContentStudio === "function") {
          window.openContentStudio(item);
        } else if (typeof showToast === "function") {
          showToast("Content Studio belum sedia.");
        }
      });
    });
  }

  function renderJobExercisesPanel() {
    const panel = $("cmdJobExercisesPanel");
    if (!panel || !actionData) return;
    const jobs = actionData.jobExercises || [];
    const metrics = actionData.jobCrawlMetrics || null;
    if (!jobs.length) {
      panel.classList.add("hidden");
      return;
    }
    panel.classList.remove("hidden");

    const fmtN = (n) => Number(n || 0).toLocaleString("en-MY");
    const j1 = metrics?.job1 || jobs.find((j) => j.id === "JOB-N9-01") || {};
    const j2k = metrics?.job2?.keywords || jobs.find((j) => j.id === "JOB-N9-02")?.keywords || [];
    const j2job = jobs.find((j) => j.id === "JOB-N9-02") || {};
    const bloc7 = metrics?.bloc7_effects?.effects || [];
    const adatEngK5 = metrics?.totals?.engagement_job2_k5 || j2job.stats?.engagement_k5 || 0;
    const adatEngOverlap = metrics?.totals?.engagement_job2_overlap || j2job.engagement_total_overlap || 0;

    const kwRows = j2k
      .map(
        (k) => `<tr>
          <td><strong>${esc(k.id)}</strong></td>
          <td>${esc(k.label)}</td>
          <td>${fmtN(k.posts || k.records)}</td>
          <td>${fmtN(k.records || k.posts)}</td>
          <td>${Number(k.neg_pct || 0).toFixed(1)}%</td>
          <td>${fmtN(k.engagement)}</td>
        </tr>`
      )
      .join("");

    const blocRows = bloc7
      .filter((e) => e.nudge_pp !== 0)
      .map(
        (e) => `<tr>
          <td>${esc(e.label)}</td>
          <td><strong>${esc(e.sign)}</strong></td>
          <td>${esc(e.reason)}</td>
        </tr>`
      )
      .join("");

    panel.innerHTML = `
      <h4>Job Exercises — InsightPulse Crawl (Jul 2026)</h4>
      <p class="desc" style="margin:-2px 0 8px">Sync penuh: post · komen · engagement · 7-bloc scenario · ML Analytics</p>
      <div class="cula-kpi-row" style="margin-bottom:12px">
        <div class="cula-kpi-mini"><div class="v">${fmtN(adatEngK5)}</div><div class="l">Engagement Isu Adat (K5)</div></div>
        <div class="cula-kpi-mini"><div class="v">${fmtN(adatEngOverlap)}</div><div class="l">Engagement K1–K5 (overlap)</div></div>
        <div class="cula-kpi-mini"><div class="v">${fmtN(j1.engagement)}</div><div class="l">Engagement Poll MN</div></div>
        <div class="cula-kpi-mini"><div class="v">${j1.sokong_mn_pct || j1.stats?.sokong_mn_pct || "—"}%</div><div class="l">Sokong MN (poll)</div></div>
      </div>
      <div class="job-exercises-grid">
        <div class="job-ex-card">
          <span class="job-ex-status">siap</span>
          <h5>JOB-N9-01 · Pengundi Malaysia Poll</h5>
          <div class="job-ex-stats">
            1 post · ${fmtN(j1.comments)} komen · ${fmtN(j1.likes)} likes · ${fmtN(j1.shares)} shares · ${fmtN(j1.engagement)} eng
          </div>
          <div class="job-ex-insight">~${j1.sokong_mn_pct || j1.stats?.sokong_mn_pct || "—"}% sokong MN · #3 MN +3pp</div>
        </div>
        <div class="job-ex-card">
          <span class="job-ex-status">siap</span>
          <h5>JOB-N9-02 · Monarki K1–K5</h5>
          <div class="job-ex-stats">
            ${j2k.length} keyword · K5 ${fmtN(metrics?.totals?.records_job2_k5 || "—")} rekod · ${fmtN(metrics?.totals?.engagement_job2_k5 || "—")} eng
          </div>
          <div class="job-ex-insight">K5 <strong>${fmtN(adatEngK5)}</strong> eng · overlap <strong>${fmtN(adatEngOverlap)}</strong> · elak politisasi istana</div>
        </div>
      </div>
      <details class="cula-poll-details" style="margin-top:10px" open>
        <summary>Job 2 — K1–K5 posts · rekod · engagement</summary>
        <table class="cula-poll-post-table">
          <thead><tr><th>KW</th><th>Frame</th><th>Posts</th><th>Rekod</th><th>Neg</th><th>Engagement</th></tr></thead>
          <tbody>${kwRows}</tbody>
        </table>
      </details>
      <details class="cula-poll-details" style="margin-top:8px">
        <summary>7 Senario — kesan Job 1+2 (nudge P majoriti)</summary>
        <table class="cula-poll-post-table">
          <thead><tr><th>Bloc</th><th>Nudge</th><th>Sebab</th></tr></thead>
          <tbody>${blocRows || "<tr><td colspan='3'>—</td></tr>"}</tbody>
        </table>
      </details>`;
  }

  function renderDailyBriefingV2() {
    const root = $("briefContent");
    if (!root || !actionData) return false;
    const b = actionData.dailyBriefing || {};
    const actions = currentActions().sort(prioritySort).slice(0, 3);
    root.innerHTML = `
      <h4 style="margin-bottom:12px;font-size:14px;color:#fff">Briefing Negeri Sembilan — ${new Date().toLocaleDateString("ms-MY")}</h4>
      <div class="post-card"><strong>Apa berlaku:</strong> ${esc(b.headline)}</div>
      <div class="post-card"><strong>Apa berubah hari ini:</strong><ul>${(b.what_changed || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>
      <div class="post-card"><strong>Tindakan 24 jam:</strong><ol>${(b.next_24h || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ol></div>
      <div class="post-card"><strong>Risiko:</strong> ${esc(b.risk)}</div>
      <div class="action-queue">${actions.map((a) => actionCard(a, true)).join("")}</div>`;
    bindActionButtons(root);
    return true;
  }

  window.openActionCenterWithFilters = function openActionCenterWithFilters(opts = {}) {
    selectedSeat = opts.seat || null;
    filters.scope = "mn20";
    filters.priority = opts.priority || "all";
    filters.category = opts.category || "all";
    filters.mlGroup = opts.mlGroup || "all";
    filters.status = opts.status || "all";
    if (typeof showPage === "function") {
      showPage("action");
      return;
    }
    renderActionCenter();
  };

  window.refreshActionCenterFromCula = async function refreshActionCenterFromCula() {
    actionData = null;
    mnSeatCodes = null;
    mlSeatMap = null;
    mnSeatMeta = {};
    await loadMnMlContext();
    await loadActionData();
    renderCommandActions();
    renderJobExercisesPanel();
    if (typeof page !== "undefined" && page === "action") {
      renderActionCenter();
    }
  };

  window.initActionCenter = async function initActionCenter() {
    actionData = null;
    await loadMnMlContext();
    await loadActionData();
    renderCommandActions();
    renderJobExercisesPanel();
    renderActionCenter();
    renderPulseDigital();
  };

  window.refreshCommandActions = renderCommandActions;
  window.renderActionCenter = async function renderActionCenterLive() {
    if (!actionData) await loadActionData();
    renderActionCenter();
  };
  window.renderPulseDigital = async function renderPulseDigitalLive() {
    if (!actionData) await loadActionData();
    renderPulseDigital();
  };
  window.renderDailyBriefingV2 = renderDailyBriefingV2;
})();
