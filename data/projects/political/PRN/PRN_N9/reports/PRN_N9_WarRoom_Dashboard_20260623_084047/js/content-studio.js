/**
 * InsightPulse PRN N9 V2 — Content Studio
 * Tukar signal/tindakan kepada kandungan siap guna:
 *   FB/IG caption · skrip TikTok/Reels · hashtag · prompt video AI · insight ringkas.
 *
 * Generator tempatan (offline, copy & paste terus). Butang "Naik taraf AI"
 * memanggil /api/content/generate yang sedia untuk disambung ke LLM + RAG + VectorDB.
 */
(function () {
  const ISSUE_LABEL_BM = {
    "Cost of Living": "Kos Sara Hidup",
    "SME and Business": "PKS & Perniagaan",
    "Local Government Services": "Perkhidmatan Kerajaan Tempatan",
    "Employment": "Pekerjaan",
    "Candidate Performance": "Prestasi Calon",
    "Misinformation": "Salah Maklumat",
    "DAP Performance": "Prestasi DAP",
    "Chinese Education": "Pendidikan Cina",
    "PAS Factor": "Faktor PAS",
    "Ekonomi & Pekerjaan": "Ekonomi & Pekerjaan",
    "Perkhidmatan kerajaan tempatan": "Perkhidmatan Kerajaan Tempatan",
    "Other": "Isu Komuniti",
  };

  function esc(v) {
    return String(v ?? "").replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
    }[ch]));
  }

  function issueBm(label) {
    return ISSUE_LABEL_BM[label] || label || "Isu Komuniti";
  }

  function normalize(item) {
    const dun = item.dun || "N9";
    const seat = item.seat || item.nama_dun || "";
    const rawIssue = item.issue_cluster
      || (item.title ? String(item.title).split("—")[0].trim() : "")
      || item.category || "Isu Komuniti";
    const issue = issueBm(rawIssue);
    const platform = item.platform || "Facebook";
    const sentiment = item.sentiment_summary || item.sentiment || "campuran";
    const emotion = item.emotion_summary || "";
    const recommended = item.recommended_action
      || (Array.isArray(item.recommended_steps) ? item.recommended_steps[0] : "")
      || "Sediakan respons komunikasi yang jelas dan beramanah.";
    const evidence = item.evidence || [];
    return { id: item.id || "", dun, seat, issue, platform, sentiment, emotion, recommended, evidence };
  }

  function tone(ctx) {
    return /negat|risau|marah|bimbang|skeptik/i.test(ctx.sentiment + " " + ctx.emotion)
      ? "empati-tenang"
      : "harapan-positif";
  }

  function genFbIg(ctx) {
    const hook = tone(ctx) === "empati-tenang"
      ? `Kami dengar kebimbangan anda tentang ${ctx.issue.toLowerCase()} di ${ctx.seat || ctx.dun}.`
      : `Berita baik untuk warga ${ctx.seat || ctx.dun}: tindakan untuk ${ctx.issue.toLowerCase()} sedang bergerak.`;
    return [
      `${hook}`,
      ``,
      `Apa yang kami buat:`,
      `• [Isi 1 fakta/inisiatif sebenar di sini]`,
      `• [Isi 1 lagi langkah konkrit]`,
      ``,
      `Apa anda boleh buat:`,
      `👉 [CTA: hadir program / hubungi pejabat khidmat / kongsi maklumat sahih]`,
      ``,
      genHashtags(ctx),
    ].join("\n");
  }

  function genTikTok(ctx) {
    return [
      `JUDUL: ${ctx.issue} — ${ctx.seat || ctx.dun}`,
      `FORMAT: 9:16 · 25–35 saat · sari kata BM`,
      ``,
      `[0–3s] HOOK (teks besar): "${tone(ctx) === "empati-tenang" ? "Anda risau pasal " + ctx.issue.toLowerCase() + "?" : ctx.issue + " — kami ambil tindakan"}"`,
      `[3–10s] MASALAH: nyatakan isu rakyat secara jujur dan ringkas.`,
      `[10–20s] JAWAPAN: tunjuk apa yang sedang/akan dibuat — [isi fakta sebenar].`,
      `[20–27s] BUKTI: rakam lokasi/aktiviti sebenar di ${ctx.seat || ctx.dun}.`,
      `[27–32s] CTA: "${tone(ctx) === "empati-tenang" ? "Kami bersama anda — hubungi pejabat kami." : "Sertai kami. Sebarkan maklumat yang sahih."}"`,
      ``,
      `Caption: ${ctx.issue} di ${ctx.seat || ctx.dun}. ${ctx.recommended}`,
      genHashtags(ctx),
    ].join("\n");
  }

  function genVideoPrompt(ctx) {
    return [
      `Cipta video pendek menegak (9:16), 30 saat, gaya dokumentari komuniti Malaysia.`,
      `Lokasi: ${ctx.seat || ctx.dun}, Negeri Sembilan.`,
      `Subjek: isu ${ctx.issue.toLowerCase()} dan tindakan penyelesaian.`,
      `Nada: ${tone(ctx) === "empati-tenang" ? "empati, tenang, beramanah" : "harapan, mesra, bertenaga"}.`,
      `Babak: (1) wajah/lokasi tempatan, (2) teks isu di skrin, (3) aktiviti tindakan, (4) CTA.`,
      `Teks atas skrin (BM): ringkas, 4–6 patah perkataan setiap babak.`,
      `Elakkan: dakwaan tidak disahkan, imej sensitif, muka individu tanpa izin.`,
      `Output: storyboard 4 babak + cadangan VO 30 saat dalam BM.`,
    ].join("\n");
  }

  function genHashtags(ctx) {
    const seatTag = (ctx.seat || "").replace(/[^a-zA-Z]/g, "");
    const issueTag = (ctx.issue || "").replace(/[^a-zA-Z]/g, "");
    return [
      "#PRNNegeriSembilan", "#N9", ctx.dun ? `#${ctx.dun}` : "",
      seatTag ? `#${seatTag}` : "", issueTag ? `#${issueTag}` : "",
    ].filter(Boolean).join(" ");
  }

  function genInsight(ctx) {
    return [
      `Apa berlaku: Signal ${ctx.issue} di ${ctx.seat || ctx.dun} · sentimen ${ctx.sentiment}${ctx.emotion ? " · emosi " + ctx.emotion : ""}.`,
      `Kenapa penting: boleh mempengaruhi persepsi pengundi di kerusi ini jika tidak dijawab.`,
      `Tindakan disyorkan: ${ctx.recommended}`,
      `KPI dipantau: engagement, anjakan sentimen, komen positif dalam 24–48 jam selepas posting.`,
    ].join("\n");
  }

  function buildPack(item) {
    const ctx = normalize(item);
    return {
      ctx,
      insight: genInsight(ctx),
      fb_ig: genFbIg(ctx),
      tiktok: genTikTok(ctx),
      video_prompt: genVideoPrompt(ctx),
      hashtags: genHashtags(ctx),
    };
  }

  function ensureModal() {
    let modal = document.getElementById("contentStudioModal");
    if (modal) return modal;
    modal = document.createElement("div");
    modal.id = "contentStudioModal";
    modal.className = "cs-overlay";
    modal.setAttribute("aria-hidden", "true");
    modal.innerHTML = `
      <div class="cs-backdrop" data-cs-close></div>
      <div class="cs-panel" role="dialog" aria-label="Content Studio">
        <button class="cs-close" data-cs-close aria-label="Tutup">×</button>
        <div class="cs-head">
          <h3 id="csTitle">Content Studio</h3>
          <p class="desc" id="csSub">Kandungan siap guna — copy &amp; paste terus laksanakan.</p>
        </div>
        <div class="cs-tabs" id="csTabs"></div>
        <div class="cs-body" id="csBody"></div>
        <div class="cs-foot">
          <button class="btn btn-ghost btn-sm" id="csAiBtn">Naik taraf dengan AI (LLM)</button>
          <span class="cs-foot-note" id="csAiNote">Versi asas (templat). Sambung LLM + RAG untuk versi penuh.</span>
        </div>
      </div>`;
    document.body.appendChild(modal);
    modal.querySelectorAll("[data-cs-close]").forEach((el) =>
      el.addEventListener("click", () => closeStudio())
    );
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("open")) closeStudio();
    });
    return modal;
  }

  function closeStudio() {
    const modal = document.getElementById("contentStudioModal");
    if (modal) {
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
    }
  }

  let activePack = null;

  const TABS = [
    { key: "insight", label: "Insight" },
    { key: "fb_ig", label: "FB / IG" },
    { key: "tiktok", label: "TikTok / Reels" },
    { key: "video_prompt", label: "Prompt Video AI" },
    { key: "hashtags", label: "Hashtag" },
  ];

  function renderTab(key) {
    if (!activePack) return;
    const body = document.getElementById("csBody");
    const text = activePack[key] || "";
    document.querySelectorAll("#csTabs .cs-tab").forEach((b) =>
      b.classList.toggle("active", b.dataset.tab === key)
    );
    body.innerHTML = `
      <div class="cs-output-head">
        <span>${esc(TABS.find((t) => t.key === key)?.label || key)}</span>
        <button class="btn btn-primary btn-sm" id="csCopyBtn">Salin</button>
      </div>
      <textarea class="cs-textarea" id="csTextarea" spellcheck="false">${esc(text)}</textarea>
      ${key === "fb_ig" || key === "tiktok" ? `<p class="cs-tip">Tip: isi bahagian <strong>[...]</strong> dengan fakta sebenar sebelum hantar. Jangan auto-post tanpa semakan.</p>` : ""}`;
    document.getElementById("csCopyBtn").addEventListener("click", async () => {
      const val = document.getElementById("csTextarea").value;
      try {
        await navigator.clipboard.writeText(val);
        if (typeof showToast === "function") showToast("✓ Disalin — sedia paste");
      } catch {
        document.getElementById("csTextarea").select();
        if (typeof showToast === "function") showToast("Tekan Cmd/Ctrl+C untuk salin");
      }
    });
  }

  window.openContentStudio = function openContentStudio(item) {
    const modal = ensureModal();
    activePack = buildPack(item || {});
    const ctx = activePack.ctx;
    document.getElementById("csTitle").textContent = `Content Studio — ${ctx.seat || ctx.dun}`;
    document.getElementById("csSub").textContent = `${ctx.issue} · ${ctx.platform} · sentimen ${ctx.sentiment}`;
    document.getElementById("csTabs").innerHTML = TABS.map(
      (t, i) => `<button class="cs-tab ${i === 0 ? "active" : ""}" data-tab="${t.key}">${esc(t.label)}</button>`
    ).join("");
    document.querySelectorAll("#csTabs .cs-tab").forEach((b) =>
      b.addEventListener("click", () => renderTab(b.dataset.tab))
    );
    const aiNote = document.getElementById("csAiNote");
    if (aiNote) aiNote.textContent = "Versi asas (templat). Sambung LLM + RAG untuk versi penuh.";
    document.getElementById("csAiBtn").onclick = () => upgradeWithAi(item);
    renderTab("insight");
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
  };

  async function upgradeWithAi(item) {
    const note = document.getElementById("csAiNote");
    if (note) note.textContent = "Menjana versi AI…";
    try {
      const res = await fetch("/api/content/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: typeof state !== "undefined" ? state : "N9", item }),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const payload = await res.json();
      if (!payload.ok) throw new Error(payload.error || "Gagal");
      const c = payload.content || {};
      activePack = {
        ctx: activePack.ctx,
        insight: c.insight || activePack.insight,
        fb_ig: c.fb_ig || activePack.fb_ig,
        tiktok: c.tiktok || activePack.tiktok,
        video_prompt: c.video_prompt || activePack.video_prompt,
        hashtags: c.hashtags || activePack.hashtags,
      };
      renderTab(document.querySelector("#csTabs .cs-tab.active")?.dataset.tab || "insight");
      if (note) {
        note.textContent = c.ai_ready
          ? "Versi AI (LLM) dijana."
          : "Backend belum sambung LLM — masih versi templat. Tetapkan LLM/RAG di lib/ai.";
      }
    } catch (e) {
      if (note) note.textContent = "Tiada backend AI — guna versi templat (sudah copy-paste ready).";
    }
  }

  window.ContentStudio = { buildPack };
})();
