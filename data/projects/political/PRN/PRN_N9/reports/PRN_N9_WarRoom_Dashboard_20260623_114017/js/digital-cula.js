/**
 * InsightPulse — Digital Culaan (N9, Johor, Melaka)
 * Data entry module; results shown in Command Center.
 * Requires prn_digital_cula_server.py (not plain http.server)
 */
(function () {
  const API = "";
  const JENIS_LABEL = {
    door_to_door: "Door-to-door",
    program: "Program / ceramah",
    follow_up: "Follow-up",
    lain: "Lain-lain",
  };

  let culaHub = null;
  let culaDuns = [];
  let culaTab = "upload";
  let culaSocmedPlan = null;
  let culaSocmedSeeds = [];

  const STATUS_BADGE = {
    planned: ["cula-badge-planned", "Dirancang"],
    posted: ["cula-badge-posted", "Dihantar"],
    url_registered: ["cula-badge-url", "URL OK"],
    crawl_queued: ["cula-badge-crawl", "Crawl…"],
    crawled: ["cula-badge-url", "Siap"],
    failed: ["cula-badge-due", "Gagal"],
  };

  function updateCulaRoleCards(tab) {
    document.querySelectorAll(".cula-role-card").forEach((el) => {
      el.classList.toggle("active", el.dataset.tab === tab && tab !== "socmed");
    });
    $("culaHowtoField")?.classList.toggle("hidden", tab !== "lapangan");
  }

  function setCulaTab(tab) {
    culaTab = tab;
    ["upload", "lapangan", "socmed"].forEach((t) => {
      $("culaTab-" + t)?.classList.toggle("active", t === tab);
      $("culaPanel-" + t)?.classList.toggle("hidden", t !== tab);
    });
    updateCulaRoleCards(tab);
    if (tab === "upload") loadCulaHub();
    if (tab === "socmed") initCulaSocmedPanel();
  }

  function fmt(n) {
    if (n == null || n === "") return "—";
    return Number(n).toLocaleString("en-MY");
  }

  function todayISO() {
    const p = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Kuala_Lumpur",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).formatToParts(new Date());
    const y = p.find((x) => x.type === "year").value;
    const m = p.find((x) => x.type === "month").value;
    const d = p.find((x) => x.type === "day").value;
    return `${y}-${m}-${d}`;
  }

  async function api(path, opts) {
    const res = await fetch(API + path, {
      headers: { "Content-Type": "application/json", ...(opts && opts.headers) },
      ...opts,
    });
    const text = await res.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch { data = { error: text.slice(0, 120) || res.statusText }; }
    if (!res.ok) throw new Error(data.errors?.join(" ") || data.error || res.statusText);
    return data;
  }

  async function checkApiHealth() {
    const banner = $("culaApiBanner");
    const btn = document.querySelector(".btn-submit-cula");
    if (!banner) return false;
    try {
      await api("/api/health");
      banner.className = "cula-api-banner ok";
      banner.textContent = "✓ Sistem culaan digital aktif — masukkan data & lihat kemaskini di Command Center.";
      if (btn) btn.disabled = false;
      return true;
    } catch {
      banner.className = "cula-api-banner err";
      banner.innerHTML =
        "⚠ Server API tidak aktif — borang <strong>tidak boleh disimpan</strong>. " +
        "Jalankan: <code>bash scripts/start_prn_warroom_prototype.sh</code> " +
        "(bukan python -m http.server sahaja).";
      if (btn) btn.disabled = true;
      return false;
    }
  }

  async function loadCulaDuns() {
    const data = await api(`/api/cula/duns?state=${encodeURIComponent(state)}`);
    culaDuns = data.duns || [];
    const sel = $("culaDunSelect");
    if (sel) {
      sel.innerHTML = culaDuns
        .map((d) => `<option value="${d.kod_dun}">${d.kod_dun} — ${d.name}</option>`)
        .join("");
    }
    const socmedSel = $("culaSocmedDun");
    if (socmedSel) {
      socmedSel.innerHTML = culaDuns
        .map((d) => `<option value="${d.kod_dun}">${d.kod_dun} — ${d.name}</option>`)
        .join("");
    }
  }

  async function loadSocmedPlan() {
    const kod = $("culaSocmedDun")?.value || "N01";
    const trek = $("culaSocmedTrek")?.value || "lokaliti";
    const box = $("culaSocmedSuggestions");
    const meta = $("culaSocmedMeta");
    if (!box) return;
    try {
      culaSocmedPlan = await api(
        `/api/cula-socmed/plan?state=${encodeURIComponent(state)}&kod_dun=${encodeURIComponent(kod)}&trek=${encodeURIComponent(trek)}`
      );
      if (!culaSocmedPlan.ok) throw new Error(culaSocmedPlan.error || "Plan gagal");
      box.innerHTML = (culaSocmedPlan.suggested_posts || [])
        .map(
          (text, i) => `
          <div class="cula-seed-suggest">
            <div class="cula-seed-suggest-row">
              <span>${text.replace(/</g, "&lt;")}</span>
              <button type="button" class="btn-sm btn-green cula-copy-seed" data-idx="${i}">Salin</button>
            </div>
          </div>`
        )
        .join("");
      box.querySelectorAll(".cula-copy-seed").forEach((btn) => {
        btn.addEventListener("click", () => {
          const idx = Number(btn.dataset.idx);
          const t = culaSocmedPlan.suggested_posts[idx];
          $("culaSocmedPostText").value = t;
          navigator.clipboard?.writeText(t);
          if (typeof showToast === "function") showToast("✓ Teks disalin");
        });
      });
      if (meta) {
        const def = culaSocmedPlan.default_wait_hours || 24;
        meta.innerHTML =
          `<strong>Landmark:</strong> ${culaSocmedPlan.landmarks || "—"} · ` +
          `<strong>Isu:</strong> ${culaSocmedPlan.local_issues || "—"} · ` +
          `<strong>Platform:</strong> ${(culaSocmedPlan.platforms || []).join(", ")} · ` +
          `<strong>Tunggu lalai:</strong> ${def} jam (boleh ubah di dropdown)`;
      }
    } catch (e) {
      box.innerHTML = `<p style="color:#f87171;font-size:12px">${e.message || "Gagal muat cadangan"}</p>`;
      if (state !== "N9" && meta) meta.textContent = "Socmed seed — N9 sahaja setakat ini.";
    }
  }

  function statusBadge(st) {
    const [cls, label] = STATUS_BADGE[st] || STATUS_BADGE.planned;
    return `<span class="cula-badge ${cls}">${label}</span>`;
  }

  async function loadSocmedSeeds() {
    try {
      const data = await api(`/api/cula-socmed/seeds?state=${encodeURIComponent(state)}`);
      culaSocmedSeeds = data.seeds || [];
    } catch {
      culaSocmedSeeds = [];
    }
    renderSocmedTable();
    renderSocmedKpis();
    populateSeedPick();
  }

  async function loadSocmedHub() {
    try {
      const data = await api(`/api/cula-socmed/hub?state=${encodeURIComponent(state)}`);
      const h = data.hub || {};
      $("culaSocmedTotal") && ($("culaSocmedTotal").textContent = h.seeds_total ?? 0);
      $("culaSocmedDue") && ($("culaSocmedDue").textContent = h.due_for_crawl ?? 0);
      const posted = (h.recent || []).filter((s) => s.status !== "planned").length;
      const urls = (h.recent || []).filter((s) => s.post_url).length;
      $("culaSocmedPosted") && ($("culaSocmedPosted").textContent = posted);
      $("culaSocmedUrl") && ($("culaSocmedUrl").textContent = urls);
    } catch {
      /* fallback counts from seeds */
    }
  }

  function renderSocmedKpis() {
    const total = culaSocmedSeeds.length;
    const posted = culaSocmedSeeds.filter((s) => ["posted", "url_registered", "crawl_queued", "crawled"].includes(s.status)).length;
    const urls = culaSocmedSeeds.filter((s) => s.post_url).length;
    const due = culaSocmedSeeds.filter(
      (s) => s.status === "url_registered" && s.post_url && isSeedDue(s)
    ).length;
    $("culaSocmedTotal") && ($("culaSocmedTotal").textContent = total);
    $("culaSocmedPosted") && ($("culaSocmedPosted").textContent = posted);
    $("culaSocmedUrl") && ($("culaSocmedUrl").textContent = urls);
    $("culaSocmedDue") && ($("culaSocmedDue").textContent = due);
  }

  function fmtDueCell(s) {
    const due = s.crawl_due_at || "—";
    const wait = s.wait_label || (s.wait_hours != null ? `${s.wait_hours}j` : "");
    if (s.status === "posted" && !s.post_url) {
      return `${due}<br><span style="font-size:10px;color:var(--muted)">tunggu ${wait || "—"}</span>`;
    }
    return `${due}${wait ? `<br><span style="font-size:10px;color:var(--muted)">${wait}</span>` : ""}`;
  }

  function isSeedDue(s) {
    if (!s.crawl_due_at) return true;
    const t = new Date(String(s.crawl_due_at).replace(" ", "T") + "+08:00");
    return !isNaN(t.getTime()) && Date.now() >= t.getTime();
  }

  function populateSeedPick() {
    const sel = $("culaSocmedSeedPick");
    if (!sel) return;
    const waiting = culaSocmedSeeds.filter((s) => s.status === "posted");
    sel.innerHTML =
      waiting.length === 0
        ? `<option value="">— Tiada seed menunggu URL —</option>`
        : waiting
            .map(
              (s) =>
                `<option value="${s.id}">${s.kod_dun} ${s.dun_name} · ${s.trek_label || s.trek} · ${s.posted_at || ""}</option>`
            )
            .join("");
  }

  function renderSocmedTable() {
    const tbody = $("culaSocmedTableBody");
    if (!tbody) return;
    if (!culaSocmedSeeds.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="color:var(--muted)">Belum ada seed — mulakan dari borang atas.</td></tr>`;
      return;
    }
    tbody.innerHTML = culaSocmedSeeds
      .slice(0, 50)
      .map((s) => {
        const snippet = (s.post_text_actual || s.post_text_suggested || "").slice(0, 80);
        const url = s.post_url ? `<a href="${s.post_url}" target="_blank" rel="noopener" style="color:#93c5fd;font-size:11px">URL</a>` : "—";
        return `<tr>
          <td><strong>${s.kod_dun}</strong> ${s.dun_name || ""}</td>
          <td>${s.trek_label || s.trek}</td>
          <td>${statusBadge(s.status)}</td>
          <td style="max-width:220px">${snippet}${snippet.length >= 80 ? "…" : ""} ${url !== "—" ? " · " + url : ""}</td>
          <td>${fmtDueCell(s)}</td>
        </tr>`;
      })
      .join("");
  }

  async function markSocmedPosted() {
    const msg = $("culaSocmedPlanMsg");
    msg.textContent = "";
    msg.className = "cula-form-msg";
    const pelapor = ($("culaSocmedPelapor")?.value || "").trim();
    if (pelapor.length < 2) {
      msg.textContent = "Isi ID Pelapor.";
      msg.classList.add("err");
      return;
    }
    const postText = ($("culaSocmedPostText")?.value || "").trim();
    if (!postText) {
      msg.textContent = "Isi atau salin teks post.";
      msg.classList.add("err");
      return;
    }
    try {
      const data = await api("/api/cula-socmed/seed", {
        method: "POST",
        body: JSON.stringify({
          state,
          kod_dun: $("culaSocmedDun").value,
          trek: $("culaSocmedTrek").value,
          platform: $("culaSocmedPlatform").value,
          group_name: $("culaSocmedGroup").value.trim(),
          pelapor_id: pelapor,
          post_text: postText,
          wait_hours: Number($("culaSocmedWait")?.value || 24),
          mark_posted: true,
          posted_at: todayISO(),
        }),
      });
      const wl = data.seed?.wait_label || "24 jam";
      const due = data.seed?.crawl_due_at || "";
      msg.textContent = `✓ Post ditandakan DIHANTAR — crawl disyorkan selepas ${wl}${due ? ` (${due})` : ""}.`;
      msg.classList.add("ok");
      if (typeof showToast === "function") showToast(`✓ Dihantar — tunggu ${wl}`);
      await loadSocmedSeeds();
      await loadSocmedHub();
    } catch (e) {
      msg.textContent = e.message || "Gagal";
      msg.classList.add("err");
    }
  }

  async function registerSocmedUrl() {
    const msg = $("culaSocmedUrlMsg");
    msg.textContent = "";
    msg.className = "cula-form-msg";
    const seedId = $("culaSocmedSeedPick")?.value;
    const url = ($("culaSocmedUrl")?.value || "").trim();
    if (!seedId) {
      msg.textContent = "Pilih seed yang sudah dihantar.";
      msg.classList.add("err");
      return;
    }
    if (!url.startsWith("http")) {
      msg.textContent = "Paste URL post yang sah.";
      msg.classList.add("err");
      return;
    }
    try {
      await api("/api/cula-socmed/seed", {
        method: "PATCH",
        body: JSON.stringify({ state, id: seedId, post_url: url }),
      });
      msg.textContent = "✓ URL didaftar — sedia untuk crawl.";
      msg.classList.add("ok");
      $("culaSocmedUrl").value = "";
      if (typeof showToast === "function") showToast("✓ URL didaftar");
      await loadSocmedSeeds();
    } catch (e) {
      msg.textContent = e.message || "Gagal daftar URL";
      msg.classList.add("err");
    }
  }

  async function crawlSocmedDue() {
    const msg = $("culaSocmedUrlMsg");
    msg.textContent = "Menghantar crawl ke InsightPulse…";
    msg.className = "cula-form-msg";
    try {
      const data = await api("/api/cula-socmed/crawl", {
        method: "POST",
        body: JSON.stringify({ state, all_ready: true }),
      });
      if (!data.ok) throw new Error(data.error || "Crawl gagal");
      msg.textContent = `✓ ${data.count || 0} task dihantar — monitor backend.log (:8001)`;
      msg.classList.add("ok");
      if (typeof showToast === "function") showToast("✓ Crawl dihantar");
      await loadSocmedSeeds();
    } catch (e) {
      msg.textContent = e.message || "Backend :8001 mungkin offline";
      msg.classList.add("err");
    }
  }

  async function initCulaSocmedPanel() {
    if (state !== "N9") {
      $("culaSocmedSuggestions") &&
        ($("culaSocmedSuggestions").innerHTML =
          '<p style="color:var(--muted);font-size:12px">Socmed seed planner — N9 dahulu. Johor/Melaka Sprint 3.</p>');
      return;
    }
    await loadSocmedPlan();
    await loadSocmedSeeds();
    await loadSocmedHub();
  }

  async function loadCulaHub() {
    try {
      const data = await api(`/api/cula/hub?state=${encodeURIComponent(state)}`);
      culaHub = data.hub;
    } catch {
      const fallback = await fetch(`data/cula_hub_${state}.json`).then((r) => r.json()).catch(() => null);
      culaHub = fallback;
    }
    renderCommandIntel(culaHub);
  }

  async function renderCommandIntel(hub) {
    if (typeof refreshCommandIntel === "function") {
      await refreshCommandIntel(hub);
    }
  }

  window.renderCommandCulaFeed = renderCommandIntel;

  async function submitCulaForm(ev) {
    ev.preventDefault();
    const msg = $("culaFormMsg");
    const btn = document.querySelector("#culaForm .btn-submit-cula");
    msg.textContent = "";
    msg.className = "cula-form-msg";

    const ok = await checkApiHealth();
    if (!ok) {
      msg.textContent = "Server API offline — lihat banner merah di atas.";
      msg.classList.add("err");
      if (typeof showToast === "function") showToast("Server API offline");
      return;
    }

    if (btn) { btn.disabled = true; btn.textContent = "Menghantar…"; }
    const payload = {
      state,
      tarikh_lawatan: $("culaTarikh").value,
      kod_dun: $("culaDunSelect").value,
      pdm: $("culaPdm").value.trim(),
      pelapor_id: $("culaPelaporId").value.trim(),
      pelapor_nama: $("culaPelaporNama").value.trim(),
      jenis_aktiviti: $("culaJenis").value,
      rumah_dilawati: $("culaRumah").value,
      cula_baharu: $("culaBaharu").value,
      cula_bulan: $("culaBulan").value || 0,
      cula_condong: $("culaCondong").value || 0,
      cula_atas_pagar: $("culaPagar").value || 0,
      cula_dacing: $("culaDacing").value || 0,
      catatan: $("culaCatatan").value.trim(),
      auto_verify: true,
      reviewer: $("culaPelaporId").value.trim(),
    };
    try {
      const data = await api("/api/cula/submit", { method: "POST", body: JSON.stringify(payload) });
      msg.textContent = data.message || "✓ Data diterima — lihat kemaskini di Command Center.";
      msg.classList.add("ok");
      if (typeof showToast === "function") showToast("✓ Cula dikemaskini — Command Center");
      $("culaForm").reset();
      $("culaTarikh").value = todayISO();
      $("culaRumah").value = "0";
      $("culaBaharu").value = "0";
      await loadCulaHub();
    } catch (e) {
      msg.textContent = e.message || "Gagal hantar.";
      msg.classList.add("err");
      if (typeof showToast === "function") showToast("Gagal: " + (e.message || "hantar"));
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "Hantar & Kemaskini Dashboard"; }
    }
  }

  async function uploadBatch() {
    const msg = $("culaUploadMsg");
    const log = $("culaUploadLog");
    const btn = $("culaUploadBtn");
    msg.textContent = "";
    msg.className = "cula-form-msg";
    log?.classList.add("hidden");

    const uploader = ($("culaUploaderId")?.value || "").trim();
    if (uploader.length < 2) {
      msg.textContent = "Isi ID Uploader (HQ) dahulu.";
      msg.classList.add("err");
      return;
    }
    const ok = await checkApiHealth();
    if (!ok) {
      msg.textContent = "Server API offline.";
      msg.classList.add("err");
      return;
    }

    const file = $("culaCsvFile")?.files?.[0];
    const paste = ($("culaWhatsappPaste")?.value || "").trim();
    let body;
    if (file) {
      const csv = await file.text();
      body = { state, uploader, mode: "csv", csv };
    } else if (paste) {
      body = {
        state,
        uploader,
        mode: "whatsapp",
        text: paste,
        tarikh_lawatan: $("culaBatchTarikh")?.value || todayISO(),
      };
    } else {
      msg.textContent = "Pilih fail CSV atau tampal teks WhatsApp.";
      msg.classList.add("err");
      return;
    }

    if (btn) { btn.disabled = true; btn.textContent = "Memproses…"; }
    try {
      const data = await api("/api/cula/upload", { method: "POST", body: JSON.stringify(body) });
      msg.textContent = `✓ ${data.imported} rekod diterima — lihat kemaskini di Command Center.`;
      msg.classList.add("ok");
      if (data.errors?.length) {
        log.textContent = data.errors.join("\n");
        log.classList.remove("hidden");
      }
      if (typeof showToast === "function") showToast(`✓ ${data.imported} rekod — Command Center dikemaskini`);
      $("culaCsvFile").value = "";
      $("culaWhatsappPaste").value = "";
      await loadCulaHub();
    } catch (e) {
      msg.textContent = e.message || "Upload gagal.";
      msg.classList.add("err");
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "Upload & Kemaskini Dashboard"; }
    }
  }

  window.initDigitalCula = async function initDigitalCula() {
    if (window._culaBound) {
      await refreshDigitalCula();
      return;
    }
    window._culaBound = true;
    $("culaTarikh") && ($("culaTarikh").value = todayISO());
    $("culaStateLabel") && ($("culaStateLabel").textContent = DATA[state]?.label || state);
    const share = $("culaShareLink");
    if (share) share.textContent = location.origin + location.pathname + "?module=cula&state=" + state;
    const stTpl = $("culaCsvStateTpl");
    if (stTpl) { stTpl.href = "/api/cula/template-" + state + ".csv"; stTpl.textContent = "⬇ CSV Contoh " + state; }
    $("culaCopyLink")?.addEventListener("click", () => {
      const link = share?.textContent || location.href;
      navigator.clipboard?.writeText(link).then(() => {
        if (typeof showToast === "function") showToast("✓ Link disalin — hantar ke WhatsApp lapangan");
      });
    });
    $("culaForm")?.addEventListener("submit", submitCulaForm);
    $("culaTab-upload")?.addEventListener("click", () => setCulaTab("upload"));
    $("culaTab-lapangan")?.addEventListener("click", () => setCulaTab("lapangan"));
    $("culaTab-socmed")?.addEventListener("click", () => setCulaTab("socmed"));
    $("culaSocmedDun")?.addEventListener("change", loadSocmedPlan);
    $("culaSocmedTrek")?.addEventListener("change", loadSocmedPlan);
    $("culaSocmedMarkPosted")?.addEventListener("click", markSocmedPosted);
    $("culaSocmedRegisterUrl")?.addEventListener("click", registerSocmedUrl);
    $("culaSocmedCrawlDue")?.addEventListener("click", crawlSocmedDue);
    document.querySelectorAll(".cula-role-card").forEach((el) => {
      el.addEventListener("click", () => setCulaTab(el.dataset.tab));
    });
    const culaParams = new URLSearchParams(location.search);
    const culaStartTab =
      culaParams.get("tab") ||
      (culaParams.get("module") === "cula" && !culaParams.get("tab") ? "lapangan" : "upload");
    setCulaTab(["upload", "lapangan", "socmed"].includes(culaStartTab) ? culaStartTab : "upload");
    $("culaUploadBtn")?.addEventListener("click", uploadBatch);
    $("culaBatchTarikh") && ($("culaBatchTarikh").value = todayISO());
    $("cmdCulaInputBtn")?.addEventListener("click", () => {
      if (typeof showPage === "function") showPage("cula");
    });
    await checkApiHealth();
    try {
      await loadCulaDuns();
      await loadCulaHub();
    } catch (e) {
      console.warn("Cula init:", e);
    }
  };

  window.refreshDigitalCula = async function refreshDigitalCula() {
    $("culaStateLabel") && ($("culaStateLabel").textContent = DATA[state]?.label || state);
    const share = $("culaShareLink");
    if (share) share.textContent = location.origin + location.pathname + "?module=cula&state=" + state;
    const stTpl = $("culaCsvStateTpl");
    if (stTpl) { stTpl.href = "/api/cula/template-" + state + ".csv"; stTpl.textContent = "⬇ CSV Contoh " + state; }
    await checkApiHealth();
    try {
      await loadCulaDuns();
      await loadCulaHub();
      if (culaTab === "socmed") await initCulaSocmedPanel();
    } catch (e) {
      console.warn("Cula refresh:", e);
    }
  };
})();
