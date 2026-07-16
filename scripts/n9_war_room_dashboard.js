// PRN N9 War Room Lite — Hari Ini (6 kerusi) + Checklist 10 modul

const WR_LITE_KEY = 'n9_hari_ini_done_v1';

function wrLiteLoadDone() {
  try { return JSON.parse(localStorage.getItem(WR_LITE_KEY) || '{}'); } catch (e) { return {}; }
}
function wrLiteSaveDone(map) {
  localStorage.setItem(WR_LITE_KEY, JSON.stringify(map));
}

function wrLiteToggle(id, checked) {
  const m = wrLiteLoadDone();
  m[id] = checked;
  wrLiteSaveDone(m);
  if (activeSection === 'war-room') renderSection();
}

function wrCopyWhatsApp() {
  const text = warRoomData.whatsapp_digest || '';
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => alert('Disalin! Paste ke WhatsApp group jentera.'));
  } else {
    prompt('Copy mesej ini:', text);
  }
}

function modStatusIcon(st) {
  return { ready: '✅', partial: '🟡', planned: '⬜' }[st] || '⬜';
}
function modStatusLabel(st) {
  return { ready: 'Siap', partial: 'Separuh', planned: 'Rancang' }[st] || st;
}

function renderWarRoom(root) {
  const wr = warRoomData;
  const hi = wr.hari_ini || { items: [], alerts: [], date: '' };
  const done = wrLiteLoadDone();
  const doneCount = hi.items.filter(i => done[i.id]).length;
  const hl = (dpiUpdates && dpiUpdates.highlights) || {};
  const topCula = (hl.topCulaPct || [])[0] || {};

  root.innerHTML = `
    <div class="sticky-sub">
      <h3 class="section-title" style="margin:0">Hari Ini — War Room
        <span>${hi.date || ''} · 6 kerusi kritikal · DPI ${hi.dpi_as_of || META.dpiAsOf || 'Dec 2025'}</span>
      </h3>
    </div>

    <div class="grid-4" style="margin-bottom:14px">
      <div class="card"><div class="card-label">Cula Tertinggi NS</div><div class="card-value">${topCula.code || '—'}</div><div class="card-sub">${topCula.culaPct || '—'}% · ${topCula.culaPasTotal || '—'} pengundi</div></div>
      <div class="card"><div class="card-label">Alert Jentera</div><div class="card-value" style="font-size:18px">${(hi.jentera_alerts || []).length}</div><div class="card-sub">BKC cula kritikal · 6 kerusi fokus</div></div>
      <div class="card"><div class="card-label">Cadangan MN</div><div class="card-value" style="font-size:18px">${(dpiUpdates.mnProposals || []).filter(r => r.calonMn).length}</div><div class="card-sub">PAS+BN perbincangan 10 Jun</div></div>
      <div class="card"><div class="card-label">Tindakan Hari Ini</div><div class="card-value">${doneCount}/${hi.items.length}</div><div class="card-sub">Tick + Copy WhatsApp</div></div>
    </div>

    ${(hi.jentera_alerts || []).length ? `
    <div class="alert-banner" style="margin-bottom:14px;background:rgba(245,158,11,.08);border-color:rgba(245,158,11,.35)">
      <i data-lucide="users" style="width:16px;height:16px;color:var(--warn)"></i>
      <span><strong>Jentera DPI:</strong> ${(hi.jentera_alerts || []).slice(0,3).map(a => `${a.kod_dun} — ${a.message}`).join(' · ')}</span>
    </div>` : ''}

    <div class="card wr-lite-modules" style="margin-bottom:16px;padding:14px 18px">
      <div class="card-label" style="margin-bottom:10px">10 Modul Kempen — status sistem</div>
      <div class="wr-module-grid">
        ${(wr.module_checklist || []).map(m => `
          <div class="wr-module-chip wr-mod-${m.status}" title="${m.note || ''}">
            <span>${modStatusIcon(m.status)}</span>
            <span class="wr-mod-label">${m.label}</span>
          </div>`).join('')}
      </div>
      <p style="font-size:10px;color:var(--muted);margin-top:10px">✅ siap · 🟡 separuh · ⬜ rancang — hover untuk nota</p>
    </div>

    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:14px">
      <div>
        <strong style="font-size:15px">Tindakan hari ini</strong>
        <span style="color:var(--muted);font-size:12px;margin-left:8px">${doneCount}/${hi.items.length} siap</span>
      </div>
      <button class="btn btn-primary" onclick="wrCopyWhatsApp()"><i data-lucide="message-circle"></i> Copy ke WhatsApp</button>
    </div>

    ${(hi.alerts || []).length ? `
    <div class="alert-banner" style="margin-bottom:14px;background:rgba(239,68,68,.1);border-color:rgba(239,68,68,.35)">
      <i data-lucide="alert-triangle" style="width:16px;height:16px;color:var(--neg)"></i>
      <span>${hi.alerts.map(a => `<strong>${a.kod_dun}</strong>: ${a.message}`).join(' · ')}</span>
    </div>` : ''}

    <div class="wr-hari-ini-list">
      ${hi.items.map(item => {
        const checked = !!done[item.id];
        const catCls = 'cat-' + (item.kategori_pas || 'not_priority');
        const alertBadge = item.alert_level === 'warning' || item.alert_level === 'critical'
          ? `<span class="badge badge-risk" style="margin-left:6px">${item.alert_level}</span>` : '';
        return `
        <label class="card wr-hari-row ${checked ? 'wr-row-done' : ''}">
          <input type="checkbox" ${checked ? 'checked' : ''} onchange="wrLiteToggle('${item.id}', this.checked)" />
          <div class="wr-hari-body">
            <div class="wr-hari-head">
              <strong>${item.kod_dun} ${item.kawasan}</strong>
              <span class="cat-pill ${catCls}">${item.kategori_label}</span>${alertBadge}
            </div>
            <p class="wr-hari-action">${item.action_text}</p>
            <div class="wr-hari-meta">
              PAS ${item.pas_win_prob}% · mention ${item.mentions} · neg ${item.neg_pct}%
              ${item.cula_pct != null ? ` · cula ${item.cula_pct}%` : ''}
              ${item.bkc_cula != null ? ` · BKC ${item.bkc_cula.toLocaleString()}` : ''}
              ${item.jentera_status ? ` · ${item.jentera_status}` : ''}
            </div>
            ${item.mn_calon ? `<div class="wr-hari-meta" style="color:var(--accent);margin-top:4px">MN: ${item.mn_calon}</div>` : ''}
          </div>
        </label>`;
      }).join('')}
    </div>

    <details class="card" style="margin-top:16px">
      <summary style="cursor:pointer;font-size:13px;font-weight:600;color:var(--muted)">Lihat semua tindakan (198) — optional</summary>
      <div id="wrFullFallback" style="margin-top:12px"></div>
    </details>`;

  const fb = root.querySelector('#wrFullFallback');
  if (fb && (wr.actions || []).length) {
    fb.innerHTML = `<div style="font-size:11px;color:var(--muted);margin-bottom:8px">Playbook penuh — untuk analisis sahaja</div>
      <div style="max-height:240px;overflow-y:auto;font-size:11px">${wr.actions.slice(0, 30).map(a =>
        `<div style="padding:4px 0;border-bottom:1px solid var(--border)">${a.kod_dun} · ${a.action_type}: ${a.action_text.slice(0, 80)}…</div>`
      ).join('')}${wr.actions.length > 30 ? `<div style="padding:8px;color:var(--muted)">+${wr.actions.length - 30} lagi…</div>` : ''}</div>`;
  }
}

function renderDrawerPlaybook(seat) {
  const hi = (warRoomData.hari_ini || {}).items || [];
  const item = hi.find(i => i.kod_dun === seat.code);
  const done = wrLiteLoadDone();
  if (!item) {
    return `<div class="card" style="margin-top:16px;background:var(--surface-2)">
      <div class="card-label">Hari Ini</div>
      <p style="font-size:12px;color:var(--muted);margin-top:6px">Kerusi bukan fokus hari ini — lihat tab Analitik.</p>
    </div>`;
  }
  const checked = !!done[item.id];
  return `<div class="card" style="margin-top:16px;background:var(--surface-2)">
    <div class="card-label">Tindakan Hari Ini · ${item.kategori_label}</div>
    <label style="display:flex;gap:10px;align-items:flex-start;margin-top:8px;cursor:pointer">
      <input type="checkbox" ${checked ? 'checked' : ''} onchange="wrLiteToggle('${item.id}', this.checked)" style="margin-top:4px" />
      <span style="font-size:13px;line-height:1.5">${item.action_text}</span>
    </label>
  </div>`;
}
