/**
 * InsightPulse — Digital Culaan (N9, Johor, Melaka)
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
  const STATUS_LABEL = {
    pending: "Menunggu PDM",
    verified: "Disahkan",
    rejected: "Ditolak",
  };

  let culaHub = null;
  let culaDuns = [];
  let culaTab = "lapangan";

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
      banner.textContent = "✓ Sistem culaan digital aktif — isi borang & tekan Hantar (data masuk CSV automatik).";
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
    if (!sel) return;
    sel.innerHTML = culaDuns
      .map((d) => `<option value="${d.kod_dun}">${d.kod_dun} — ${d.name}</option>`)
      .join("");
  }

  async function loadCulaHub() {
    try {
      const data = await api(`/api/cula/hub?state=${encodeURIComponent(state)}`);
      culaHub = data.hub;
    } catch {
      const fallback = await fetch(`data/cula_hub_${state}.json`).then((r) => r.json()).catch(() => null);
      culaHub = fallback;
    }
    renderCulaSummary();
    renderCulaDunTable();
  }

  async function loadCulaPending() {
    const tbody = $("culaReviewBody");
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="8" style="color:var(--muted)">Memuatkan…</td></tr>`;
    try {
      const data = await api(`/api/cula/submissions?state=${encodeURIComponent(state)}&status=pending`);
      const rows = data.submissions || [];
      if (!rows.length) {
        tbody.innerHTML = `<tr><td colspan="8" style="color:var(--muted)">Tiada rekod menunggu semakan.</td></tr>`;
        return;
      }
      tbody.innerHTML = rows
        .map(
          (r) => `
        <tr data-id="${r.id}">
          <td>${r.tarikh_lawatan}<br><span style="font-size:10px;color:var(--muted)">${r.created_at || ""}</span></td>
          <td><strong>${r.kod_dun}</strong><br>${r.dun_name || ""}</td>
          <td>${r.pdm}</td>
          <td>${r.pelapor_id}<br><span style="font-size:10px">${r.pelapor_nama || ""}</span></td>
          <td>${JENIS_LABEL[r.jenis_aktiviti] || r.jenis_aktiviti}<br>${r.rumah_dilawati} rumah · <strong>+${r.cula_baharu}</strong> cula</td>
          <td style="font-size:10px">B:${r.cula_bulan} C:${r.cula_condong} P:${r.cula_atas_pagar} D:${r.cula_dacing}${r.flags ? `<br><span class="chip chip-amber">${r.flags}</span>` : ""}</td>
          <td style="max-width:120px;font-size:11px">${r.catatan || "—"}</td>
          <td class="cula-review-actions">
            <button type="button" class="btn-sm btn-green" data-action="verified" data-id="${r.id}">✓ Lulus</button>
            <button type="button" class="btn-sm btn-red" data-action="rejected" data-id="${r.id}">✕ Tolak</button>
          </td>
        </tr>`
        )
        .join("");
      tbody.querySelectorAll("[data-action]").forEach((btn) => {
        btn.onclick = () => reviewRow(btn.dataset.id, btn.dataset.action);
      });
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="8" style="color:var(--red)">API tidak tersedia — jalankan prn_digital_cula_server.py<br><span style="font-size:11px">${e.message}</span></td></tr>`;
    }
  }

  async function reviewRow(id, status) {
    const reviewer = ($("culaReviewerId")?.value || "").trim();
    if (reviewer.length < 2) {
      showToast("Isi ID Ketua PDM dahulu");
      $("culaReviewerId")?.focus();
      return;
    }
    const note = status === "rejected" ? prompt("Sebab tolak (optional):") || "" : "";
    try {
      await api("/api/cula/review", {
        method: "PATCH",
        body: JSON.stringify({ state, id, status, reviewer, reviewer_note: note }),
      });
      showToast(status === "verified" ? "✓ Disahkan" : "Rekod ditolak");
      await loadCulaPending();
      await loadCulaHub();
    } catch (e) {
      showToast(e.message);
    }
  }

  async function submitCulaForm(ev) {
    ev.preventDefault();
    const msg = $("culaFormMsg");
    const btn = document.querySelector(".btn-submit-cula");
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
    };
    const autoVerify = $("culaAutoVerify")?.checked;
    if (autoVerify) {
      payload.auto_verify = true;
      payload.reviewer = payload.pelapor_id;
    }
    try {
      const data = await api("/api/cula/submit", { method: "POST", body: JSON.stringify(payload) });
      msg.textContent = data.message || (autoVerify ? "Disahkan & dashboard dikemaskini." : "Dihantar — menunggu semakan PDM.");
      msg.classList.add("ok");
      if (typeof showToast === "function") showToast("✓ Laporan cula dihantar");
      $("culaForm").reset();
      $("culaTarikh").value = todayISO();
      $("culaRumah").value = "0";
      $("culaBaharu").value = "0";
      await loadCulaHub();
      if (culaTab === "semakan") await loadCulaPending();
    } catch (e) {
      msg.textContent = e.message || "Gagal hantar.";
      msg.classList.add("err");
      if (typeof showToast === "function") showToast("Gagal: " + (e.message || "hantar"));
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "Hantar — Menunggu Semakan PDM"; }
    }
  }

  function renderCulaSummary() {
    const el = $("culaSummaryGrid");
    if (!el || !culaHub) return;
    const s = culaHub.summary || {};
    el.innerHTML = `
      <div class="kpi"><div class="kpi-label">Verified 24j</div><div class="kpi-value green">+${fmt(s.verified_delta_24h)}</div><div class="kpi-sub">cula digital disahkan</div></div>
      <div class="kpi"><div class="kpi-label">Verified Total</div><div class="kpi-value">+${fmt(s.verified_delta_total)}</div><div class="kpi-sub">delta terkumpul</div></div>
      <div class="kpi"><div class="kpi-label">Menunggu PDM</div><div class="kpi-value amber">${fmt(s.pending_count)}</div><div class="kpi-sub">belum masuk peta</div></div>
      <div class="kpi"><div class="kpi-label">Rekod</div><div class="kpi-value">${fmt(s.submission_count)}</div><div class="kpi-sub">semua status</div></div>`;
  }

  function renderCulaDunTable() {
    const el = $("culaDunTable");
    if (!el || !culaHub) return;
    const rows = Object.entries(culaHub.byDun || {})
      .map(([code, d]) => ({ code, ...d }))
      .filter((d) => d.verified_delta_total > 0 || d.pending_count > 0 || d.bkc_cula != null)
      .sort((a, b) => (a.bkc_cula ?? 0) - (b.bkc_cula ?? 0));

    if (!rows.length) {
      el.innerHTML = `<p style="font-size:13px;color:var(--muted)">Belum ada cula verified. Lapangan hantar borang → PDM lulus → data muncul di sini.</p>`;
      return;
    }

    el.innerHTML = `
      <table class="cula-table">
        <thead><tr>
          <th>DUN</th><th>+24j</th><th>Verified Δ</th><th>Digital Total</th><th>BKC</th><th>Pending</th><th>Kemaskini</th>
        </tr></thead>
        <tbody>${rows
          .map(
            (d) => `
          <tr>
            <td><strong>${d.code}</strong> ${d.name || ""}</td>
            <td class="green">+${fmt(d.verified_delta_24h)}</td>
            <td>+${fmt(d.verified_delta_total)}</td>
            <td>${d.digital_cula_total != null ? fmt(d.digital_cula_total) : "—"}${d.digital_cula_pct != null ? `<br><span style="font-size:10px;color:var(--muted)">${d.digital_cula_pct}%</span>` : ""}</td>
            <td class="${d.bkc_cula != null && d.bkc_cula < -2000 ? "amber" : ""}">${d.bkc_cula != null ? fmt(d.bkc_cula) : "—"}</td>
            <td>${d.pending_count || 0}</td>
            <td style="font-size:10px;color:var(--muted)">${d.last_verified_at || "—"}</td>
          </tr>`
          )
          .join("")}</tbody>
      </table>`;
  }

  function setCulaTab(tab) {
    culaTab = tab;
    ["upload", "lapangan", "semakan", "ringkasan"].forEach((t) => {
      $("culaTab-" + t)?.classList.toggle("active", t === tab);
      $("culaPanel-" + t)?.classList.toggle("hidden", t !== tab);
    });
    if (tab === "semakan") loadCulaPending();
    if (tab === "ringkasan" || tab === "upload") loadCulaHub();
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
      msg.textContent = "Isi ID Uploader (HQ/PDM) dahulu.";
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
      msg.textContent = `✓ ${data.imported} rekod imported — dashboard dikemaskini.`;
      msg.classList.add("ok");
      if (data.errors?.length) {
        log.textContent = data.errors.join("\n");
        log.classList.remove("hidden");
      }
      if (typeof showToast === "function") showToast(`✓ ${data.imported} rekod imported`);
      $("culaCsvFile").value = "";
      $("culaWhatsappPaste").value = "";
      await loadCulaHub();
      setCulaTab("ringkasan");
    } catch (e) {
      msg.textContent = e.message || "Upload gagal.";
      msg.classList.add("err");
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = "Upload & Kemaskini Dashboard"; }
    }
  }

  window.initDigitalCula = async function initDigitalCula() {
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
    $("culaTab-semakan")?.addEventListener("click", () => setCulaTab("semakan"));
    $("culaTab-ringkasan")?.addEventListener("click", () => setCulaTab("ringkasan"));
    $("culaUploadBtn")?.addEventListener("click", uploadBatch);
    $("culaBatchTarikh") && ($("culaBatchTarikh").value = todayISO());
    await checkApiHealth();
    try {
      await loadCulaDuns();
      await loadCulaHub();
      await loadCulaPending();
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
      if (culaTab === "semakan") await loadCulaPending();
    } catch (e) {
      console.warn("Cula refresh:", e);
    }
  };
})();
