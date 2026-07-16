/**
 * Persist crawl form state (project, platforms, query, processing) across refresh.
 */
(function (global) {
  const STORAGE_KEY = "insightpulse_crawl_form_v1";

  const DEFAULT_PLATFORMS = {
    political: ["facebook", "tiktok", "youtube", "news", "x"],
    sme: ["facebook", "news", "google"],
    agency: ["facebook", "x", "news"],
    commercial: ["facebook", "instagram", "google"],
  };

  function $(id) {
    return document.getElementById(id);
  }

  function readState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  }

  function writeState(patch) {
    const next = { ...(readState() || {}), ...patch, saved_at: new Date().toISOString() };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch (_) {
      /* ignore quota / private mode */
    }
  }

  function collectState() {
    const platforms = [];
    document.querySelectorAll(".platform-item input[type='checkbox']:checked").forEach((cb) => {
      platforms.push(cb.value);
    });
    return {
      projectId: $("projectId")?.value || "",
      analysisQuery: $("analysisQuery")?.value || "",
      analysisType: $("analysisType")?.value || "social_listening",
      processingMode: $("processingMode")?.value || "on-prem-nemotron",
      enableMultimodal: Boolean($("enableMultimodal")?.checked),
      dataSourceMode: global.IPPlatform?.state?.dataSourceMode || "social_crawl",
      crawlMode: (global._directUrlTarget === "post" && global._crawlMode === "direct_url")
        ? "direct_url_post"
        : (global._crawlMode || "keyword"),
      directUrlInput: $("directUrlInput")?.value || "",
      commentTargetPerPost: $("commentTargetPerPost")?.value || "3000",
      multipassComments: $("multipassComments")?.checked !== false,
      includeNestedComments: $("includeNestedComments")?.checked !== false,
      maxResults: $("maxResults")?.value || "",
      dateRange: $("dateRange")?.value || "",
      platforms,
    };
  }

  function saveFormState() {
    writeState(collectState());
  }

  function setPlatformChecked(platformId, checked) {
    const checkbox = $(platformId);
    if (!checkbox) return;
    checkbox.checked = checked;
    const item = checkbox.closest(".platform-item");
    if (item) item.classList.toggle("selected", checked);
  }

  function setPlatforms(platformIds) {
    document.querySelectorAll(".platform-item input[type='checkbox']").forEach((cb) => {
      setPlatformChecked(cb.id, false);
    });
    (platformIds || []).forEach((id) => setPlatformChecked(id, true));
    if (typeof updateDatasetInfo === "function") updateDatasetInfo();
    if (global.IPPlatform?.updatePackageSummary) global.IPPlatform.updatePackageSummary();
    else if (typeof updatePackageSummary === "function") updatePackageSummary();
  }

  function applyProjectProfile(projectId, projects) {
    const project = (projects || []).find((p) => p.project_id === projectId);
    if (!project) return;

    const processing = $("processingMode");
    if (processing && project.processing) processing.value = project.processing;

    const multimodal = $("enableMultimodal");
    if (multimodal) multimodal.checked = Boolean(project.multimodal);

    const saved = readState();
    const hasSavedPlatforms = saved?.projectId === projectId && (saved.platforms || []).length;
    if (!hasSavedPlatforms) {
      const category = project.category || "commercial";
      setPlatforms(DEFAULT_PLATFORMS[category] || DEFAULT_PLATFORMS.commercial);
    }
  }

  function restoreFormState(fallbackProjectId) {
    const saved = readState();
    const projectSel = $("projectId");
    const projectId = saved?.projectId || fallbackProjectId || "PRN_N9";
    if (projectSel && projectId && [...projectSel.options].some((o) => o.value === projectId)) {
      projectSel.value = projectId;
    }

    if (saved?.analysisQuery && $("analysisQuery")) $("analysisQuery").value = saved.analysisQuery;
    if (saved?.analysisType && $("analysisType")) $("analysisType").value = saved.analysisType;
    if (saved?.processingMode && $("processingMode")) $("processingMode").value = saved.processingMode;
    if (saved?.enableMultimodal != null && $("enableMultimodal")) {
      $("enableMultimodal").checked = Boolean(saved.enableMultimodal);
    }
    if (saved?.maxResults && $("maxResults")) $("maxResults").value = saved.maxResults;
    if (saved?.dateRange && $("dateRange")) $("dateRange").value = saved.dateRange;
    if (saved?.directUrlInput && $("directUrlInput")) $("directUrlInput").value = saved.directUrlInput;
    if (saved?.commentTargetPerPost && $("commentTargetPerPost")) {
      $("commentTargetPerPost").value = saved.commentTargetPerPost;
    }
    if (saved?.multipassComments != null && $("multipassComments")) {
      $("multipassComments").checked = Boolean(saved.multipassComments);
    }
    if (saved?.includeNestedComments != null && $("includeNestedComments")) {
      $("includeNestedComments").checked = Boolean(saved.includeNestedComments);
    }

    if (saved?.crawlMode && typeof setCrawlMode === "function") setCrawlMode(saved.crawlMode);
    if (saved?.dataSourceMode && global.IPPlatform?.setDataSourceMode) {
      global.IPPlatform.setDataSourceMode(saved.dataSourceMode);
    }

    if ((saved?.platforms || []).length) {
      setPlatforms(saved.platforms);
    } else if (global._ipProjects && projectSel?.value) {
      applyProjectProfile(projectSel.value, global._ipProjects);
    }

    if (global.IPPlatform?.onAnalysisTypeChange) global.IPPlatform.onAnalysisTypeChange();
    saveFormState();
  }

  function bindPersistence() {
    [
      "projectId",
      "analysisQuery",
      "analysisType",
      "processingMode",
      "enableMultimodal",
      "maxResults",
      "dateRange",
      "directUrlInput",
      "commentTargetPerPost",
      "multipassComments",
      "includeNestedComments",
    ].forEach((id) => {
      const el = $(id);
      if (!el) return;
      el.addEventListener("change", saveFormState);
      if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
        el.addEventListener("input", saveFormState);
      }
    });

    const projectSel = $("projectId");
    if (projectSel) {
      projectSel.addEventListener("change", () => {
        applyProjectProfile(projectSel.value, global._ipProjects || []);
        saveFormState();
      });
    }

    document.querySelectorAll(".platform-item input[type='checkbox']").forEach((cb) => {
      cb.addEventListener("change", saveFormState);
    });
  }

  global.IPFormState = {
    saveFormState,
    restoreFormState,
    applyProjectProfile,
    setPlatforms,
    readState,
  };

  document.addEventListener("DOMContentLoaded", bindPersistence);
})(window);
