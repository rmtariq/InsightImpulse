/**
 * InsightPulse PRN N9 V2 — action layer
 * Converts dashboard signals into clear, owner-based actions.
 */
(function () {
  let actionData = null;
  let liveMode = false;
  const actionStatus = {};
  const filters = { priority: "all", category: "all", status: "all" };

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

  function actionMatches(a) {
    return (
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
    const evidence = (a.evidence || []).slice(0, compact ? 2 : 4);
    const steps = (a.recommended_steps || []).slice(0, compact ? 2 : 4);
    return `
      <div class="action-card ${esc(a.priority)}" data-action-id="${esc(a.id)}">
        <div class="action-top">
          <span class="chip ${PRIORITY_CHIP[a.priority] || "chip-amber"}">${esc(pri)}</span>
          <span class="chip chip-purple">${esc(cat)}</span>
          <span class="chip">${esc(status)}</span>
          <span class="action-id">${esc(a.id)}</span>
        </div>
        <div class="action-title">${esc(a.title)}</div>
        <div class="action-body">
          <strong>Apa perlu dibuat:</strong> ${esc(a.reason)}<br>
          <strong>DUN:</strong> ${esc(a.dun)} ${esc(a.seat)} · <strong>Owner:</strong> ${esc(a.owner)} · <strong>Due:</strong> ${esc(a.due)}
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
    const top = currentActions().sort(prioritySort).slice(0, 3);
    const p1 = currentActions().filter((a) => a.priority === "p1" && a.status !== "siap").length;
    const p2 = currentActions().filter((a) => a.priority === "p2" && a.status !== "siap").length;
    el.innerHTML = `
      <div class="cmd-action-head">
        <div>
          <h4>Top Actions Today</h4>
          <p class="desc" style="margin:2px 0 0">Apa yang perlu dibuat sekarang · ${p1} P1 · ${p2} P2 · ${liveMode ? "LIVE API" : "fail statik"}</p>
        </div>
        <button type="button" class="btn-sm btn-green" id="cmdOpenActionCenter">Buka Action Center</button>
      </div>
      <div class="cmd-actions-grid">
        ${top.map((a) => actionCard(a, true)).join("")}
      </div>`;
    $("cmdOpenActionCenter")?.addEventListener("click", () => typeof showPage === "function" && showPage("action"));
    bindActionButtons(el);
  }

  function renderActionStats(actions) {
    const active = actions.filter((a) => a.status !== "siap");
    const p1 = active.filter((a) => a.priority === "p1").length;
    const dueToday = active.filter((a) => /hari ini|malam ini|18:00|12:00/i.test(a.due || "")).length;
    const done = actions.filter((a) => a.status === "siap").length;
    return `
      <div class="kpi-grid action-kpis">
        <div class="kpi"><div class="kpi-label">Tindakan Aktif</div><div class="kpi-value amber">${active.length}</div><div class="kpi-sub">belum siap</div></div>
        <div class="kpi"><div class="kpi-label">P1 Segera</div><div class="kpi-value ${p1 ? "red" : "green"}">${p1}</div><div class="kpi-sub">perlu owner hari ini</div></div>
        <div class="kpi"><div class="kpi-label">Due Hari Ini</div><div class="kpi-value">${dueToday}</div><div class="kpi-sub">sebelum war room malam</div></div>
        <div class="kpi"><div class="kpi-label">Siap</div><div class="kpi-value green">${done}</div><div class="kpi-sub">direkod sesi ini</div></div>
      </div>`;
  }

  function renderActionCenter() {
    const root = $("actionCenterRoot");
    if (!root || !actionData) return;
    const actions = currentActions();
    const rows = actions.filter(actionMatches).sort(prioritySort);
    root.innerHTML = `
      ${renderActionStats(actions)}
      <div class="sync-line" style="margin-bottom:10px">● Action Center ${liveMode ? "LIVE" : "offline fallback"} · status ${liveMode ? "disimpan ke backend" : "sementara di browser"}</div>
      <div class="panel action-toolbar">
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
        <div class="action-queue">${rows.map((a) => actionCard(a)).join("") || `<div class="panel"><p class="desc">Tiada tindakan untuk filter ini.</p></div>`}</div>
        <div class="panel action-side">
          <h4>Apa yang perlu dibuat sekarang</h4>
          <ol>
            <li>Pastikan setiap P1 ada owner dan due time.</li>
            <li>Kemaskini status selepas tindakan dibuat.</li>
            <li>Masukkan impak tindakan dalam briefing harian.</li>
          </ol>
          <h4 style="margin-top:14px">Program Ops</h4>
          ${(actionData.programOps || []).map((p) => `
            <div class="post-card">
              <strong>${esc(p.title)}</strong><br>
              ${esc(p.dun)} ${esc(p.seat)} · ${esc(p.owner)} · ${esc(p.date)}<br>
              <span style="color:var(--muted)">${esc(p.target)}</span>
            </div>`).join("")}
        </div>
      </div>`;
    root.querySelectorAll("[data-action-filter]").forEach((sel) => {
      sel.addEventListener("change", () => {
        filters[sel.dataset.actionFilter] = sel.value;
        renderActionCenter();
      });
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
              <strong>Sentimen:</strong> ${esc(r.sentiment_summary)}<br>
              <strong>Emosi:</strong> ${esc(r.emotion_summary)}<br>
              <strong>Engagement:</strong> ${Number(r.engagement || 0).toLocaleString("en-MY")} · confidence ${(Number(r.confidence || 0) * 100).toFixed(0)}%
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

  function renderRapidResponseV2() {
    const root = $("rapidAlerts");
    if (!root || !actionData) return false;
    const rows = currentActions().filter((a) => a.category === "rapid_response" || a.priority === "p1").sort(prioritySort);
    root.innerHTML = rows.map((a) => actionCard(a)).join("") || `<div class="panel"><p class="desc">Tiada rapid response aktif.</p></div>`;
    bindActionButtons(root);
    return true;
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

  window.initActionCenter = async function initActionCenter() {
    actionData = null;
    await loadActionData();
    renderCommandActions();
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
  window.renderRapidResponseV2 = renderRapidResponseV2;
  window.renderDailyBriefingV2 = renderDailyBriefingV2;
})();
