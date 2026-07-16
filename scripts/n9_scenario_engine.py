"""Scenario Engine JS block for PRN N9 dashboard — injected at generate time."""


def scenario_engine_js() -> str:
    # Raw JS — no Python f-string braces except escaped as {{ }}
    return r"""
// ═══════════════════════════════════════════════════════════════
// SCENARIO ENGINE — data-driven alliance scenario module
// FUTURE: load scenario_input_template.csv via PapaParse
// FUTURE: load seat_features_template.csv
// FUTURE: merge live InsightPulse signals
// ═══════════════════════════════════════════════════════════════

let scenarioFilter = 'all';
let selectedScenarioCode = null;

const verifiedFacts = [
  { id: 'fact_001', category: 'alliances', statement: 'PAS telah menamatkan kerjasama politik dengan Bersatu', status: 'verified', sourceLabel: 'Media report / kenyataan rasmi', implication: 'Meningkatkan ketidakpastian hala tuju PN di N9' },
  { id: 'fact_002', category: 'alliances', statement: 'Bersatu Negeri Sembilan menyatakan masih akan bertanding di bawah platform PN', status: 'verified', sourceLabel: 'Kenyataan negeri Bersatu', implication: 'Operasi lapangan PN masih wujud walaupun hubungan pusat retak' },
  { id: 'fact_003', category: 'operations', statement: 'PAS Negeri Sembilan belum dimuktamadkan sama ada akan menggunakan logo PN', status: 'ambiguity', sourceLabel: 'Keambiguan operasi', implication: 'Signal kritikal untuk kejelasan mesej pengundi' },
  { id: 'fact_004', category: 'alliances', statement: 'Pimpinan UMNO menyatakan tiada perbincangan untuk hidupkan semula Muafakat Nasional 2.0', status: 'verified', sourceLabel: 'Kenyataan UMNO pusat', implication: 'S3 (PAS-UMNO taktikal) kekal spekulatif, bukan rasmi' }
];

const scenarioEngineData = [
  { code: 'S1', title: 'PAS kekal bersama PN secara berfungsi', type: 'scenario', probability: 35, confidence: 'Sederhana', classification: 'Realistik tetapi rapuh', pasSeatMin: 3, pasSeatMax: 6, pnCohesion: 62, messageClarity: 55, malayVoteUnity: 61, threeCornerRisk: 38, grassrootsConflict: 44, phBnBenefit: 42, strategicScore: 64, benefitsMost: 'PAS dan Bersatu jika rundingan kerusi berjaya', strengths: ['Mengurangkan risiko pertembungan terus', 'Mengekalkan sebahagian struktur PN sedia ada', 'Lebih mudah mempertahan kerusi tradisi'], risks: ['Hubungan pusat masih retak', 'Pengundi keliru soal hala tuju PAS', 'Pertindihan kerusi boleh muncul semula'], watchSignals: ['Keputusan lambang PAS N9', 'Penyelarasan kerusi PN', 'Nada kenyataan pemimpin negeri'] },
  { code: 'S2', title: 'PAS bertanding solo', type: 'scenario', probability: 20, confidence: 'Rendah-Sederhana', classification: 'Defensif', pasSeatMin: 2, pasSeatMax: 5, pnCohesion: 18, messageClarity: 74, malayVoteUnity: 37, threeCornerRisk: 79, grassrootsConflict: 52, phBnBenefit: 73, strategicScore: 41, benefitsMost: 'PAS dari segi identiti, tetapi lawan dari segi struktur', strengths: ['Identiti PAS lebih jelas', 'Kempen lebih terkawal secara dalaman', 'Kurang bergantung pada parti lain'], risks: ['Risiko pecah undi sangat tinggi', 'Sukar tambah kerusi campuran', 'Boleh membantu lawan di kerusi marginal'], watchSignals: ['Nada pimpinan PAS pusat', 'Isyarat jentera akar umbi', 'Reaksi pengundi Melayu atas isu solo'] },
  { code: 'S3', title: 'Persefahaman setempat PAS-UMNO / formula Muafakat gaya baharu', type: 'scenario', probability: 15, confidence: 'Rendah', classification: 'Taktikal, bukan rasmi', pasSeatMin: 4, pasSeatMax: 8, pnCohesion: 15, messageClarity: 48, malayVoteUnity: 76, threeCornerRisk: 33, grassrootsConflict: 63, phBnBenefit: 29, strategicScore: 58, benefitsMost: 'PAS di kerusi Melayu jika persefahaman benar-benar wujud', strengths: ['Penyatuan undi Melayu lebih tinggi', 'Kurang risiko pertembungan PAS-Bersatu jika disusun semula', 'Berpotensi bantu kerusi separa luar bandar'], risks: ['Tiada pengesahan rasmi dari UMNO pusat', 'Mudah dicabar oleh mesej pusat BN', 'Boleh cetus konflik dalaman setempat'], watchSignals: ['Isyarat tak rasmi PAS-UMNO negeri', 'Pembahagian kerusi tanpa pengumuman rasmi', 'Nada media terhadap kerjasama taktikal'] },
  { code: 'S4', title: 'PAS vs Bersatu bertembung di kerusi terpilih', type: 'scenario', probability: 20, confidence: 'Sederhana', classification: 'Risiko tinggi', pasSeatMin: 1, pasSeatMax: 4, pnCohesion: 12, messageClarity: 32, malayVoteUnity: 28, threeCornerRisk: 85, grassrootsConflict: 71, phBnBenefit: 82, strategicScore: 26, benefitsMost: 'PH-BN', strengths: ['PAS boleh tunjuk kekuatan sendiri di kawasan tertentu', 'Mesej kepada ahli lebih tegas', 'Boleh uji kekuatan sebenar jentera'], risks: ['Undi Melayu berpecah', 'Lawan mendapat laluan lebih mudah', 'Menghakis persepsi kestabilan blok pembangkang'], watchSignals: ['Pertikaian seat overlap', 'Calon diumum di kerusi sama', 'Serangan terbuka antara penyokong'] },
  { code: 'S5', title: 'Fragmentasi penuh pembangkang', type: 'scenario', probability: 10, confidence: 'Rendah', classification: 'Worst-case', pasSeatMin: 0, pasSeatMax: 3, pnCohesion: 5, messageClarity: 20, malayVoteUnity: 19, threeCornerRisk: 94, grassrootsConflict: 83, phBnBenefit: 91, strategicScore: 18, benefitsMost: 'PH-BN dengan margin lebih selesa', strengths: ['Hampir tiada kekuatan strategik sebenar', 'Hanya sesuai sebagai senario amaran', 'Berguna untuk stress test model'], risks: ['Pembangkang kehilangan koordinasi', 'Pengundi keliru dan kecewa', 'Kerosakan jenama blok lawan lebih besar'], watchSignals: ['Kenyataan saling bercanggah', 'Tiada penyelarasan calon', 'Media framing bahawa blok pembangkang berpecah penuh'] }
];

const scenarioTransitions = [
  { from: 'S1', to: 'S4', trigger: 'Pertindihan kerusi / lambang / rundingan gagal' },
  { from: 'S4', to: 'S5', trigger: 'Konflik merebak ke lebih banyak DUN' },
  { from: 'S1', to: 'S2', trigger: 'PAS memilih identiti solo sepenuhnya' },
  { from: 'S2', to: 'S3', trigger: 'Persefahaman setempat muncul' },
  { from: 'S3', to: 'mixed', trigger: 'Tactical deal wujud hanya di kerusi tertentu' }
];

const monitorSignals = [
  { item: 'Keputusan lambang PAS N9', status: 'pending', importance: 5, note: 'Signal kritikal untuk kejelasan pakatan' },
  { item: 'Penyelarasan kerusi PAS-Bersatu', status: 'active', importance: 5, note: 'Penentu sama ada S1 bertahan atau turun ke S4' },
  { item: 'Kenyataan UMNO pusat vs negeri', status: 'noisy', importance: 4, note: 'Penting untuk menilai kebolehjadian S3' },
  { item: 'Naratif TikTok/Facebook comments', status: 'active', importance: 4, note: 'Pantau tema pengkhianatan, perpaduan Melayu, dan anti-Bersatu' },
  { item: 'Ceramah crowd proxy', status: 'pending', importance: 3, note: 'Boleh jadi pengesah awal momentum akar umbi' }
];

const SCENARIO_FILTER_TABS = [
  { id: 'all', label: 'Semua' },
  { id: 'S1', label: 'S1 PN' },
  { id: 'S2', label: 'S2 Solo' },
  { id: 'S3', label: 'S3 PAS-UMNO' },
  { id: 'S4', label: 'S4 Clash' },
  { id: 'S5', label: 'S5 Fragmented' }
];

const SCENARIO_MATRIX_COLS = [
  { key: 'probability', label: 'Kebolehjadian', type: 'prob' },
  { key: 'messageClarity', label: 'Kejelasan mesej', type: 'high_good' },
  { key: 'malayVoteUnity', label: 'Penyatuan undi Melayu', type: 'high_good' },
  { key: 'threeCornerRisk', label: 'Risiko 3 penjuru', type: 'risk' },
  { key: 'grassrootsConflict', label: 'Konflik akar umbi', type: 'risk' },
  { key: 'phBnBenefit', label: 'Faedah kepada PH-BN', type: 'risk' },
  { key: 'strategicScore', label: 'Skor strategi', type: 'high_good' }
];

// ─── CSV wiring (PapaParse-ready) ───
async function loadCsvText(path) {
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return await res.text();
  } catch (e) {
    console.warn('[ScenarioEngine] CSV load failed:', path, e.message);
    return null;
  }
}

function parseCsv(text) {
  if (!text || typeof Papa === 'undefined') return [];
  return Papa.parse(text, { header: true, skipEmptyLines: true }).data;
}

function mapScenarioCsvRows(rows) {
  return (rows || []).map(r => ({
    code: r.code || r.scenario_code || '',
    title: r.title || r.scenario_title || '',
    type: 'scenario',
    probability: +r.probability || 0,
    confidence: r.confidence || '',
    classification: r.classification || '',
    pasSeatMin: +r.pas_seat_min || 0,
    pasSeatMax: +r.pas_seat_max || 0,
    pnCohesion: +r.pn_cohesion || 0,
    messageClarity: +r.message_clarity || 0,
    malayVoteUnity: +r.malay_vote_unity || 0,
    threeCornerRisk: +r.three_corner_risk || 0,
    grassrootsConflict: +r.grassroots_conflict || 0,
    phBnBenefit: +r.ph_bn_benefit || 0,
    strategicScore: +r.strategic_score || 0,
    benefitsMost: r.benefits_most || '',
    strengths: (r.strengths || '').split('|').filter(Boolean),
    risks: (r.risks || '').split('|').filter(Boolean),
    watchSignals: (r.watch_signals || '').split('|').filter(Boolean)
  }));
}

function mapSeatFeatureRows(rows) {
  return (rows || []).map(r => ({
    code: r.kod_dun || r.code,
    kategoriPas: r.kategori_pas,
    kategoriMargin: r.kategori_margin,
    pasWinProb: +r.pas_win_prob || 0,
    clusterKawasan: r.cluster_kawasan || ''
  }));
}

function mapEventRows(rows) {
  return (rows || []).map(r => ({
    id: r.event_id || r.id,
    date: r.event_date || r.date,
    category: r.category,
    statement: r.statement || r.description,
    status: r.status || 'verified',
    sourceLabel: r.source || r.source_label || ''
  }));
}

async function hydrateScenarioEngineFromCsv(basePath) {
  // FUTURE: load scenario_input_template.csv
  const scenarioText = await loadCsvText(basePath + '/scenario_input_template.csv');
  if (scenarioText) {
    const mapped = mapScenarioCsvRows(parseCsv(scenarioText));
    if (mapped.length) return { scenarios: mapped, source: 'csv' };
  }
  return { scenarios: scenarioEngineData, source: 'mock' };
}

function normalizeScenarioDataset(payload) {
  if (!payload) return scenarioEngineData;
  if (Array.isArray(payload)) return payload;
  if (payload.scenarios) return payload.scenarios;
  return scenarioEngineData;
}

// ─── Analytic utilities ───
function getScenarioByCode(code) {
  return scenarioEngineData.find(s => s.code === code);
}

function getFilteredScenarios() {
  if (scenarioFilter === 'all') return scenarioEngineData;
  return scenarioEngineData.filter(s => s.code === scenarioFilter);
}

function getBestScenario(data) {
  const pool = (data || scenarioEngineData).filter(s => s.probability >= 15);
  return pool.reduce((a, b) => (a.strategicScore >= b.strategicScore ? a : b), pool[0] || scenarioEngineData[0]);
}

function getWorstScenario(data) {
  const pool = data || scenarioEngineData;
  return pool.reduce((a, b) => {
    const scoreA = a.threeCornerRisk - a.strategicScore;
    const scoreB = b.threeCornerRisk - b.strategicScore;
    return scoreA >= scoreB ? a : b;
  }, pool[0]);
}

function getTopTrigger(signals) {
  const sigs = signals || monitorSignals;
  const open = sigs.filter(s => s.status !== 'confirmed' && s.status !== 'resolved');
  return open.sort((a, b) => b.importance - a.importance)[0] || sigs[0];
}

function buildScenarioHeatClass(value, type) {
  const v = +value || 0;
  if (type === 'risk') {
    if (v >= 75) return 'heat-high';
    if (v >= 50) return 'heat-mid';
    return 'heat-low';
  }
  if (type === 'prob') {
    if (v >= 30) return 'heat-good';
    if (v >= 15) return 'heat-mid';
    return 'heat-low';
  }
  if (v >= 65) return 'heat-good';
  if (v >= 40) return 'heat-mid';
  return 'heat-low';
}

function factBadge(status) {
  if (status === 'verified') return '<span class="badge badge-live">Verified Fact</span>';
  if (status === 'ambiguity') return '<span class="badge badge-pending">Operational Ambiguity</span>';
  return '<span class="badge badge-pending">Analytical Scenario</span>';
}

function updateScenarioSummary() {
  const best = getBestScenario(getFilteredScenarios());
  const worst = getWorstScenario(getFilteredScenarios());
  const trigger = getTopTrigger();
  const elSafe = document.getElementById('seSummarySafe');
  const elRisk = document.getElementById('seSummaryRisk');
  const elTrig = document.getElementById('seSummaryTrigger');
  if (elSafe) elSafe.innerHTML = `<strong>${best.code}</strong> · ${best.title}<br><span style="color:var(--muted);font-size:11px">Skor ${best.strategicScore} · ${best.probability}%</span>`;
  if (elRisk) elRisk.innerHTML = `<strong>${worst.code}</strong> · ${worst.classification}<br><span style="color:var(--neg);font-size:11px">3 penjuru ${worst.threeCornerRisk}% · skor ${worst.strategicScore}</span>`;
  if (elTrig) elTrig.innerHTML = `<strong>${trigger.item}</strong><br><span style="color:var(--muted);font-size:11px">${trigger.note}</span>`;
}

function renderScenarioCards(container) {
  const list = getFilteredScenarios();
  container.innerHTML = list.map(s => {
    const sel = selectedScenarioCode === s.code ? ' se-card-selected' : '';
    return `<article class="card se-scenario-card${sel}" data-scenario="${s.code}" tabindex="0" role="button" aria-label="Senario ${s.code}">
      <div class="se-card-head">
        <span class="se-code">${s.code}</span>
        <span class="badge badge-pending">${s.classification}</span>
      </div>
      <h4 class="se-card-title">${s.title}</h4>
      <div class="se-metrics-row">
        <span><span class="card-label">Kebolehjadian</span><strong class="tabular">${s.probability}%</strong></span>
        <span><span class="card-label">Keyakinan</span><strong>${s.confidence}</strong></span>
        <span><span class="card-label">PAS kerusi</span><strong class="tabular">${s.pasSeatMin}–${s.pasSeatMax}</strong></span>
      </div>
      <div class="card-sub" style="margin:8px 0"><strong>Faedah utama:</strong> ${s.benefitsMost}</div>
      <div class="se-list-cols">
        <div><div class="card-label">Kekuatan</div><ul>${s.strengths.slice(0,3).map(x=>`<li>${x}</li>`).join('')}</ul></div>
        <div><div class="card-label">Risiko</div><ul>${s.risks.slice(0,3).map(x=>`<li>${x}</li>`).join('')}</ul></div>
      </div>
      <div class="card-label" style="margin-top:8px">Watch signals</div>
      <div class="se-chips">${s.watchSignals.map(w=>`<span class="chip">${w}</span>`).join('')}</div>
      <span class="badge badge-pending" style="margin-top:8px;display:inline-block">Analytical Scenario</span>
    </article>`;
  }).join('');
  container.querySelectorAll('.se-scenario-card').forEach(card => {
    const code = card.dataset.scenario;
    const activate = () => {
      selectedScenarioCode = selectedScenarioCode === code ? null : code;
      updateScenarioSummary();
      renderScenarioCards(container);
      renderScenarioMatrix(document.getElementById('seMatrixBody'));
      renderScenarioCharts();
    };
    card.onclick = activate;
    card.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activate(); } };
  });
}

function renderScenarioMatrix(tbody) {
  if (!tbody) return;
  const list = getFilteredScenarios();
  tbody.innerHTML = list.map(s => {
    const hl = selectedScenarioCode && selectedScenarioCode !== s.code ? ' style="opacity:.55"' : '';
    const cells = SCENARIO_MATRIX_COLS.map(c =>
      `<td class="heat-cell ${buildScenarioHeatClass(s[c.key], c.type)}"${hl}>${s[c.key]}${c.type === 'prob' ? '%' : ''}</td>`
    ).join('');
    return `<tr${selectedScenarioCode === s.code ? ' class="se-row-selected"' : ''}>
      <td><strong>${s.code}</strong><div style="font-size:10px;color:var(--muted)">${s.title.slice(0,42)}…</div></td>${cells}</tr>`;
  }).join('');
}

function renderTransitionFlow(container) {
  container.innerHTML = scenarioTransitions.map(t => `
    <div class="se-transition">
      <span class="se-code">${t.from}</span>
      <i data-lucide="arrow-right" style="width:14px;height:14px;color:var(--muted)"></i>
      <span class="se-code">${t.to}</span>
      <span class="se-trigger">${t.trigger}</span>
    </div>`).join('');
}

function renderMonitorSignals(container) {
  container.innerHTML = monitorSignals.map(s => {
    const st = s.status === 'active' ? 'badge-live' : s.status === 'pending' ? 'badge-pending' : 'badge-risk';
    return `<div class="se-monitor-item">
      <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start">
        <strong style="font-size:12px">${s.item}</strong>
        <span class="badge ${st}">${s.status}</span>
      </div>
      <div style="font-size:11px;color:var(--muted);margin-top:4px">${s.note}</div>
      <div class="se-importance">${'●'.repeat(s.importance)}${'○'.repeat(5-s.importance)}</div>
    </div>`;
  }).join('');
}

function renderVerifiedFacts(container) {
  container.innerHTML = verifiedFacts.map(f => `
    <div class="card se-fact-card">
      <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start;margin-bottom:6px">
        ${factBadge(f.status)}
        <span style="font-size:10px;color:var(--muted)">${f.sourceLabel}</span>
      </div>
      <p style="font-size:13px;line-height:1.5">${f.statement}</p>
      <p style="font-size:11px;color:var(--muted);margin-top:6px"><strong>Implikasi:</strong> ${f.implication}</p>
    </div>`).join('');
}

function renderScenarioCharts() {
  const list = getFilteredScenarios();
  const labels = list.map(s => s.code);
  const destroy = id => { if (charts[id]) { charts[id].destroy(); delete charts[id]; } };

  destroy('seSeatRange');
  const ctx1 = document.getElementById('chartSeSeatRange');
  if (ctx1) {
    charts.seSeatRange = new Chart(ctx1, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Min PAS', data: list.map(s => s.pasSeatMin), backgroundColor: 'rgba(26,127,90,.5)' },
          { label: 'Max PAS', data: list.map(s => s.pasSeatMax), backgroundColor: '#1a7f5a' }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 10 } } }
    });
  }

  destroy('seThreeCorner');
  const ctx2 = document.getElementById('chartSeThreeCorner');
  if (ctx2) {
    charts.seThreeCorner = new Chart(ctx2, {
      type: 'bar',
      data: { labels, datasets: [{ label: 'Risiko 3 penjuru %', data: list.map(s => s.threeCornerRisk), backgroundColor: list.map(s => s.threeCornerRisk >= 70 ? '#ef4444' : '#f59e0b') }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 100 } } }
    });
  }

  destroy('seBenefit');
  const ctx3 = document.getElementById('chartSeBenefit');
  if (ctx3) {
    charts.seBenefit = new Chart(ctx3, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'PN cohesion', data: list.map(s => s.pnCohesion), backgroundColor: '#1e4fa8' },
          { label: 'PH-BN benefit', data: list.map(s => s.phBnBenefit), backgroundColor: '#c8102e' }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 100 } } }
    });
  }

  destroy('seRadar');
  const ctx4 = document.getElementById('chartSeRadar');
  const focus = selectedScenarioCode ? getScenarioByCode(selectedScenarioCode) : list[0];
  if (ctx4 && focus) {
    charts.seRadar = new Chart(ctx4, {
      type: 'radar',
      data: {
        labels: ['PN cohesion', 'Mesej', 'Undi Melayu', '3 penjuru', 'Akar umbi', 'Skor strategi'],
        datasets: [{
          label: focus.code + ' ' + focus.title.slice(0, 20),
          data: [focus.pnCohesion, focus.messageClarity, focus.malayVoteUnity, 100 - focus.threeCornerRisk, 100 - focus.grassrootsConflict, focus.strategicScore],
          borderColor: '#d4a853', backgroundColor: 'rgba(212,168,83,.15)', pointBackgroundColor: '#d4a853'
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { r: { beginAtZero: true, max: 100 } } }
    });
  }
}

function bindScenarioFilterTabs(root) {
  root.querySelectorAll('.se-filter-tab').forEach(tab => {
    tab.onclick = () => {
      scenarioFilter = tab.dataset.seFilter;
      selectedScenarioCode = scenarioFilter === 'all' ? null : scenarioFilter;
      root.querySelectorAll('.se-filter-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.seFilter === scenarioFilter);
        t.setAttribute('aria-selected', t.dataset.seFilter === scenarioFilter ? 'true' : 'false');
      });
      updateScenarioSummary();
      renderScenarioCards(document.getElementById('seCardsGrid'));
      renderScenarioMatrix(document.getElementById('seMatrixBody'));
      renderScenarioCharts();
    };
    tab.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); tab.click(); } };
  });
}

function renderScenarioEngine(root) {
  root.innerHTML = `
    <section id="scenario-engine" class="se-root" aria-labelledby="seTitle">
      <div class="sticky-sub">
        <h3 class="section-title" id="seTitle" style="margin:0">Scenario Engine
          <span>Bandingkan laluan paling realistik untuk PAS di Negeri Sembilan</span>
        </h3>
        <p style="font-size:13px;color:var(--muted);margin-top:8px;max-width:920px;line-height:1.55">
          Berdasarkan fakta semasa, risiko pakatan, dan potensi pecahan undi. Kedudukan PAS di Negeri Sembilan masih belum dimuktamadkan dari sudut operasi pilihan raya.
          Dashboard ini membezakan <strong>fakta sah</strong>, <strong>kekaburan operasi</strong>, dan <strong>senario analitik</strong>.
        </p>
      </div>

      <div class="alert-banner" style="margin-bottom:14px">
        <i data-lucide="info" style="width:16px;height:16px;color:var(--gold)"></i>
        <span>Anggaran awal ini untuk simulasi dashboard sahaja, bukan keputusan muktamad. Persefahaman setempat lebih realistik daripada kebangkitan rasmi Muafakat Nasional.</span>
      </div>

      <div class="grid-3 se-summary-banner" style="margin-bottom:16px">
        <div class="card se-summary-card"><div class="card-label">Laluan paling selamat</div><div id="seSummarySafe" style="font-size:12px;margin-top:8px;line-height:1.5">—</div></div>
        <div class="card se-summary-card se-summary-risk"><div class="card-label">Laluan paling berisiko</div><div id="seSummaryRisk" style="font-size:12px;margin-top:8px;line-height:1.5">—</div></div>
        <div class="card se-summary-card"><div class="card-label">Trigger terdekat</div><div id="seSummaryTrigger" style="font-size:12px;margin-top:8px;line-height:1.5">—</div></div>
      </div>

      <h4 class="section-title" style="font-size:16px">Verified Facts &amp; Operational Ambiguity</h4>
      <div class="se-facts-grid" id="seFactsGrid"></div>

      <div class="se-filter-tabs" role="tablist" aria-label="Tapis senario">
        ${SCENARIO_FILTER_TABS.map(t => `<button type="button" class="se-filter-tab chip${t.id==='all'?' active':''}" role="tab" data-se-filter="${t.id}" aria-selected="${t.id==='all'?'true':'false'}" tabindex="0">${t.label}</button>`).join('')}
      </div>

      <div class="se-cards-grid" id="seCardsGrid"></div>

      <h4 class="section-title" style="font-size:16px;margin-top:20px">Comparison Matrix</h4>
      <div class="table-wrap se-matrix-wrap">
        <table class="se-matrix"><thead><tr><th>Senario</th>${SCENARIO_MATRIX_COLS.map(c=>`<th>${c.label}</th>`).join('')}</tr></thead>
        <tbody id="seMatrixBody"></tbody></table>
      </div>

      <div class="grid-2" style="margin-top:16px">
        <div class="card chart-card"><div class="card-label">Julat kerusi PAS mengikut senario</div><div class="chart-box sm"><canvas id="chartSeSeatRange"></canvas></div></div>
        <div class="card chart-card"><div class="card-label">Risiko 3 penjuru (%)</div><div class="chart-box sm"><canvas id="chartSeThreeCorner"></canvas></div></div>
      </div>
      <div class="grid-2">
        <div class="card chart-card"><div class="card-label">Kohesi PN vs faedah PH-BN</div><div class="chart-box sm"><canvas id="chartSeBenefit"></canvas></div></div>
        <div class="card chart-card"><div class="card-label">Radar — senario dipilih</div><div class="chart-box sm"><canvas id="chartSeRadar"></canvas></div></div>
      </div>

      <div class="grid-2" style="margin-top:16px">
        <div class="card">
          <div class="card-label">Transition Flow</div>
          <div id="seTransitions" style="margin-top:10px"></div>
        </div>
        <div class="card">
          <div class="card-label">Monitoring Checklist</div>
          <div id="seMonitor" style="margin-top:10px"></div>
        </div>
      </div>

      <div class="card" style="margin-top:16px;border-left:3px solid var(--gold)">
        <div class="card-label">Why this matters for N9</div>
        <ul class="se-why-list">
          <li>Kejelasan pakatan penting — risiko terbesar ialah pertindihan kerusi dan kekeliruan mesej, bukan sekadar isu jenama.</li>
          <li>Undi Melayu boleh terpecah jika PAS dan Bersatu bertembung di DUN terpilih; pihak lawan berpotensi mendapat laluan lebih mudah.</li>
          <li>Kerusi campuran (marginal) sensitif kepada kekeliruan logo, calon, dan naratif split.</li>
          <li>Persefahaman setempat lebih realistik daripada naratif besar Muafakat Nasional 2.0 yang tiada pengesahan rasmi.</li>
          <li>Social comments dan isyarat lapangan (TikTok, FB, ceramah) penting untuk mengesahkan atau menolak senario S1–S5.</li>
        </ul>
      </div>
    </section>`;

  renderVerifiedFacts(document.getElementById('seFactsGrid'));
  bindScenarioFilterTabs(root);
  updateScenarioSummary();
  renderScenarioCards(document.getElementById('seCardsGrid'));
  renderScenarioMatrix(document.getElementById('seMatrixBody'));
  renderTransitionFlow(document.getElementById('seTransitions'));
  renderMonitorSignals(document.getElementById('seMonitor'));
  renderScenarioCharts();
}
"""
