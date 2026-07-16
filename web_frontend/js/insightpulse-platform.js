/**
 * InsightPulse Platform Layer — unified data sources (crawl + upload + feeds + hybrid)
 */
(function (global) {
  const API = window.location.origin;

  const ANALYSIS_HELP = {
    social_listening: 'Best with social crawl. Monitor narrative, sentiment, and trend spikes.',
    sme_insights: 'Combine social crawl + borrower CSV + BNM/Bursa feeds for PMKS advisory.',
    issue_detection: 'Use social crawl + complaint upload for hotspot and crisis detection.',
    competitor_analysis: 'Social crawl + news/Bursa sector feeds for share-of-voice comparison.',
    product_intelligence: 'Reviews/marketplace crawl + product complaint CSV.',
    market_research: 'Social + DOSM/Bursa feeds + survey CSV for demand/supply view.',
    brand_monitoring: 'Social crawl + news feed for reputation and brand health.',
    portfolio_intelligence: 'Social signal + borrower list + macro feeds → EWS advisory.',
    field_operations: 'Upload cula/field CSV + optional post URL batch for validation.',
    economy_outlook: 'BNM + Bursa + DOSM feeds with optional social context.',
    public_complaint: 'Complaint log upload + social crawl for agency dispatch.',
  };

  const MODE_HELP = {
    social_crawl: 'Collect live data from selected social/news/marketplace platforms.',
    upload: 'Import CSV/Excel (Save As CSV): cula, borrower list, complaints, indicators.',
    feed: 'Attach macro/sector feeds (BNM, Bursa, DOSM) to enrich analysis.',
    hybrid: 'Full intelligence package: crawl + upload + external feeds together.',
  };

  const state = {
    dataSourceMode: 'social_crawl',
    uploadIds: [],
    uploadMeta: [],
    feedIds: [],
    pendingFiles: [],
  };

  function $(id) { return document.getElementById(id); }

  function setDataSourceMode(mode) {
    state.dataSourceMode = mode;
    ['social_crawl', 'upload', 'feed', 'hybrid'].forEach(m => {
      const btn = $('btnSource' + m.split('_').map(s => s[0].toUpperCase() + s.slice(1)).join(''));
      if (!btn) return;
      const active = m === mode;
      btn.classList.toggle('btn-primary', active);
      btn.classList.toggle('btn-outline-primary', !active && m !== 'hybrid');
      btn.classList.toggle('btn-outline-success', !active && m === 'hybrid');
    });

    const crawlSec = $('crawlModeSection');
    const uploadSec = $('uploadDataSection');
    const feedSec = $('connectFeedSection');
    const hybridSec = $('hybridSummarySection');
    const platSec = $('platformSection');
    const kwSec = $('keywordInputSection');
    const urlSec = $('urlInputSection');

    const showCrawl = mode === 'social_crawl' || mode === 'hybrid';
    const showUpload = mode === 'upload' || mode === 'hybrid';
    const showFeed = mode === 'feed' || mode === 'hybrid';

    if (crawlSec) crawlSec.style.display = showCrawl ? 'block' : 'none';
    if (uploadSec) uploadSec.style.display = showUpload ? 'block' : 'none';
    if (feedSec) feedSec.style.display = showFeed ? 'block' : 'none';
    if (hybridSec) hybridSec.style.display = mode === 'hybrid' ? 'block' : 'none';
    if (platSec) platSec.style.display = showCrawl ? 'block' : 'none';

    if (mode === 'upload' || mode === 'feed') {
      if (kwSec) kwSec.style.display = 'none';
      if (urlSec) urlSec.style.display = 'none';
    } else if (showCrawl && typeof setCrawlMode === 'function') {
      setCrawlMode(window._crawlMode || 'keyword');
    }

    const help = $('dataSourceHelp');
    if (help) help.textContent = MODE_HELP[mode] || '';

    updatePackageSummary();
    if (global.IPFormState) global.IPFormState.saveFormState();
  }

  function onAnalysisTypeChange() {
    const sel = $('analysisType');
    const help = $('analysisTypeHelp');
    if (!sel || !help) return;
    help.textContent = ANALYSIS_HELP[sel.value] || 'Select analysis type to see recommended data sources.';
    if (sel.value === 'field_operations') setDataSourceMode('upload');
    else if (sel.value === 'economy_outlook') setDataSourceMode('feed');
    else if (sel.value === 'portfolio_intelligence') setDataSourceMode('hybrid');
    updatePackageSummary();
  }

  function updatePackageSummary() {
    const box = $('packageSummary');
    if (!box) return;
    const mode = state.dataSourceMode;
    const at = $('analysisType')?.value || 'social_listening';
    const uploads = state.uploadMeta.length;
    const feeds = state.feedIds.length;
    const plats = document.querySelectorAll('.platform-item input:checked').length;
    let parts = [`Mode: ${mode}`, `Analysis: ${at}`];
    if (mode !== 'upload' && mode !== 'feed') {
      const crawlMode = window._crawlMode || 'keyword';
      const crawlLabel = crawlMode === 'direct_url'
        ? (window._directUrlTarget === 'post' ? 'Post URL Batch' : 'Direct URL')
        : 'Keyword Search';
      parts.push(`Crawl: ${crawlLabel}`);
      const platBadge = plats
        ? `Platforms: ${plats}`
        : `<span class="text-danger fw-semibold">Platforms: 0 — pilih sekurang-kurangnya 1</span>`;
      parts.push(platBadge);
    }
    if (uploads) parts.push(`Uploads: ${uploads}`);
    if (feeds) parts.push(`Feeds: ${feeds}`);
    box.innerHTML = parts.map(p => `<span class="badge bg-light text-dark border me-1 mb-1">${p}</span>`).join('');
  }

  async function uploadPendingFiles() {
    const input = $('dataUploadInput');
    const datasetType = $('datasetType')?.value || 'generic_csv';
    const projectId = $('projectId')?.value || null;
    const files = input?.files ? Array.from(input.files) : state.pendingFiles;
    state.uploadIds = [];
    state.uploadMeta = [];

    for (const file of files) {
      const fd = new FormData();
      fd.append('file', file);
      const url = new URL(`${API}/api/data/upload`);
      url.searchParams.set('dataset_type', datasetType);
      if (projectId) url.searchParams.set('project_id', projectId);
      const res = await fetch(url.toString(), { method: 'POST', body: fd });
      if (!res.ok) throw new Error(`Upload failed: ${file.name}`);
      const data = await res.json();
      state.uploadIds.push(data.upload.upload_id);
      state.uploadMeta.push(data.upload);
    }
    renderUploadPreview();
    updatePackageSummary();
    return state.uploadIds;
  }

  function renderUploadPreview() {
    const el = $('uploadPreview');
    if (!el) return;
    if (!state.uploadMeta.length) {
      el.innerHTML = '<small class="text-muted">No files uploaded yet.</small>';
      return;
    }
    el.innerHTML = state.uploadMeta.map(u => {
      const s = u.summary || {};
      let extra = `${u.rows || 0} rows · ${u.detected_type || u.dataset_type}`;
      if (s.total_cula != null) extra += ` · ${s.total_cula} cula · ${s.dun_count} DUN`;
      if (s.borrower_count != null) extra += ` · ${s.borrower_count} borrowers`;
      if (s.complaint_count != null) extra += ` · ${s.complaint_count} complaints`;
      return `<div class="border rounded p-2 mb-2 bg-white"><strong>${u.filename}</strong><br><small>${extra}</small></div>`;
    }).join('');
  }

  function collectFeedIds() {
    state.feedIds = [];
    document.querySelectorAll('.feed-check:checked').forEach(cb => state.feedIds.push(cb.value));
    updatePackageSummary();
    return state.feedIds;
  }

  function bindFeedChecks() {
    document.querySelectorAll('.feed-check').forEach(cb => {
      cb.addEventListener('change', collectFeedIds);
    });
  }

  function bindUploadInput() {
    const input = $('dataUploadInput');
    if (!input) return;
    input.addEventListener('change', () => {
      state.pendingFiles = Array.from(input.files || []);
    });
  }

  async function validateBeforeStart(mode) {
    collectFeedIds();
    if (mode === 'upload') {
      if (!state.pendingFiles.length && !state.uploadIds.length) {
        alert('Sila upload sekurang-kurangnya satu fail CSV/Excel (Save As CSV).');
        return false;
      }
      if (state.pendingFiles.length) await uploadPendingFiles();
      if (!state.uploadIds.length) return false;
      return true;
    }
    if (mode === 'feed') {
      if (!state.feedIds.length) {
        alert('Sila pilih sekurang-kurangnya satu external feed (BNM, Bursa, DOSM).');
        return false;
      }
      return true;
    }
    if (mode === 'hybrid') {
      if (state.pendingFiles.length) await uploadPendingFiles();
      const hasCrawl = document.querySelector('.platform-item input:checked');
      if (!hasCrawl && !state.uploadIds.length && !state.feedIds.length) {
        alert('Hybrid mode: pilih platform crawl, upload fail, atau feed — sekurang-kurangnya satu.');
        return false;
      }
      return true;
    }
    return true;
  }

  function buildExtraPayload(mode) {
    return {
      data_source_mode: mode,
      upload_ids: state.uploadIds.length ? state.uploadIds : null,
      feed_ids: state.feedIds.length ? state.feedIds : null,
      dataset_type: $('datasetType')?.value || 'generic_csv',
      skip_crawl: mode === 'upload' || mode === 'feed',
    };
  }

  function renderUnifiedResults(result, container) {
    if (!result?.unified || !container) return false;
    let html = `<div class="alert alert-primary"><strong>Unified Intelligence Package</strong> — ${result.analysis_type_label || result.analysis_type}</div>`;
    html += `<p><strong>Recommended dashboard:</strong> <code>${result.recommended_dashboard || '—'}</code></p>`;

    if (result.upload_summaries?.length) {
      html += '<h5 class="mt-3">Upload Summary</h5><ul>';
      result.upload_summaries.forEach(u => {
        const s = u.summary || {};
        html += `<li><strong>${u.filename}</strong>: ${s.row_count || 0} rows`;
        if (s.strategic_action) html += `<br><em>Strategic:</em> ${s.strategic_action}`;
        if (s.tactical_action) html += `<br><em>Tactical:</em> ${s.tactical_action}`;
        html += '</li>';
      });
      html += '</ul>';
    }

    if (result.feed_bundle?.feeds?.length) {
      html += '<h5 class="mt-3">External Feeds</h5><ul>';
      result.feed_bundle.feeds.forEach(f => {
        html += `<li><strong>${f.label}</strong></li>`;
      });
      html += '</ul>';
      if (result.feed_bundle.sector_outlook?.length) {
        html += '<div class="row g-2">';
        result.feed_bundle.sector_outlook.forEach(sec => {
          html += `<div class="col-md-6"><div class="border rounded p-2"><strong>${sec.name}</strong> — ${sec.status}<br><small>${sec.note || ''}</small></div></div>`;
        });
        html += '</div>';
      }
    }

    if (result.key_insights?.length) {
      html += '<h5 class="mt-3">Key Insights</h5><ul>';
      result.key_insights.forEach(i => { html += `<li>${i}</li>`; });
      html += '</ul>';
    }
    if (result.recommendations?.length) {
      html += '<h5 class="mt-3">Strategic & Tactical Actions</h5><ul>';
      result.recommendations.forEach(r => { html += `<li>${r}</li>`; });
      html += '</ul>';
    }

    const ml = result.ml_analytics;
    if (ml?.success && (ml.predictive?.models || ml.prescriptive_actions?.length)) {
      html += '<h5 class="mt-3">ML Analytics</h5>';
      html += `<p><span class="badge bg-purple">${ml.analytics_tier || 'descriptive'}</span> · ${ml.domain || 'analysis'}</p>`;
      if (ml.predictive?.models) {
        html += '<ul class="small">';
        Object.entries(ml.predictive.models).forEach(([name, s]) => {
          if (s.cv_accuracy_mean != null) {
            html += `<li><strong>${name}</strong>: CV accuracy ${Math.round(s.cv_accuracy_mean * 100)}% · F1 ${Math.round((s.cv_f1_mean || 0) * 100)}%</li>`;
          }
        });
        html += '</ul>';
      }
      if (ml.prescriptive_actions?.length) {
        html += '<p class="fw-semibold mt-2">Prescriptive (ML-ranked)</p><ul>';
        ml.prescriptive_actions.slice(0, 5).forEach(a => {
          html += `<li><strong>[${(a.urgency || 'action').toUpperCase()}]</strong> ${a.title}</li>`;
        });
        html += '</ul>';
      }
      if (ml.seat_predictions?.length) {
        html += '<p class="fw-semibold mt-2">Top seat predictions</p><ul class="small">';
        ml.seat_predictions.slice(0, 5).forEach(s => {
          html += `<li>${s.code} ${s.name || ''} — ML ${Math.round((s.ml_competitive_prob || 0) * 100)}%</li>`;
        });
        html += '</ul>';
      }
      if (ml.borrower_predictions?.length) {
        html += '<p class="fw-semibold mt-2">Borrower EWS</p><ul class="small">';
        ml.borrower_predictions.slice(0, 5).forEach(b => {
          html += `<li>${b.borrower} — HIGH risk ${Math.round((b.ml_high_risk_prob || 0) * 100)}%</li>`;
        });
        html += '</ul>';
      }
    }

    container.insertAdjacentHTML('afterbegin', html);
    return true;
  }

  function init() {
    setDataSourceMode('social_crawl');
    onAnalysisTypeChange();
    bindFeedChecks();
    bindUploadInput();
    const at = $('analysisType');
    if (at) at.addEventListener('change', onAnalysisTypeChange);
    document.querySelectorAll('.platform-item input').forEach(cb => cb.addEventListener('change', updatePackageSummary));
  }

  global.IPPlatform = {
    state,
    setDataSourceMode,
    onAnalysisTypeChange,
    validateBeforeStart,
    buildExtraPayload,
    renderUnifiedResults,
    uploadPendingFiles,
    init,
  };

  document.addEventListener('DOMContentLoaded', init);
})(window);
