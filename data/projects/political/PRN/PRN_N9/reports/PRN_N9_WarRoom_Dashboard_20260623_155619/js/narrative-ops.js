/**
 * Command Center — narrative update reminder + daily checklist (Modul #6)
 * Paparan ikut negeri aktif (N9 / Johor / Melaka) — tiada campur negeri lain.
 */
(function () {
  const STORAGE_KEY = "prn_narrative_checklist_v1";

  function $(id) {
    return document.getElementById(id);
  }

  function todayKey() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  function loadChecklist() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const all = raw ? JSON.parse(raw) : {};
      if (!all[todayKey()]) {
        all[todayKey()] = { pagi: false, petang: false, semakP1: false, refresh: false };
      }
      return all[todayKey()];
    } catch {
      return { pagi: false, petang: false, semakP1: false, refresh: false };
    }
  }

  function saveChecklist(patch) {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const all = raw ? JSON.parse(raw) : {};
      const day = todayKey();
      all[day] = { ...loadChecklist(), ...patch };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
    } catch (_) {}
  }

  function parseGeneratedAt(iso) {
    if (!iso) return null;
    const s = String(iso).trim();
    const m = s.match(/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})/);
    if (!m) return null;
    return new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]);
  }

  function hoursAgoLabel(iso) {
    const dt = parseGeneratedAt(iso);
    if (!dt) return { text: "belum dikemas kini", level: "crit", hours: null };
    const hours = (Date.now() - dt.getTime()) / 3600000;
    if (hours < 1) return { text: "baru sahaja", level: "ok", hours };
    if (hours < 24) return { text: `${Math.round(hours)} jam lalu`, level: hours <= 12 ? "ok" : "warn", hours };
    const days = Math.round(hours / 24);
    return { text: `${days} hari lalu`, level: "crit", hours };
  }

  function stateKey() {
    return typeof state !== "undefined" ? state : "N9";
  }

  function activeStateSnapshot() {
    const key = stateKey();
    if (typeof DATA === "undefined" || !DATA[key]) return null;
    const s = DATA[key];
    const p1 = (s.actions || []).filter((a) => a.p === "p1").length;
    return {
      key,
      label: s.label || key,
      chinese: s.chinese?.posts ?? 0,
      indian: s.indian?.posts ?? 0,
      p1,
    };
  }

  function kitFootnote(key) {
    if (key === "N9") return "Kit operasi: PRN_N9 · Modul #6 naratif Cina &amp; India";
    if (key === "Johor") return "Kit operasi: PRN_Johor · Modul #6 naratif Cina &amp; India";
    if (key === "Melaka") return "Kit operasi: PRN_Melaka · Modul #6 naratif Cina &amp; India";
    return "Kit operasi: Modul #6 naratif Cina &amp; India";
  }

  function narrativeCounts() {
    const s = typeof DATA !== "undefined" ? DATA[stateKey()] : null;
    if (!s) return null;
    const p1c = (s.actions || []).filter((a) => a.p === "p1" && a.comm === "chinese").length;
    const p1i = (s.actions || []).filter((a) => a.p === "p1" && a.comm === "indian").length;
    return {
      chinese: s.chinese?.posts ?? 0,
      indian: s.indian?.posts ?? 0,
      p1Chinese: p1c,
      p1Indian: p1i,
      topChinese: s.chinese?.topIssue ?? "—",
      topIndian: s.indian?.topIssue ?? "—",
    };
  }

  function freshnessClass(level) {
    if (level === "ok") return "narr-ops-fresh-ok";
    if (level === "warn") return "narr-ops-fresh-warn";
    return "narr-ops-fresh-crit";
  }

  function renderPanel(meta) {
    const panel = $("narrOpsPanel");
    if (!panel) return;

    const fresh = hoursAgoLabel(meta?.generated_at);
    const chk = loadChecklist();
    const mode = meta?.mode === "live" ? "live" : "demo";
    const doneCount = Object.values(chk).filter(Boolean).length;

    const snap = activeStateSnapshot();
    const active = stateKey();
    const stateLabel = snap?.label || active;
    const totalP1 = snap?.p1 ?? 0;

    panel.innerHTML = `
      <div class="narr-ops-head">
        <div>
          <h4>Naratif Cina &amp; India — ${stateLabel}</h4>
          <p class="desc" style="margin:0">Modul #6 · data ${mode} · <strong style="color:var(--green)">✓ crawl berjaya</strong> · checklist manual ${doneCount}/4</p>
        </div>
        <div class="narr-ops-actions">
          <button type="button" class="btn-sm btn-primary" id="narrOpsCopyCmd" title="Salin command update">Salin command</button>
        </div>
      </div>
      <div class="narr-ops-banner ${totalP1 ? "narr-ops-banner-warn" : "narr-ops-banner-ok"}">
        ${totalP1
          ? `⚡ <strong>${totalP1} isu P1</strong> (${stateLabel}) — semak senarai isu di bawah &amp; laksana tindakan. Tick checklist ≠ selesai operasi.`
          : `✓ Data live dimuatkan. "Baru sahaja" = kemas kini berjaya, bukan tiada data.`}
      </div>
      <div class="narr-ops-grid">
        <div class="narr-ops-stat ${freshnessClass(fresh.level)}">
          <div class="lbl">Last narrative update</div>
          <div class="val">${fresh.text}</div>
          <div class="sub">${meta?.generated_at ? "✓ " + meta.generated_at + " MYT · data live" : "Jalankan: ./scripts/update_narrative.sh pagi"}</div>
        </div>
        ${snap ? `
        <div class="narr-ops-stat narr-ops-stat-active">
          <div class="lbl">${snap.key} · Cina + India</div>
          <div class="val">${snap.chinese} + ${snap.indian} post</div>
          <div class="sub">P1: <strong>${snap.p1}</strong> · ${snap.label} · <em>negeri aktif</em></div>
        </div>` : `
        <div class="narr-ops-stat">
          <div class="lbl">${active} · Cina + India</div>
          <div class="val">—</div>
          <div class="sub">Tiada data naratif untuk negeri ini</div>
        </div>`}
      </div>
      <p class="narr-ops-note">Checklist di bawah = <strong>tick manual</strong> (ingatan operasi harian). Tandakan sendiri bila siap — tidak auto dari crawl.</p>
      <div class="narr-ops-checklist" id="narrOpsChecklist">
        ${checklistRow("pagi", "Crawl + publish pagi", chk.pagi, "./scripts/update_narrative.sh pagi")}
        ${checklistRow("petang", "Crawl + publish petang", chk.petang, "./scripts/update_narrative.sh petang")}
        ${checklistRow("semakP1", "Semak isu P1 Modul #6", chk.semakP1, "")}
        ${checklistRow("refresh", "Hard refresh dashboard (Cmd+Shift+R)", chk.refresh, "")}
      </div>
      <p class="narr-ops-foot">${kitFootnote(active)}</p>`;

    panel.querySelectorAll("[data-chk]").forEach((el) => {
      el.addEventListener("change", () => {
        saveChecklist({ [el.dataset.chk]: el.checked });
        renderPanel(meta);
      });
    });

    $("narrOpsCopyCmd")?.addEventListener("click", async () => {
      const cmd = fresh.hours != null && fresh.hours <= 12
        ? "./scripts/update_narrative.sh"
        : "./scripts/update_narrative.sh pagi";
      try {
        await navigator.clipboard.writeText(`cd /Users/rmtariq/Documents/InsightPulse\n${cmd}`);
        if (typeof showToast === "function") showToast("✓ Command disalin");
      } catch {
        if (typeof showToast === "function") showToast(cmd);
      }
    });
  }

  function checklistRow(key, label, checked, hint) {
    return `<label class="narr-ops-chk">
      <input type="checkbox" data-chk="${key}" ${checked ? "checked" : ""}/>
      <span>${label}</span>
      ${hint ? `<code class="narr-ops-hint">${hint}</code>` : ""}
    </label>`;
  }

  window.refreshNarrativeOpsChecklist = function refreshNarrativeOpsChecklist(meta) {
    const m = meta ?? (typeof narrativeMeta !== "undefined" ? narrativeMeta : null);
    renderPanel(m);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => renderPanel(null));
  } else {
    renderPanel(null);
  }
})();
