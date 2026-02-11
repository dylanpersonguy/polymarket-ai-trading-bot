/* ─── Polymarket Bot Dashboard ─ Interactive Frontend ────────── */
"use strict";

// ─── State ──────────────────────────────────────────────────────
let _configData = {};          // current config from API
let _configDirty = {};         // sections with unsaved edits
let _activeConfigTab = null;   // currently visible config section
let _modalConfirmCb = null;    // callback for confirm modal
let _charts = {};              // Chart.js instances

const $  = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ─── Smart DOM Update (skip if unchanged) ───────────────────────
function safeHTML(el, html) {
    if (!el) return;
    if (el.innerHTML === html) return;      // no-op if identical
    el.innerHTML = html;
}

// ─── Expanded Decision Cards State ─────────────────────────────
const _expandedDecisionKeys = new Set();   // "cycleId-marketId" keys

// ─── Helpers ────────────────────────────────────────────────────
const fmt  = (v, d=2) => Number(v||0).toFixed(d);
const fmtD = (v) => `$${fmt(v)}`;
const fmtP = (v) => `${fmt(v)}%`;
const pnlClass = (v) => v > 0.001 ? 'pnl-positive' : v < -0.001 ? 'pnl-negative' : 'pnl-zero';
const pillClass = (d) => {
    const dl = (d||'').toLowerCase();
    if (dl === 'trade' || dl === 'buy') return 'pill-trade';
    if (dl === 'no trade' || dl === 'sell') return 'pill-no-trade';
    if (dl === 'filled') return 'pill-filled';
    return 'pill-dry';
};
const shortDate = (iso) => {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleString('en-US', {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
};

async function apiFetch(url, opts) {
    try {
        const res = await fetch(url, opts);
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return await res.json();
    } catch (e) {
        console.error(`API ${url}:`, e);
        return null;
    }
}

// ─── Toast Notifications ────────────────────────────────────────
function showToast(message, type='info') {
    const container = $('#toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = {success:'✅',error:'❌',info:'ℹ️',warning:'⚠️'};
    toast.innerHTML = `<span class="toast-icon">${icons[type]||'ℹ️'}</span><span class="toast-msg">${message}</span>`;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('toast-show'));
    setTimeout(() => {
        toast.classList.remove('toast-show');
        toast.classList.add('toast-hide');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

// ─── Confirm Modal ──────────────────────────────────────────────
function showConfirmModal(title, message, onConfirm) {
    $('#modal-title').textContent = title;
    $('#modal-message').textContent = message;
    _modalConfirmCb = onConfirm;
    $('#modal-overlay').style.display = 'flex';
    const confirmBtn = $('#modal-confirm');
    // clone to remove old listeners
    const newBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
    newBtn.id = 'modal-confirm';
    newBtn.addEventListener('click', () => {
        closeModal();
        if (_modalConfirmCb) _modalConfirmCb();
    });
}
function closeModal() {
    $('#modal-overlay').style.display = 'none';
    _modalConfirmCb = null;
}

// ─── Table Search / Filter ──────────────────────────────────────
function filterTable(tbodyId, query) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    const q = query.toLowerCase().trim();
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
        if (row.querySelector('.empty-state')) { row.style.display = q ? 'none' : ''; return; }
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(q) ? '' : 'none';
    });
}

// ─── Data Export ────────────────────────────────────────────────
async function exportData(table) {
    showToast(`Exporting ${table}…`, 'info');
    const data = await apiFetch(`/api/export/${table}`);
    if (!data || !data.rows) { showToast('Export failed', 'error'); return; }
    if (data.rows.length === 0) { showToast('No data to export', 'warning'); return; }

    // Convert to CSV
    const keys = Object.keys(data.rows[0]);
    const csvRows = [keys.join(',')];
    for (const row of data.rows) {
        csvRows.push(keys.map(k => {
            let v = row[k] ?? '';
            if (typeof v === 'string' && (v.includes(',') || v.includes('"') || v.includes('\n'))) {
                v = `"${v.replace(/"/g, '""')}"`;
            }
            return v;
        }).join(','));
    }
    const blob = new Blob([csvRows.join('\n')], {type:'text/csv'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `${table}_export.csv`; a.click();
    URL.revokeObjectURL(url);
    showToast(`Exported ${data.rows.length} rows`, 'success');
}

// ─── Kill Switch ────────────────────────────────────────────────
function confirmKillSwitch(enable) {
    if (enable) {
        showConfirmModal('Activate Kill Switch',
            'This will immediately halt all trading. Are you sure?',
            toggleKillSwitch);
    } else {
        showConfirmModal('Deactivate Kill Switch',
            'Trading will resume on next cycle. Are you sure?',
            toggleKillSwitch);
    }
}

async function toggleKillSwitch() {
    const data = await apiFetch('/api/kill-switch', {method:'POST'});
    if (data) {
        showToast(data.message, data.kill_switch ? 'warning' : 'success');
        updateRisk();
        updateDrawdown();
    }
}

// ═══════════════════════════════════════════════════════════════
//  DATA REFRESH FUNCTIONS
// ═══════════════════════════════════════════════════════════════

// ─── Portfolio Cards ────────────────────────────────────────────
async function updatePortfolio() {
    const d = await apiFetch('/api/portfolio');
    if (!d) return;
    $('#bankroll').textContent   = fmtD(d.bankroll);
    $('#available-capital').textContent = `Available: ${fmtD(d.available_capital)}`;

    const pnlEl = $('#total-pnl');
    pnlEl.textContent = fmtD(d.total_pnl);
    pnlEl.className   = `card-value ${pnlClass(d.total_pnl)}`;
    const pnlSub = `Unrealized: ${fmtD(d.unrealized_pnl)}`;
    const pnlBest = d.best_pnl ? ` | Best: ${fmtD(d.best_pnl)}` : '';
    const pnlWorst = d.worst_pnl ? ` | Worst: ${fmtD(d.worst_pnl)}` : '';
    $('#unrealized-pnl').textContent = d.open_positions > 0
        ? pnlSub + pnlBest + pnlWorst
        : pnlSub;

    $('#open-positions').textContent = d.open_positions;
    $('#total-invested').textContent = `Invested: ${fmtD(d.total_invested)}`;

    $('#total-trades').textContent   = d.total_trades;
    $('#trade-breakdown').textContent = `Live: ${d.live_trades} | Paper: ${d.paper_trades}`;

    $('#avg-edge').textContent = fmtP(d.avg_edge * 100);
    $('#avg-evidence-quality').textContent = `Avg EQ: ${fmt(d.avg_evidence_quality, 3)}`;

    $('#today-trades').textContent = `${d.today_trades} trades`;
    $('#daily-volume').textContent = `Volume: ${fmtD(d.daily_volume)}`;

    // Mode badge
    const modeBadge = $('#mode-badge');
    if (d.live_trading_enabled && !d.dry_run) {
        modeBadge.textContent = 'LIVE'; modeBadge.className = 'badge badge-live';
    } else {
        modeBadge.textContent = 'PAPER MODE'; modeBadge.className = 'badge badge-paper';
    }
}

// ─── Risk Monitor ───────────────────────────────────────────────
async function updateRisk() {
    const d = await apiFetch('/api/risk');
    if (!d) return;

    // Daily exposure bar
    const dailyPct = d.current.daily_loss_pct;
    const dailyBar = $('#risk-bar-daily');
    dailyBar.style.width = `${Math.min(dailyPct,100)}%`;
    dailyBar.className = `risk-bar ${dailyPct > 80 ? 'danger' : dailyPct > 50 ? 'warning' : ''}`;
    $('#risk-daily-current').textContent = fmtD(d.current.daily_exposure);
    $('#risk-daily-limit').textContent   = fmtD(d.limits.max_daily_loss);

    // Positions bar
    const posPct = d.current.positions_pct;
    const posBar = $('#risk-bar-positions');
    posBar.style.width = `${Math.min(posPct,100)}%`;
    posBar.className = `risk-bar ${posPct > 80 ? 'danger' : posPct > 60 ? 'warning' : ''}`;
    $('#risk-pos-current').textContent = d.current.open_positions;
    $('#risk-pos-limit').textContent   = d.limits.max_open_positions;

    // Evidence quality bar (inverted — higher is better)
    const eqMin = d.forecasting.min_evidence_quality;
    const eqCur = d.current.avg_evidence_quality;
    const eqPct = eqMin > 0 ? Math.min((eqCur / eqMin) * 100, 100) : 0;
    const eqBar = $('#risk-bar-eq');
    eqBar.style.width = `${eqPct}%`;
    $('#risk-eq-current').textContent = fmt(eqCur, 3);
    $('#risk-eq-limit').textContent   = fmt(eqMin, 3);

    // Kill switch
    const ksBadge = $('#kill-switch-badge');
    const btnOn   = $('#btn-kill-on');
    const btnOff  = $('#btn-kill-off');
    if (d.kill_switch) {
        ksBadge.textContent = '🛑 KILL SWITCH ON'; ksBadge.className = 'badge badge-danger'; ksBadge.style.display = '';
        btnOn.style.display = 'none'; btnOff.style.display = '';
    } else {
        ksBadge.style.display = 'none';
        btnOn.style.display = ''; btnOff.style.display = 'none';
    }

    // Risk params pills
    const params = $('#risk-params');
    safeHTML(params, [
        ['Max Stake', fmtD(d.limits.max_stake_per_market)],
        ['Bankroll Frac', fmtP(d.limits.max_bankroll_fraction * 100)],
        ['Min Edge', fmtP(d.limits.min_edge * 100)],
        ['Kelly Frac', fmt(d.limits.kelly_fraction, 3)],
        ['Min Liquidity', fmtD(d.limits.min_liquidity)],
        ['Max Spread', fmtP(d.limits.max_spread * 100)],
        ['Slippage Tol', fmtP(d.execution.slippage_tolerance * 100)],
        ['LLM Model', d.forecasting.llm_model || '—'],
    ].map(([l,v]) => `<div class="risk-param"><div class="rp-label">${l}</div><div class="rp-value">${v}</div></div>`).join(''));
}

// ─── Positions Table ────────────────────────────────────────────
async function updatePositions() {
    const d = await apiFetch('/api/positions');
    if (!d) return;
    const tbody = $('#positions-body');
    if (!d.positions || d.positions.length === 0) {
        safeHTML(tbody, '<tr><td colspan="11" class="empty-state">No active positions</td></tr>');
        // Update summary strip
        const strip = $('#positions-summary');
        if (strip) safeHTML(strip, '');
        return;
    }

    // Positions summary strip
    const s = d.summary || {};
    const strip = $('#positions-summary');
    if (strip) {
        safeHTML(strip, `
            <div class="pnl-summary-strip">
                <span class="pnl-stat">📊 <strong>${s.count||0}</strong> positions</span>
                <span class="pnl-stat ${pnlClass(s.total_pnl)}">P&L: <strong>${fmtD(s.total_pnl)}</strong> (${fmtP(s.pnl_pct)})</span>
                <span class="pnl-stat">Invested: <strong>${fmtD(s.total_invested)}</strong></span>
                <span class="pnl-stat pnl-positive">✅ ${s.winners||0}W</span>
                <span class="pnl-stat pnl-negative">❌ ${s.losers||0}L</span>
                <span class="pnl-stat pnl-zero">➖ ${s.flat||0}F</span>
            </div>
        `);
    }

    safeHTML(tbody, d.positions.map(p => {
        const pnl = p.pnl || 0;
        const pnlPct = p.pnl_pct || 0;
        const priceChange = p.price_change || 0;
        const priceChangePct = p.price_change_pct || 0;
        const arrow = priceChange > 0.001 ? '▲' : priceChange < -0.001 ? '▼' : '─';
        const arrowClass = priceChange > 0.001 ? 'price-up' : priceChange < -0.001 ? 'price-down' : 'price-flat';
        const hoursHeld = p.hours_held || 0;
        const timeLabel = hoursHeld >= 24 ? `${(hoursHeld/24).toFixed(1)}d` : `${hoursHeld.toFixed(1)}h`;

        return `<tr class="position-row ${pnlClass(pnl)}">
            <td title="${p.market_id}">${(p.question||p.market_id||'').substring(0,50)}</td>
            <td>${p.market_type||'—'}</td>
            <td><span class="pill ${p.direction==='BUY_YES'||p.direction==='BUY'?'pill-buy':'pill-sell'}">${p.direction||'—'}</span></td>
            <td>${fmt(p.entry_price,3)}</td>
            <td>
                <span class="live-price">${fmt(p.current_price,3)}</span>
                <span class="price-arrow ${arrowClass}">${arrow}</span>
            </td>
            <td>${fmt(p.size,1)}</td>
            <td>${fmtD(p.stake_usd)}</td>
            <td class="${pnlClass(pnl)}">
                <span class="pnl-value">${fmtD(pnl)}</span>
            </td>
            <td class="${pnlClass(pnlPct)}">
                <span class="pnl-badge ${pnl > 0 ? 'pnl-badge-pos' : pnl < 0 ? 'pnl-badge-neg' : 'pnl-badge-flat'}">${fmtP(pnlPct)}</span>
            </td>
            <td class="${arrowClass}">
                ${fmtP(priceChangePct)}
            </td>
            <td title="${p.opened_at||''}">${timeLabel}</td>
        </tr>`;
    }).join(''));
}

// ─── Forecasts Table ────────────────────────────────────────────
async function updateForecasts() {
    const d = await apiFetch('/api/forecasts');
    if (!d) return;
    const tbody = $('#forecasts-body');
    if (!d.forecasts || d.forecasts.length === 0) {
        safeHTML(tbody, '<tr><td colspan="10" class="empty-state">No forecasts yet</td></tr>');
        return;
    }
    safeHTML(tbody, d.forecasts.map(f => `<tr>
        <td title="${f.question||''}">${(f.question||f.market_id||'').substring(0,50)}</td>
        <td>${f.market_type||'—'}</td>
        <td>${fmtP((f.implied_probability||0)*100)}</td>
        <td>${fmtP((f.model_probability||0)*100)}</td>
        <td class="${pnlClass(f.edge)}">${fmtP((f.edge||0)*100)}</td>
        <td>${fmt(f.evidence_quality,3)}</td>
        <td>${f.num_sources||f.evidence_count||0}</td>
        <td>${f.confidence_level||'—'}</td>
        <td><span class="pill ${pillClass(f.decision)}">${f.decision||'—'}</span></td>
        <td>${shortDate(f.created_at)}</td>
    </tr>`).join(''));
}

// ─── Trades Table ───────────────────────────────────────────────
async function updateTrades() {
    const d = await apiFetch('/api/trades');
    if (!d) return;
    const tbody = $('#trades-body');
    if (!d.trades || d.trades.length === 0) {
        safeHTML(tbody, '<tr><td colspan="9" class="empty-state">No trades yet</td></tr>');
        return;
    }
    safeHTML(tbody, d.trades.map(t => `<tr>
        <td title="${t.question||''}">${(t.question||t.market_id||'').substring(0,50)}</td>
        <td>${t.market_type||'—'}</td>
        <td><span class="pill ${t.side==='BUY'?'pill-buy':'pill-sell'}">${t.side||'—'}</span></td>
        <td>${fmt(t.price,3)}</td>
        <td>${fmt(t.size,1)}</td>
        <td>${fmtD(t.stake_usd)}</td>
        <td><span class="pill ${pillClass(t.status)}">${t.status||'—'}</span></td>
        <td>${t.dry_run ? '🧪 Paper' : '💰 Live'}</td>
        <td>${shortDate(t.created_at)}</td>
    </tr>`).join(''));
}

// ─── Audit Trail ────────────────────────────────────────────────
async function updateAudit() {
    const d = await apiFetch('/api/audit');
    if (!d) return;
    const tbody = $('#audit-body');
    if (!d.entries || d.entries.length === 0) {
        safeHTML(tbody, '<tr><td colspan="7" class="empty-state">No audit entries</td></tr>');
        return;
    }
    safeHTML(tbody, d.entries.map(e => `<tr>
        <td style="font-family:var(--font-mono);font-size:0.72rem;">${(e.id||'').substring(0,8)}</td>
        <td>${(e.market_id||'').substring(0,20)}</td>
        <td><span class="pill ${pillClass(e.decision)}">${e.decision||'—'}</span></td>
        <td>${e.stage||'—'}</td>
        <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${e.details||''}">${(e.details||'—').substring(0,60)}</td>
        <td>${e.integrity_hash ? '✅' : '—'}</td>
        <td>${shortDate(e.timestamp)}</td>
    </tr>`).join(''));
}

// ─── Alerts ─────────────────────────────────────────────────────
async function updateAlerts() {
    const d = await apiFetch('/api/alerts');
    if (!d) return;
    const tbody = $('#alerts-body');
    if (!d.alerts || d.alerts.length === 0) {
        safeHTML(tbody, '<tr><td colspan="4" class="empty-state">No alerts</td></tr>');
        return;
    }
    const levelClass = (l) => {
        const ll = (l||'').toLowerCase();
        return ll === 'critical' || ll === 'error' ? 'pnl-negative' :
               ll === 'warning' ? 'accent-orange' : '';
    };
    safeHTML(tbody, d.alerts.map(a => `<tr>
        <td class="${levelClass(a.level)}" style="font-weight:700;text-transform:uppercase">${a.level||'info'}</td>
        <td>${a.channel||'—'}</td>
        <td>${a.message||'—'}</td>
        <td>${shortDate(a.timestamp || a.created_at)}</td>
    </tr>`).join(''));
}

// ─── Pipeline Candidates ────────────────────────────────────────
async function updateCandidates() {
    const d = await apiFetch('/api/candidates');
    if (!d) return;
    const tbody = $('#candidates-body');
    if (!d.candidates || d.candidates.length === 0) {
        safeHTML(tbody, '<tr><td colspan="13" class="empty-state">No candidates processed yet</td></tr>');
        return;
    }
    safeHTML(tbody, d.candidates.map(c => {
        const decClass = (c.decision||'').toUpperCase() === 'TRADE' ? 'pill-trade' :
                         (c.decision||'').toUpperCase() === 'NO TRADE' ? 'pill-no-trade' : 'pill-dry';
        return `<tr>
            <td>${c.cycle_id||'—'}</td>
            <td title="${c.question||''}">${(c.question||c.market_id||'').substring(0,45)}</td>
            <td>${c.market_type||'—'}</td>
            <td>${fmtP((c.implied_prob||0)*100)}</td>
            <td>${fmtP((c.model_prob||0)*100)}</td>
            <td class="${pnlClass(c.edge)}">${fmtP((c.edge||0)*100)}</td>
            <td>${fmt(c.evidence_quality,3)}</td>
            <td>${c.num_sources||0}</td>
            <td>${c.confidence||'—'}</td>
            <td><span class="pill ${decClass}">${c.decision||'—'}</span></td>
            <td>${c.stake_usd ? fmtD(c.stake_usd) : '—'}</td>
            <td title="${c.decision_reasons||''}" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${(c.decision_reasons||'—').substring(0,40)}</td>
            <td>${shortDate(c.created_at)}</td>
        </tr>`;
    }).join(''));
}

// ─── Engine & Drawdown Cards ────────────────────────────────────
async function updateEngineStatus() {
    const d = await apiFetch('/api/engine-status');
    if (!d) return;
    const statusEl = $('#engine-status');
    statusEl.textContent = d.running ? 'RUNNING' : 'OFF';
    statusEl.className   = `card-value ${d.running ? 'pnl-positive' : 'pnl-zero'}`;
    $('#engine-cycles').textContent = `Cycles: ${d.cycles || 0}`;

    const engineBadge = $('#engine-badge');
    if (d.running) {
        engineBadge.textContent = '🟢 ENGINE ON'; engineBadge.className = 'badge badge-ok'; engineBadge.style.display = '';
    } else {
        engineBadge.textContent = '⚫ ENGINE OFF'; engineBadge.className = 'badge badge-paper'; engineBadge.style.display = '';
    }

    // Show last cycle info if available
    if (d.last_cycle) {
        const lc = d.last_cycle;
        $('#engine-cycles').textContent =
            `Cycles: ${d.cycles || 0} | Last: ${lc.markets_scanned||0} scanned, ${lc.edges_found||0} edges, ${lc.trades_executed||0} trades (${lc.duration_secs||0}s)`;
    }
}

async function updateDrawdown() {
    const d = await apiFetch('/api/drawdown');
    if (!d) return;
    $('#drawdown-pct').textContent = fmtP(d.drawdown_pct * 100);
    $('#drawdown-detail').textContent = `Peak: ${fmtD(d.peak_equity)} | Current: ${fmtD(d.current_equity)}`;

    const heat = d.heat_level || 0;
    const heatEl = $('#heat-level');
    if (heat === 0) { heatEl.textContent = '🟢 Cool'; }
    else if (heat === 1) { heatEl.textContent = '🟡 Warm'; }
    else if (heat === 2) { heatEl.textContent = '🟠 Hot'; }
    else { heatEl.textContent = '🔴 Critical'; }

    $('#kelly-mult').textContent = `Kelly multiplier: ${fmt(d.kelly_multiplier, 2)}x`;

    const ksStatus = $('#kill-switch-status');
    ksStatus.textContent = d.is_killed ? '🛑 ACTIVE' : 'OFF';
    ksStatus.className = `card-value ${d.is_killed ? 'pnl-negative' : 'pnl-zero'}`;
}

// ─── Charts ─────────────────────────────────────────────────────
const chartColors = {
    blue:   'rgba(76,141,255,0.8)',
    green:  'rgba(0,214,143,0.8)',
    orange: 'rgba(255,159,67,0.8)',
    purple: 'rgba(168,85,247,0.8)',
    red:    'rgba(255,77,106,0.8)',
    teal:   'rgba(20,184,166,0.8)',
    pink:   'rgba(244,114,182,0.8)',
    yellow: 'rgba(251,191,36,0.8)',
};
const chartBg = {
    blue:   'rgba(76,141,255,0.15)',
    green:  'rgba(0,214,143,0.15)',
    orange: 'rgba(255,159,67,0.15)',
    purple: 'rgba(168,85,247,0.15)',
};
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {legend:{labels:{color:'#8b8fa3',font:{size:11}}}},
    scales: {
        x: {ticks:{color:'#5a5e72',font:{size:10}}, grid:{color:'rgba(42,45,58,0.5)'}},
        y: {ticks:{color:'#5a5e72',font:{size:10}}, grid:{color:'rgba(42,45,58,0.5)'}},
    },
};

async function updateCharts() {
    const [perf, types] = await Promise.all([
        apiFetch('/api/performance'),
        apiFetch('/api/market-types'),
    ]);

    // ── Daily Activity Chart
    if (perf && perf.daily_forecasts) {
        const days = perf.daily_forecasts.reverse();
        const labels = days.map(d => d.day);
        if (_charts.daily) _charts.daily.destroy();
        _charts.daily = new Chart($('#chart-daily-activity'), {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {label:'Forecasts', data:days.map(d=>d.forecasts), backgroundColor:chartBg.blue, borderColor:chartColors.blue, borderWidth:1},
                    {label:'Trades',    data:days.map(d=>d.trades),    backgroundColor:chartBg.green, borderColor:chartColors.green, borderWidth:1},
                ],
            },
            options: {...chartDefaults},
        });
    }

    // ── Edge & EQ Chart
    if (perf && perf.daily_forecasts) {
        const days = perf.daily_forecasts;
        const labels = days.map(d => d.day);
        if (_charts.edgeEq) _charts.edgeEq.destroy();
        _charts.edgeEq = new Chart($('#chart-edge-eq'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {label:'Avg Edge',data:days.map(d=>(d.avg_edge||0)*100), borderColor:chartColors.green, backgroundColor:chartBg.green, fill:true, tension:0.3},
                    {label:'Avg EQ',  data:days.map(d=>d.avg_eq||0),        borderColor:chartColors.purple,backgroundColor:chartBg.purple,fill:true, tension:0.3, yAxisID:'y1'},
                ],
            },
            options: {
                ...chartDefaults,
                scales: {
                    ...chartDefaults.scales,
                    y1: {position:'right', ticks:{color:'#5a5e72',font:{size:10}}, grid:{display:false}},
                },
            },
        });
    }

    // ── Market Types Doughnut
    if (types && types.market_types && types.market_types.length > 0) {
        const labels = types.market_types.map(t => t.market_type || 'Unknown');
        const data   = types.market_types.map(t => t.count);
        const colors = [chartColors.blue, chartColors.green, chartColors.orange, chartColors.purple, chartColors.teal, chartColors.pink, chartColors.yellow, chartColors.red];
        if (_charts.types) _charts.types.destroy();
        _charts.types = new Chart($('#chart-market-types'), {
            type: 'doughnut',
            data: {labels, datasets:[{data, backgroundColor:colors.slice(0,data.length), borderWidth:0}]},
            options: {responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'bottom',labels:{color:'#8b8fa3',font:{size:10}}}}},
        });
    }
}

// ─── Equity Curve ───────────────────────────────────────────────
async function updateEquityCurve() {
    const trades = await apiFetch('/api/trades');
    if (!trades || !trades.trades || trades.trades.length === 0) return;

    // Build cumulative P&L from trade history
    const sorted = [...trades.trades].reverse(); // oldest first
    let cumPnl = 0;
    const labels = [];
    const data = [];
    sorted.forEach((t, i) => {
        // Use actual PnL if available, otherwise estimate from price vs 0.5
        const price = t.price || 0.5;
        const stake = t.stake_usd || 0;
        // For paper trades: estimate P&L based on price deviation from fair value
        const pnl = (t.status === 'FILLED' || t.status === 'SIMULATED')
            ? (1.0 - price) * (t.size || 0) * 0.1  // simplified unrealized
            : 0;
        cumPnl += pnl;
        labels.push(shortDate(t.created_at));
        data.push(parseFloat(cumPnl.toFixed(2)));
    });

    if (_charts.equity) _charts.equity.destroy();
    _charts.equity = new Chart($('#chart-equity-curve'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Cumulative P&L ($)',
                data,
                borderColor: chartColors.green,
                backgroundColor: chartBg.green,
                fill: true,
                tension: 0.3,
                pointRadius: 2,
            }],
        },
        options: {
            ...chartDefaults,
            plugins: {
                ...chartDefaults.plugins,
                tooltip: {callbacks:{label: ctx => `P&L: ${fmtD(ctx.raw)}`}},
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════════
//  EDITABLE CONFIGURATION
// ═══════════════════════════════════════════════════════════════

const CONFIG_SECTION_LABELS = {
    scanning: '🔍 Scanning',
    research: '📚 Research',
    forecasting: '🎯 Forecasting',
    ensemble: '🧩 Ensemble',
    risk: '⚠️ Risk',
    drawdown: '📉 Drawdown',
    portfolio: '💼 Portfolio',
    timeline: '⏱️ Timeline',
    microstructure: '🔬 Microstructure',
    execution: '⚡ Execution',
    cache: '💾 Cache',
    engine: '🏗️ Engine',
    alerts: '🔔 Alerts',
    observability: '📊 Observability',
};

async function updateConfig() {
    const data = await apiFetch('/api/config');
    if (!data) return;

    // Skip re-render if user has unsaved edits (don't blow away their changes)
    if (Object.keys(_configDirty).length > 0) return;

    // Skip re-render if data hasn't changed
    if (JSON.stringify(data) === JSON.stringify(_configData)) return;

    _configData = data;
    renderConfigTabs();
    renderConfigSection(_activeConfigTab || Object.keys(data)[0]);
}

function renderConfigTabs() {
    const container = $('#config-tabs');
    if (!container) return;
    const sections = Object.keys(_configData);
    container.innerHTML = sections.map(section => {
        const label = CONFIG_SECTION_LABELS[section] || section;
        const active = section === _activeConfigTab ? 'config-tab-active' : '';
        return `<button class="config-tab ${active}" data-section="${section}" onclick="switchConfigTab('${section}')">${label}</button>`;
    }).join('');
}

function switchConfigTab(section) {
    _activeConfigTab = section;
    // Update active tab styling
    $$('.config-tab').forEach(t => t.classList.toggle('config-tab-active', t.dataset.section === section));
    renderConfigSection(section);
}

function renderConfigSection(section) {
    _activeConfigTab = section;
    const container = $('#config-grid');
    if (!container || !_configData[section]) return;

    const fields = _configData[section];
    let html = `<div class="config-editor">`;
    html += `<div class="config-section-header">
        <h3>${CONFIG_SECTION_LABELS[section] || section}</h3>
        <button class="btn btn-save btn-sm" onclick="saveSection('${section}')">💾 Save ${section}</button>
    </div>`;
    html += `<div class="config-fields">`;

    for (const [key, value] of Object.entries(fields)) {
        html += renderConfigField(section, key, value);
    }

    html += `</div></div>`;
    container.innerHTML = html;
}

function renderConfigField(section, key, value) {
    const id = `cfg-${section}-${key}`;
    const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    let input;

    if (typeof value === 'boolean') {
        input = `<label class="toggle-switch">
            <input type="checkbox" id="${id}" ${value ? 'checked' : ''} onchange="markDirty('${section}','${key}',this.checked)">
            <span class="toggle-slider"></span>
            <span class="toggle-label">${value ? 'On' : 'Off'}</span>
        </label>`;
    } else if (typeof value === 'number') {
        const step = Number.isInteger(value) ? '1' : '0.001';
        input = `<input type="number" id="${id}" class="config-input" value="${value}" step="${step}"
                   onchange="markDirty('${section}','${key}',parseFloat(this.value))">`;
    } else if (Array.isArray(value)) {
        input = `<input type="text" id="${id}" class="config-input config-input-wide" value="${value.join(', ')}"
                   placeholder="comma-separated values"
                   onchange="markDirty('${section}','${key}',this.value.split(',').map(s=>s.trim()).filter(Boolean))">`;
    } else if (typeof value === 'object' && value !== null) {
        input = `<textarea id="${id}" class="config-input config-textarea" rows="3"
                   onchange="markDirty('${section}','${key}',JSON.parse(this.value))">${JSON.stringify(value, null, 2)}</textarea>`;
    } else {
        input = `<input type="text" id="${id}" class="config-input config-input-wide" value="${value ?? ''}"
                   onchange="markDirty('${section}','${key}',this.value)">`;
    }

    return `<div class="config-field-row">
        <label class="config-field-label" for="${id}">${label}</label>
        <div class="config-field-input">${input}</div>
    </div>`;
}

function markDirty(section, key, value) {
    if (!_configDirty[section]) _configDirty[section] = {};
    _configDirty[section][key] = value;

    // Update toggle label if boolean
    const el = document.getElementById(`cfg-${section}-${key}`);
    if (el && el.type === 'checkbox') {
        const label = el.parentElement.querySelector('.toggle-label');
        if (label) label.textContent = el.checked ? 'On' : 'Off';
    }

    // Visual indicator that section has unsaved changes
    const tab = document.querySelector(`.config-tab[data-section="${section}"]`);
    if (tab && !tab.classList.contains('config-tab-dirty')) {
        tab.classList.add('config-tab-dirty');
    }
}

async function saveSection(section) {
    const changes = _configDirty[section];
    if (!changes || Object.keys(changes).length === 0) {
        showToast(`No changes in ${section}`, 'info');
        return;
    }
    showToast(`Saving ${section}…`, 'info');
    const result = await apiFetch('/api/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({[section]: changes}),
    });
    if (result && result.ok) {
        showToast(`${section} saved successfully!`, 'success');
        delete _configDirty[section];
        const tab = document.querySelector(`.config-tab[data-section="${section}"]`);
        if (tab) tab.classList.remove('config-tab-dirty');
        // Reload full config to reflect changes
        updateConfig();
    } else {
        showToast(`Failed to save: ${result?.error || 'Unknown error'}`, 'error');
    }
}

async function saveAllConfig() {
    const sections = Object.keys(_configDirty);
    if (sections.length === 0) {
        showToast('No unsaved changes', 'info');
        return;
    }
    showToast(`Saving ${sections.length} section(s)…`, 'info');
    const result = await apiFetch('/api/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(_configDirty),
    });
    if (result && result.ok) {
        showToast('All changes saved!', 'success');
        _configDirty = {};
        $$('.config-tab-dirty').forEach(t => t.classList.remove('config-tab-dirty'));
        updateConfig();
    } else {
        showToast(`Save failed: ${result?.error || 'Unknown error'}`, 'error');
    }
}

function confirmResetConfig() {
    showConfirmModal(
        'Reset Configuration',
        'This will reset ALL settings to their defaults. Your config.yaml will be deleted. This cannot be undone.',
        resetConfig
    );
}

async function resetConfig() {
    const result = await apiFetch('/api/config/reset', {method: 'POST'});
    if (result && result.ok) {
        showToast('Configuration reset to defaults', 'success');
        _configDirty = {};
        updateConfig();
        // Reload risk/drawdown since they depend on config
        updateRisk();
        updateDrawdown();
        updateEngineStatus();
    } else {
        showToast(`Reset failed: ${result?.error || 'Unknown error'}`, 'error');
    }
}

// ═══════════════════════════════════════════════════════════════
//  DECISION INTELLIGENCE LOG
// ═══════════════════════════════════════════════════════════════

let _decisionExpanded = false;

function _decisionKey(entry) {
    return `${entry.cycle_id||0}-${entry.market_id||''}`;
}

async function updateDecisionLog() {
    const cycleFilter = $('#decision-cycle-filter');
    const cycleVal = cycleFilter ? cycleFilter.value : '';
    const url = cycleVal ? `/api/decision-log?cycle=${cycleVal}` : '/api/decision-log?limit=30';
    const d = await apiFetch(url);
    if (!d) return;

    // Populate cycle selector (preserve current selection)
    if (d.cycles && d.cycles.length > 0 && cycleFilter) {
        const cur = cycleFilter.value;
        const newOpts = '<option value="">All Cycles</option>' +
            d.cycles.map(c => `<option value="${c}" ${String(c)===cur?'selected':''}>Cycle ${c}</option>`).join('');
        safeHTML(cycleFilter, newOpts);
    }

    const container = $('#decision-log-container');
    if (!d.entries || d.entries.length === 0) {
        safeHTML(container, '<div class="empty-state" style="padding:40px 0;">No decision data yet — run an engine cycle to see how the bot makes decisions.</div>');
        return;
    }

    // Build new HTML and check if data actually changed
    const newHTML = d.entries.map((e, idx) => renderDecisionCard(e, idx)).join('');

    // Compare stripped content to decide if DOM needs updating
    // (we strip display:none/block and expand icons since those are UI state)
    const normalize = (h) => h.replace(/style="display:(none|block);?"/g, '').replace(/▶|▼/g, '');
    if (normalize(container.innerHTML) === normalize(newHTML)) {
        return;  // data unchanged, keep current DOM state (expanded cards, etc.)
    }

    // Data changed — save expanded state, rebuild, restore
    _saveExpandedState();
    container.innerHTML = newHTML;
    _restoreExpandedState(d.entries);
    filterDecisionCards();
}

function _saveExpandedState() {
    // Persist which cards are currently expanded (don't clear the set,
    // user-toggled state carries across refreshes)
    document.querySelectorAll('.decision-card').forEach(card => {
        const key = card.dataset.decisionKey;
        if (!key) return;
        const detail = card.querySelector('.dc-detail');
        if (detail && detail.style.display !== 'none') {
            _expandedDecisionKeys.add(key);
        } else {
            _expandedDecisionKeys.delete(key);
        }
    });
}

function _restoreExpandedState(entries) {
    entries.forEach((entry, idx) => {
        const key = _decisionKey(entry);
        if (_expandedDecisionKeys.has(key) || _decisionExpanded) {
            const detail = document.getElementById(`dc-detail-${idx}`);
            const icon = document.getElementById(`dc-expand-${idx}`);
            if (detail) detail.style.display = 'block';
            if (icon) icon.textContent = '▼';
        }
    });
}

function renderDecisionCard(entry, idx) {
    const decision = (entry.decision || 'SKIP').toUpperCase();
    const decClass = decision === 'TRADE' ? 'dc-trade' :
                     decision === 'NO TRADE' ? 'dc-no-trade' : 'dc-skip';
    const decIcon = decision === 'TRADE' ? '✅' :
                    decision === 'NO TRADE' ? '❌' : '⏭️';

    const edgeVal = (entry.edge || 0) * 100;
    const edgeSign = edgeVal >= 0 ? '+' : '';
    const edgeClass = edgeVal > 0 ? 'pnl-positive' : edgeVal < 0 ? 'pnl-negative' : 'pnl-zero';

    // Pipeline stages dots
    const stageDots = (entry.stages || []).map(s => {
        const sc = s.status === 'passed' || s.status === 'executed' ? 'stage-pass' :
                   s.status === 'blocked' ? 'stage-block' : 'stage-skip';
        return `<span class="stage-dot ${sc}" title="${s.icon} ${s.name}: ${s.status}">${s.icon}</span>`;
    }).join('');

    // Grade badge
    const grade = entry.di_grade || '—';
    const gradeColorClass = grade.startsWith('A') ? 'grade-a' :
                            grade.startsWith('B') ? 'grade-b' :
                            grade.startsWith('C') ? 'grade-c' :
                            grade.startsWith('D') ? 'grade-d' : 'grade-f';

    // Category badge
    const catBadge = entry.category
        ? `<span class="dc-category-badge" title="Category: ${entry.category}">${categoryIcon(entry.category)} ${entry.category}</span>`
        : '';

    // Mini probability bar
    const implPct = ((entry.implied_prob || 0) * 100).toFixed(0);
    const modPct = ((entry.model_prob || 0) * 100).toFixed(0);
    const miniProbBar = `<div class="dc-mini-prob" title="Market ${implPct}% → Model ${modPct}%">
        <div class="dc-mini-prob-track">
            <div class="dc-mini-prob-implied" style="width:${implPct}%"></div>
            <div class="dc-mini-prob-model" style="width:${modPct}%"></div>
        </div>
        <span class="dc-mini-prob-label">${implPct}→${modPct}%</span>
    </div>`;

    // Confidence indicator
    const conf = (entry.confidence || '').toLowerCase();
    const confDot = conf === 'high' ? 'conf-high' : conf === 'medium' ? 'conf-med' : conf === 'low' ? 'conf-low' : 'conf-none';
    const confLabel = conf || '—';

    // Collapsed summary — enhanced
    const summary = `
    <div class="dc-header" onclick="toggleDecisionDetail(${idx})">
        <div class="dc-header-left">
            <span class="dc-grade-badge ${gradeColorClass}" title="Decision Intelligence Score: ${entry.di_score || 0}/100">${grade}</span>
            <span class="dc-decision-badge ${decClass}">${decIcon} ${decision}</span>
            <span class="dc-question" title="${entry.question || ''}">${escHtml((entry.question || entry.market_id || '').substring(0, 80))}</span>
        </div>
        <div class="dc-header-right">
            ${catBadge}
            <span class="dc-type-badge">${entry.market_type || '—'}</span>
            <div class="dc-stages-mini">${stageDots}</div>
            ${miniProbBar}
            <span class="dc-metric"><span class="dc-metric-label">Edge</span> <span class="${edgeClass}">${edgeSign}${edgeVal.toFixed(1)}%</span></span>
            <span class="dc-metric"><span class="dc-metric-label">EQ</span> ${fmt(entry.evidence_quality, 2)}</span>
            <div class="dc-conf-indicator ${confDot}" title="Confidence: ${confLabel}"><span class="dc-conf-dot"></span><span class="dc-conf-text">${confLabel}</span></div>
            <span class="dc-time">${shortDate(entry.created_at)}</span>
            <span class="dc-expand-icon" id="dc-expand-${idx}">▶</span>
        </div>
    </div>`;

    // Expanded detail
    const detail = renderDecisionDetail(entry, idx);

    const stableKey = _decisionKey(entry);
    return `<div class="decision-card ${decClass}" data-decision="${decision}" data-idx="${idx}" data-decision-key="${stableKey}">
        ${summary}
        <div class="dc-detail" id="dc-detail-${idx}" style="display:none;">${detail}</div>
    </div>`;
}

function categoryIcon(cat) {
    const icons = {
        MACRO: '📈', ELECTION: '🗳️', CRYPTO: '₿', CORPORATE: '🏢',
        LEGAL: '⚖️', SCIENCE: '🔬', TECH: '💻', SPORTS: '🏆',
        WEATHER: '🌦️', GEOPOLITICS: '🌍', SOCIAL_MEDIA: '📱', UNKNOWN: '❓'
    };
    return icons[(cat || '').toUpperCase()] || '❓';
}

function renderDecisionDetail(entry, idx) {
    const stages = entry.stages || [];
    const decision = (entry.decision || 'SKIP').toUpperCase();
    const decClass = decision === 'TRADE' ? 'dc-trade' :
                     decision === 'NO TRADE' ? 'dc-no-trade' : 'dc-skip';

    // ── Decision Summary Panel ──
    const grade = entry.di_grade || '—';
    const diScore = entry.di_score || 0;
    const gradeColorClass = grade.startsWith('A') ? 'grade-a' :
                            grade.startsWith('B') ? 'grade-b' :
                            grade.startsWith('C') ? 'grade-c' :
                            grade.startsWith('D') ? 'grade-d' : 'grade-f';

    const edgeVal = (entry.edge || 0) * 100;
    const implPct = ((entry.implied_prob || 0) * 100).toFixed(1);
    const modPct = ((entry.model_prob || 0) * 100).toFixed(1);
    const eq = entry.evidence_quality || 0;
    const researchability = entry.researchability || 0;
    const conf = (entry.confidence || '—').toLowerCase();
    const confPercent = conf === 'high' ? 85 : conf === 'medium' ? 55 : conf === 'low' ? 25 : 0;
    const completeness = entry.pipeline_completeness || 0;

    // Verdict text
    const verdictIcon = decision === 'TRADE' ? '🟢' : decision === 'NO TRADE' ? '🔴' : '🟡';
    const verdictText = decision === 'TRADE'
        ? `Trade executed with ${edgeVal >= 0 ? '+' : ''}${edgeVal.toFixed(1)}% edge and ${conf} confidence`
        : decision === 'NO TRADE'
        ? `Trade rejected — insufficient edge or failed risk checks`
        : `Market skipped during pipeline evaluation`;

    // Reasons
    const reasonsList = (entry.decision_reasons_list || []).map(r =>
        `<li>${escHtml(r)}</li>`
    ).join('');

    let html = '';

    // ═══ DECISION SUMMARY PANEL ═══
    html += `<div class="dc-summary-panel ${decClass}">
        <div class="dc-summary-header">
            <div class="dc-summary-verdict">
                <span class="dc-verdict-icon">${verdictIcon}</span>
                <div class="dc-verdict-text-wrap">
                    <div class="dc-verdict-label">DECISION VERDICT</div>
                    <div class="dc-verdict-text">${escHtml(verdictText)}</div>
                </div>
            </div>
            <div class="dc-summary-grade">
                <div class="dc-grade-circle ${gradeColorClass}">
                    <span class="dc-grade-letter">${grade}</span>
                    <span class="dc-grade-score">${diScore}/100</span>
                </div>
            </div>
        </div>

        <div class="dc-summary-question">
            <span class="dc-full-question">${escHtml(entry.question || '')}</span>
        </div>

        <div class="dc-summary-metrics">
            <div class="dc-summary-metric">
                <div class="dc-sm-label">Market Price</div>
                <div class="dc-sm-value">${implPct}%</div>
                <div class="dc-sm-bar"><div class="dc-sm-fill dc-sm-market" style="width:${implPct}%"></div></div>
            </div>
            <div class="dc-summary-metric">
                <div class="dc-sm-label">Model Forecast</div>
                <div class="dc-sm-value">${modPct}%</div>
                <div class="dc-sm-bar"><div class="dc-sm-fill dc-sm-model" style="width:${modPct}%"></div></div>
            </div>
            <div class="dc-summary-metric">
                <div class="dc-sm-label">Edge</div>
                <div class="dc-sm-value ${edgeVal > 0 ? 'pnl-positive' : edgeVal < 0 ? 'pnl-negative' : ''}">${edgeVal >= 0 ? '+' : ''}${edgeVal.toFixed(2)}%</div>
                <div class="dc-sm-bar"><div class="dc-sm-fill dc-sm-edge" style="width:${Math.min(Math.abs(edgeVal) * 5, 100)}%"></div></div>
            </div>
            <div class="dc-summary-metric">
                <div class="dc-sm-label">Evidence Quality</div>
                <div class="dc-sm-value">${(eq).toFixed(2)}</div>
                <div class="dc-sm-bar"><div class="dc-sm-fill dc-sm-eq" style="width:${eq * 100}%"></div></div>
            </div>
            <div class="dc-summary-metric">
                <div class="dc-sm-label">Confidence</div>
                <div class="dc-sm-value">${conf}</div>
                <div class="dc-sm-bar"><div class="dc-sm-fill dc-sm-conf" style="width:${confPercent}%"></div></div>
            </div>
            <div class="dc-summary-metric">
                <div class="dc-sm-label">Researchability</div>
                <div class="dc-sm-value">${researchability}%</div>
                <div class="dc-sm-bar"><div class="dc-sm-fill dc-sm-research" style="width:${researchability}%"></div></div>
            </div>
        </div>

        <div class="dc-summary-bottom">
            <div class="dc-summary-reasons">
                <div class="dc-reasons-title">📋 Decision Breakdown</div>
                <ul class="dc-reasons-list">${reasonsList || '<li>No specific reasons recorded</li>'}</ul>
            </div>
            <div class="dc-summary-completeness">
                <div class="dc-completeness-title">Pipeline Progress</div>
                <div class="dc-completeness-ring">
                    <svg viewBox="0 0 36 36" class="dc-circular-chart">
                        <path class="dc-circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                        <path class="dc-circle-fill ${gradeColorClass}" stroke-dasharray="${completeness}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                        <text x="18" y="19.5" class="dc-circle-text">${completeness}%</text>
                    </svg>
                </div>
                <div class="dc-completeness-label">${stages.filter(s => s.status === 'passed' || s.status === 'executed').length}/${stages.length} stages</div>
            </div>
        </div>
    </div>`;

    // ═══ PIPELINE SECTION HEADER ═══
    html += '<div class="dc-pipeline-section">';
    html += '<div class="dc-pipeline-title">⚡ Pipeline Stage Breakdown</div>';
    html += '<div class="dc-pipeline">';

    stages.forEach((stage, si) => {
        const sc = stage.status === 'passed' || stage.status === 'executed' ? 'stage-pass' :
                   stage.status === 'blocked' ? 'stage-block' : 'stage-skip';
        const d = stage.details || {};

        html += `<div class="dc-stage ${sc}">`;
        html += `<div class="dc-stage-header">
            <span class="dc-stage-icon">${stage.icon}</span>
            <span class="dc-stage-name">${stage.name}</span>
            <span class="dc-stage-number">${si + 1}/${stages.length}</span>
            <span class="dc-stage-status-pill ${sc}">${stage.status.toUpperCase()}</span>
        </div>`;
        html += '<div class="dc-stage-body">';

        if (stage.name === 'Discovery & Filter') {
            html += '<div class="dc-kv-grid">';
            if (d.market_type) html += kvPill('Type', d.market_type);
            if (d.category) html += kvPill('Category', d.category);
            if (d.resolution_source) html += kvPill('Resolution', d.resolution_source);
            if (d.volume != null) html += kvPill('Volume', fmtD(d.volume));
            if (d.liquidity != null) html += kvPill('Liquidity', fmtD(d.liquidity));
            if (d.end_date) html += kvPill('Expiry', d.end_date.substring(0, 10));
            html += '</div>';
        }

        if (stage.name === 'Classification') {
            html += '<div class="dc-kv-grid">';
            html += kvPill('Category', d.category || 'UNKNOWN');
            html += kvPill('Subcategory', (d.subcategory || 'unknown').replace(/_/g, ' '));
            html += kvPill('Strategy', (d.search_strategy || '—').replace(/_/g, ' '));
            html += kvPill('Query Budget', d.recommended_queries || '—');
            html += kvPillClass('Worth Research', d.worth_researching ? 'YES' : 'NO',
                d.worth_researching ? 'pnl-positive' : 'pnl-negative');
            html += '</div>';

            // Researchability bar
            const rPct = d.researchability || 0;
            const rColor = rPct >= 70 ? '#00d68f' : rPct >= 40 ? '#f59e0b' : '#ef4444';
            html += `<div class="dc-quality-breakdown">
                <div class="dc-evidence-title">🔬 Researchability Score</div>
                <div class="dc-quality-row">
                    <span class="dc-quality-label">Score</span>
                    <div class="dc-quality-track"><div class="dc-quality-fill" style="width:${rPct}%;background:${rColor}"></div></div>
                    <span class="dc-quality-val">${rPct}%</span>
                </div>
            </div>`;

            // Researchability reasons
            if (d.researchability_reasons && d.researchability_reasons.length > 0) {
                html += '<div class="dc-research-summary">';
                html += '<div class="dc-evidence-title">💡 Why this score</div>';
                d.researchability_reasons.forEach(r => {
                    html += `<div class="dc-summary-text" style="margin-bottom:4px;">• ${escHtml(r)}</div>`;
                });
                html += '</div>';
            }

            // Primary sources
            if (d.primary_sources && d.primary_sources.length > 0) {
                html += '<div class="dc-research-summary">';
                html += '<div class="dc-evidence-title">📡 Primary Sources</div>';
                html += '<div class="dc-kv-grid">';
                d.primary_sources.forEach(s => {
                    html += `<div class="dc-kv"><span class="dc-kv-value" style="font-size:12px;">${escHtml(s)}</span></div>`;
                });
                html += '</div></div>';
            }

            // Tags
            if (d.tags && d.tags.length > 0) {
                html += '<div class="dc-research-summary">';
                html += '<div class="dc-evidence-title">🏷️ Tags</div>';
                html += '<div class="dc-kv-grid">';
                d.tags.forEach(t => {
                    const tagColor = t === 'scheduled_event' ? '#3b82f6' :
                                     t === 'high_signal' ? '#00d68f' :
                                     t === 'unpredictable' ? '#ef4444' :
                                     t === 'volatile' ? '#f59e0b' : '#a78bfa';
                    html += `<div class="dc-kv"><span class="dc-kv-value" style="font-size:11px;background:${tagColor}20;color:${tagColor};padding:2px 8px;border-radius:10px;">${escHtml(t.replace(/_/g, ' '))}</span></div>`;
                });
                html += '</div></div>';
            }
        }

        if (stage.name === 'Research') {
            html += '<div class="dc-kv-grid">';
            html += kvPill('Sources', d.num_sources || 0);
            html += kvPill('Quality', fmt(d.evidence_quality, 3));
            if (d.llm_quality_score != null && d.llm_quality_score > 0) {
                html += kvPill('LLM Quality', fmt(d.llm_quality_score, 2));
            }
            html += '</div>';

            // Quality breakdown bars
            if (d.quality_breakdown && Object.keys(d.quality_breakdown).length > 0) {
                const qb = d.quality_breakdown;
                html += '<div class="dc-quality-breakdown">';
                html += '<div class="dc-evidence-title">📊 Quality Breakdown</div>';
                const dims = [
                    {label: 'Recency', key: 'recency', color: '#00d68f'},
                    {label: 'Authority', key: 'authority', color: '#3b82f6'},
                    {label: 'Agreement', key: 'agreement', color: '#a78bfa'},
                    {label: 'Numeric Data', key: 'numeric_density', color: '#f59e0b'},
                    {label: 'Content Depth', key: 'content_depth', color: '#06b6d4'},
                ];
                dims.forEach(dim => {
                    const val = qb[dim.key] || 0;
                    const pct = (val * 100).toFixed(0);
                    html += `<div class="dc-quality-row">
                        <span class="dc-quality-label">${dim.label}</span>
                        <div class="dc-quality-track"><div class="dc-quality-fill" style="width:${pct}%;background:${dim.color}"></div></div>
                        <span class="dc-quality-val">${pct}%</span>
                    </div>`;
                });
                html += '</div>';
            }

            // Research summary
            if (d.summary) {
                html += `<div class="dc-research-summary">
                    <div class="dc-evidence-title">📋 Research Summary</div>
                    <div class="dc-summary-text">${escHtml(d.summary)}</div>
                </div>`;
            }

            // Evidence bullets with clickable source links
            if (d.evidence_bullets && d.evidence_bullets.length > 0) {
                html += '<div class="dc-evidence-list">';
                html += '<div class="dc-evidence-title">� Key Evidence from Sources</div>';
                d.evidence_bullets.forEach(b => {
                    const text = typeof b === 'string' ? b : (b.text || JSON.stringify(b));
                    const citation = (typeof b === 'object' && b.citation) ? b.citation : null;
                    const confidence = (typeof b === 'object' && b.confidence != null) ? b.confidence : null;
                    const isNumeric = (typeof b === 'object' && b.is_numeric) ? true : false;

                    // Impact/confidence badge
                    let impactBadge = '';
                    if (typeof b === 'object' && b.impact) {
                        const impClass = b.impact === 'supports' ? 'dc-impact-supports' :
                                        b.impact === 'opposes' ? 'dc-impact-opposes' : 'dc-impact-neutral';
                        const impIcon = b.impact === 'supports' ? '▲' : b.impact === 'opposes' ? '▼' : '●';
                        impactBadge = `<span class="dc-impact-badge ${impClass}">${impIcon} ${b.impact}</span>`;
                    }

                    // Numeric data badge
                    let numericBadge = '';
                    if (isNumeric && b.metric_name) {
                        const metricVal = b.metric_value || '';
                        const metricUnit = b.metric_unit || '';
                        numericBadge = `<span class="dc-numeric-badge">📊 ${escHtml(b.metric_name)}: ${escHtml(metricVal)}${metricUnit ? ' ' + escHtml(metricUnit) : ''}</span>`;
                    }

                    // Relevance indicator
                    const rel = (typeof b === 'object' && b.relevance != null)
                        ? `<span class="dc-relevance">${(b.relevance * 100).toFixed(0)}% relevant</span>`
                        : '';

                    // Confidence indicator
                    const confBadge = confidence != null
                        ? `<span class="dc-confidence-badge">${(confidence * 100).toFixed(0)}% conf.</span>`
                        : '';

                    // Source link with title
                    let sourceLink = '';
                    if (citation) {
                        const publisher = citation.publisher || '';
                        const title = citation.title || '';
                        const url = citation.url || '';
                        const date = citation.date || '';

                        if (url) {
                            const linkText = title || publisher || url;
                            sourceLink = `<a href="${escHtml(url)}" target="_blank" rel="noopener" class="dc-source-link" title="${escHtml(url)}">🔗 ${escHtml(linkText.substring(0, 80))}</a>`;
                        }
                        if (publisher) {
                            sourceLink += `<span class="dc-publisher">${escHtml(publisher)}</span>`;
                        }
                        if (date) {
                            sourceLink += `<span class="dc-source-date">${escHtml(date)}</span>`;
                        }
                    } else if (typeof b === 'object' && b.source) {
                        // Fallback for LLM evidence format {text, source, url, date, impact}
                        const url = b.url || '';
                        if (url) {
                            sourceLink = `<a href="${escHtml(url)}" target="_blank" rel="noopener" class="dc-source-link">🔗 ${escHtml(b.source || url)}</a>`;
                        } else if (b.source) {
                            sourceLink = `<span class="dc-publisher">${escHtml(b.source)}</span>`;
                        }
                        if (b.date) sourceLink += `<span class="dc-source-date">${escHtml(b.date)}</span>`;
                    }

                    html += `<div class="dc-evidence-item${isNumeric ? ' dc-evidence-numeric' : ''}">
                        <div class="dc-evidence-header">
                            ${impactBadge}${rel}${confBadge}${numericBadge}
                        </div>
                        <div class="dc-evidence-text">${escHtml(text)}</div>
                        <div class="dc-evidence-meta">${sourceLink}</div>
                    </div>`;
                });
                html += '</div>';
            }

            // Contradictions
            if (d.contradictions && d.contradictions.length > 0) {
                html += '<div class="dc-contradictions">';
                html += '<div class="dc-evidence-title">⚖️ Contradictions Found</div>';
                d.contradictions.forEach(c => {
                    html += `<div class="dc-contradiction-item">
                        <div class="dc-contradiction-claim">
                            <span class="dc-contra-label">Claim A:</span> ${escHtml(c.claim_a || '')}
                        </div>
                        <div class="dc-contradiction-claim">
                            <span class="dc-contra-label">Claim B:</span> ${escHtml(c.claim_b || '')}
                        </div>
                        ${c.description ? `<div class="dc-contradiction-desc">${escHtml(c.description)}</div>` : ''}
                    </div>`;
                });
                html += '</div>';
            }
        }

        if (stage.name === 'Forecast') {
            html += '<div class="dc-kv-grid">';
            html += kvPill('Implied P', fmtP((d.implied_prob || 0) * 100));
            html += kvPill('Model P', fmtP((d.model_prob || 0) * 100));
            const e = (d.edge || 0) * 100;
            html += kvPillClass('Edge', (e >= 0 ? '+' : '') + e.toFixed(2) + '%', e > 0 ? 'pnl-positive' : 'pnl-negative');
            html += kvPill('Confidence', d.confidence || '—');
            html += '</div>';

            // Edge visualization bar
            const implPct = ((d.implied_prob || 0) * 100).toFixed(1);
            const modPct = ((d.model_prob || 0) * 100).toFixed(1);
            html += `<div class="dc-prob-compare">
                <div class="dc-prob-bar-wrap">
                    <div class="dc-prob-label">Market ${implPct}%</div>
                    <div class="dc-prob-bar-track">
                        <div class="dc-prob-bar dc-prob-implied" style="width:${implPct}%"></div>
                    </div>
                </div>
                <div class="dc-prob-bar-wrap">
                    <div class="dc-prob-label">Model ${modPct}%</div>
                    <div class="dc-prob-bar-track">
                        <div class="dc-prob-bar dc-prob-model" style="width:${modPct}%"></div>
                    </div>
                </div>
            </div>`;

            if (d.reasoning) {
                html += `<div class="dc-reasoning">
                    <div class="dc-reasoning-title">💭 LLM Reasoning</div>
                    <div class="dc-reasoning-text">${escHtml(d.reasoning)}</div>
                </div>`;
            }
            if (d.invalidation_triggers && d.invalidation_triggers.length > 0) {
                html += `<div class="dc-triggers">
                    <div class="dc-triggers-title">⚠️ Invalidation Triggers</div>
                    <ul class="dc-triggers-list">
                        ${d.invalidation_triggers.map(t => `<li>${escHtml(t)}</li>`).join('')}
                    </ul>
                </div>`;
            }
        }

        if (stage.name === 'Risk Check') {
            html += '<div class="dc-kv-grid">';
            html += kvPillClass('Decision', d.decision || '—',
                (d.decision || '') === 'TRADE' ? 'pnl-positive' : 'pnl-negative');
            html += '</div>';
            if (d.violations && d.violations.length > 0) {
                html += '<div class="dc-violations">';
                html += '<div class="dc-violations-title">🚫 Violations</div>';
                d.violations.forEach(v => {
                    html += `<div class="dc-violation-item">${escHtml(v)}</div>`;
                });
                html += '</div>';
            }
            if (d.reasons && !d.violations?.length) {
                html += `<div class="dc-reason-text">${escHtml(d.reasons)}</div>`;
            }
        }

        if (stage.name === 'Execution') {
            html += '<div class="dc-kv-grid">';
            html += kvPill('Stake', d.stake_usd ? fmtD(d.stake_usd) : '—');
            html += kvPill('Status', d.order_status || '—');
            html += '</div>';
        }

        html += '</div></div>'; // close body, stage

        // Connector arrow between stages
        if (si < stages.length - 1) {
            html += '<div class="dc-stage-connector"><div class="dc-connector-line"></div><div class="dc-connector-arrow">›</div></div>';
        }
    });

    html += '</div>'; // close pipeline
    html += '</div>'; // close pipeline-section
    return html;
}

function kvPill(label, value) {
    return `<div class="dc-kv"><span class="dc-kv-label">${label}</span><span class="dc-kv-value">${value}</span></div>`;
}
function kvPillClass(label, value, cls) {
    return `<div class="dc-kv"><span class="dc-kv-label">${label}</span><span class="dc-kv-value ${cls}">${value}</span></div>`;
}
function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
}

function toggleDecisionDetail(idx) {
    const detail = document.getElementById(`dc-detail-${idx}`);
    const icon = document.getElementById(`dc-expand-${idx}`);
    if (!detail) return;
    const open = detail.style.display !== 'none';
    detail.style.display = open ? 'none' : 'block';
    if (icon) icon.textContent = open ? '▶' : '▼';

    // Persist expanded state by stable key
    const card = detail.closest('.decision-card');
    if (card && card.dataset.decisionKey) {
        if (open) _expandedDecisionKeys.delete(card.dataset.decisionKey);
        else      _expandedDecisionKeys.add(card.dataset.decisionKey);
    }
}

function toggleDecisionExpand() {
    _decisionExpanded = !_decisionExpanded;
    const btn = $('#btn-expand-all');
    if (btn) btn.textContent = _decisionExpanded ? 'Collapse All' : 'Expand All';
    const details = document.querySelectorAll('.dc-detail');
    const icons = document.querySelectorAll('.dc-expand-icon');
    details.forEach(d => d.style.display = _decisionExpanded ? 'block' : 'none');
    icons.forEach(i => i.textContent = _decisionExpanded ? '▼' : '▶');
}

function filterDecisionCards() {
    const sel = $('#decision-filter');
    const filter = sel ? sel.value.toUpperCase() : '';
    const cards = document.querySelectorAll('.decision-card');
    cards.forEach(c => {
        if (!filter || c.dataset.decision === filter) {
            c.style.display = '';
        } else {
            c.style.display = 'none';
        }
    });
}

// ═══════════════════════════════════════════════════════════════
//  PERFORMANCE ANALYTICS
// ═══════════════════════════════════════════════════════════════

let chartCategoryPnl = null;
let chartCalibration = null;
let chartModelAccuracy = null;

async function updateAnalytics() {
    try {
        const [analytics, calibration, modelAcc] = await Promise.all([
            fetch('/api/analytics').then(r => r.json()).catch(() => null),
            fetch('/api/calibration-curve').then(r => r.json()).catch(() => null),
            fetch('/api/model-accuracy').then(r => r.json()).catch(() => null),
        ]);

        if (analytics) {
            // KPI Cards
            const wr = analytics.win_rate || 0;
            $('#ana-win-rate').textContent = `${(wr * 100).toFixed(1)}%`;
            $('#ana-win-rate-sub').textContent = `7d: ${(analytics.win_rate_7d * 100 || 0).toFixed(1)}% | 30d: ${(analytics.win_rate_30d * 100 || 0).toFixed(1)}%`;

            const sharpe = analytics.sharpe_ratio || 0;
            $('#ana-sharpe').textContent = sharpe.toFixed(2);
            $('#ana-sortino-sub').textContent = `Sortino: ${(analytics.sortino_ratio || 0).toFixed(2)}`;

            const pf = analytics.profit_factor || 0;
            $('#ana-profit-factor').textContent = pf === Infinity ? '∞' : pf.toFixed(2);
            const avgWin = (analytics.avg_win || 0).toFixed(2);
            const avgLoss = Math.abs(analytics.avg_loss || 0).toFixed(2);
            $('#ana-pf-sub').textContent = `Avg W: $${avgWin} / L: $${avgLoss}`;

            const maxDD = (analytics.max_drawdown_pct || 0) * 100;
            $('#ana-max-dd').textContent = `${maxDD.toFixed(2)}%`;
            $('#ana-calmar-sub').textContent = `Calmar: ${(analytics.calmar_ratio || 0).toFixed(2)}`;

            const roi = analytics.roi_pct || 0;
            $('#ana-roi').textContent = `${roi >= 0 ? '+' : ''}${roi.toFixed(2)}%`;
            $('#ana-roi').style.color = roi >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
            $('#ana-roi-sub').textContent = `Staked: $${(analytics.total_staked || 0).toFixed(2)}`;

            const streak = analytics.current_streak || 0;
            const streakEmoji = streak > 0 ? '🔥' : streak < 0 ? '❄️' : '—';
            $('#ana-streak').textContent = `${streakEmoji} ${Math.abs(streak)}`;
            $('#ana-streak-sub').textContent = `Best: ${analytics.best_streak || 0} | Worst: ${analytics.worst_streak || 0}`;

            // Leaderboard
            const lb = analytics.leaderboard || [];
            const lbBody = $('#leaderboard-body');
            if (lb.length > 0) {
                lbBody.innerHTML = lb.map(entry => {
                    const rankClass = entry.rank <= 3 ? `rank-${entry.rank}` : 'rank-other';
                    const roiColor = entry.roi_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
                    return `<tr>
                        <td><span class="leaderboard-rank ${rankClass}">${entry.rank}</span></td>
                        <td>${entry.category}</td>
                        <td style="color:${roiColor};font-weight:700;">${entry.roi_pct >= 0 ? '+' : ''}${entry.roi_pct.toFixed(1)}%</td>
                        <td>${(entry.win_rate * 100).toFixed(1)}%</td>
                        <td style="color:${entry.total_pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">$${entry.total_pnl.toFixed(2)}</td>
                        <td>${entry.trades}</td>
                        <td>${(entry.avg_edge * 100).toFixed(2)}%</td>
                        <td>${entry.score.toFixed(1)}</td>
                    </tr>`;
                }).join('');
            }

            // Category PnL Chart
            const cats = analytics.category_stats || [];
            if (cats.length > 0) {
                const labels = cats.map(c => c.category);
                const pnlData = cats.map(c => c.total_pnl);
                const bgColors = pnlData.map(v => v >= 0
                    ? 'rgba(0, 214, 143, 0.7)'
                    : 'rgba(255, 77, 106, 0.7)');

                const ctx = document.getElementById('chart-category-pnl');
                if (chartCategoryPnl) chartCategoryPnl.destroy();
                chartCategoryPnl = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels,
                        datasets: [{
                            label: 'P&L ($)',
                            data: pnlData,
                            backgroundColor: bgColors,
                            borderRadius: 4,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { ticks: { color: '#8b8fa3', maxRotation: 45 }, grid: { display: false } },
                            y: { ticks: { color: '#8b8fa3' }, grid: { color: 'rgba(42,45,58,0.5)' } },
                        },
                    },
                });
            }
        }

        // Calibration Chart
        if (calibration && calibration.bins && calibration.bins.length > 0) {
            const bins = calibration.bins;
            const labels = bins.map(b => b.range);
            const forecasted = bins.map(b => b.avg_forecast);
            const actual = bins.map(b => b.avg_outcome);

            const ctx = document.getElementById('chart-calibration');
            if (chartCalibration) chartCalibration.destroy();
            chartCalibration = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [
                        {
                            label: 'Forecast Avg',
                            data: forecasted,
                            backgroundColor: 'rgba(76, 141, 255, 0.6)',
                            borderRadius: 3,
                        },
                        {
                            label: 'Actual Outcome',
                            data: actual,
                            backgroundColor: 'rgba(0, 214, 143, 0.6)',
                            borderRadius: 3,
                        },
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { labels: { color: '#8b8fa3' } },
                    },
                    scales: {
                        x: { ticks: { color: '#8b8fa3' }, grid: { display: false } },
                        y: { ticks: { color: '#8b8fa3' }, grid: { color: 'rgba(42,45,58,0.5)' }, min: 0, max: 1 },
                    },
                },
            });
        }

        // Model Accuracy Chart
        if (modelAcc && modelAcc.models && modelAcc.models.length > 0) {
            const models = modelAcc.models;
            const labels = models.map(m => m.model_name.split('/').pop().split('-').slice(0, 2).join('-'));
            const brierData = models.map(m => m.brier_score);

            const ctx = document.getElementById('chart-model-accuracy');
            if (chartModelAccuracy) chartModelAccuracy.destroy();
            chartModelAccuracy = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels,
                    datasets: [{
                        data: models.map(m => m.total_forecasts),
                        backgroundColor: [
                            'rgba(76, 141, 255, 0.7)',
                            'rgba(168, 85, 247, 0.7)',
                            'rgba(255, 159, 67, 0.7)',
                            'rgba(0, 214, 143, 0.7)',
                            'rgba(244, 114, 182, 0.7)',
                        ],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { labels: { color: '#8b8fa3', font: { size: 11 } } },
                        tooltip: {
                            callbacks: {
                                afterLabel: (ctx) => {
                                    const m = models[ctx.dataIndex];
                                    return `Brier: ${m.brier_score.toFixed(4)} | Err: ${m.avg_error.toFixed(4)}`;
                                }
                            }
                        }
                    },
                },
            });
        }
    } catch (e) {
        console.warn('Analytics update error:', e);
    }
}

// ═══════════════════════════════════════════════════════════════
//  MARKET REGIME
// ═══════════════════════════════════════════════════════════════

async function updateRegime() {
    try {
        const data = await fetch('/api/regime').then(r => r.json()).catch(() => null);
        if (!data || !data.current) return;

        const c = data.current;
        const regimeEl = $('#regime-current');
        regimeEl.textContent = c.regime || 'NORMAL';
        regimeEl.className = 'card-value';

        const conf = c.confidence || 0;
        $('#regime-confidence').textContent = `Confidence: ${(conf * 100).toFixed(1)}%`;

        const kelly = c.kelly_multiplier || 1;
        $('#regime-kelly').textContent = `${kelly.toFixed(2)}x`;
        $('#regime-kelly').style.color = kelly < 0.8 ? 'var(--accent-red)' : kelly > 1.1 ? 'var(--accent-green)' : 'var(--text)';

        const sizeMult = c.size_multiplier || 1;
        $('#regime-size-mult').textContent = `Size: ${sizeMult.toFixed(2)}x`;

        $('#regime-explanation').textContent = c.explanation || '—';
        $('#regime-detected-at').textContent = c.detected_at ? `Detected: ${new Date(c.detected_at).toLocaleString()}` : '—';
    } catch (e) {
        console.warn('Regime update error:', e);
    }
}

// ═══════════════════════════════════════════════════════════════
//  WHALE / SMART MONEY TRACKER
// ═══════════════════════════════════════════════════════════════

async function updateWhaleTracker() {
    const data = await apiFetch('/api/whale-activity');
    if (!data) return;

    const s = data.summary || {};

    // Summary cards
    safeHTML($('#whale-total-wallets'), String(s.total_wallets || 0));
    safeHTML($('#whale-total-signals'), String(s.total_signals || 0));
    safeHTML($('#whale-strong-signals'), `Strong: ${s.strong_signals || 0}`);
    safeHTML($('#whale-recent-entries'), String(s.recent_entries || 0));
    safeHTML($('#whale-recent-exits'), `Exits: ${s.recent_exits || 0}`);
    safeHTML($('#whale-last-scan'), s.last_scan ? `Last scan: ${shortDate(s.last_scan)}` : 'Last scan: —');

    // Conviction signals table
    const signals = data.conviction_signals || [];
    if (signals.length === 0) {
        safeHTML($('#conviction-body'),
            '<tr><td colspan="11" class="empty-state">No conviction signals yet — run a wallet scan to populate</td></tr>');
    } else {
        const rows = signals.map(sig => {
            const strengthClass = sig.signal_strength === 'STRONG' ? 'pnl-positive'
                : sig.signal_strength === 'MODERATE' ? 'pnl-zero' : 'pnl-negative';
            const dirIcon = sig.direction === 'BULLISH' ? '🟢' : '🔴';
            const names = (sig.whale_names || []).slice(0, 3).join(', ');
            const namesSuffix = (sig.whale_names || []).length > 3
                ? ` +${(sig.whale_names || []).length - 3}` : '';
            return `<tr>
                <td title="${sig.market_slug || ''}">${(sig.title || sig.market_slug || '—').substring(0, 50)}</td>
                <td>${sig.outcome || '—'}</td>
                <td><strong>${sig.whale_count || 0}</strong></td>
                <td>${fmtD(sig.total_whale_usd)}</td>
                <td>${fmt(sig.avg_whale_price, 3)}</td>
                <td>${fmt(sig.current_price, 3)}</td>
                <td><strong>${fmt(sig.conviction_score, 0)}</strong></td>
                <td class="${strengthClass}"><strong>${sig.signal_strength || '—'}</strong></td>
                <td>${dirIcon} ${sig.direction || '—'}</td>
                <td title="${(sig.whale_names || []).join(', ')}">${names}${namesSuffix}</td>
                <td>${shortDate(sig.detected_at)}</td>
            </tr>`;
        }).join('');
        safeHTML($('#conviction-body'), rows);
    }

    // Recent deltas table
    const deltas = data.recent_deltas || [];
    if (deltas.length === 0) {
        safeHTML($('#whale-deltas-body'),
            '<tr><td colspan="8" class="empty-state">No whale activity detected yet</td></tr>');
    } else {
        const dRows = deltas.slice(0, 30).map(d => {
            const actionIcons = {
                'NEW_ENTRY': '🟢 Entry',
                'EXIT': '🔴 Exit',
                'SIZE_INCREASE': '📈 ↑ Size',
                'SIZE_DECREASE': '📉 ↓ Size',
            };
            const actionLabel = actionIcons[d.action] || d.action;
            const valClass = d.value_change_usd >= 0 ? 'pnl-positive' : 'pnl-negative';
            return `<tr>
                <td><strong>${d.wallet_name || d.wallet_address?.substring(0, 10) || '—'}</strong></td>
                <td>${actionLabel}</td>
                <td title="${d.market_slug || ''}">${(d.title || d.market_slug || '—').substring(0, 45)}</td>
                <td>${d.outcome || '—'}</td>
                <td>${fmt(d.size_change, 2)}</td>
                <td class="${valClass}">${fmtD(d.value_change_usd)}</td>
                <td>${fmt(d.current_price, 3)}</td>
                <td>${shortDate(d.detected_at)}</td>
            </tr>`;
        }).join('');
        safeHTML($('#whale-deltas-body'), dRows);
    }

    // Tracked wallets leaderboard
    const wallets = data.tracked_wallets || [];
    if (wallets.length === 0) {
        safeHTML($('#tracked-wallets-body'),
            '<tr><td colspan="8" class="empty-state">No wallets tracked yet</td></tr>');
    } else {
        const wRows = wallets.map((w, i) => {
            const pnlCls = w.total_pnl >= 0 ? 'pnl-positive' : 'pnl-negative';
            const shortAddr = w.address ? `${w.address.substring(0, 6)}…${w.address.slice(-4)}` : '—';
            return `<tr>
                <td><strong>#${i + 1}</strong></td>
                <td><strong>${w.name || '—'}</strong></td>
                <td><code title="${w.address}">${shortAddr}</code></td>
                <td class="${pnlCls}"><strong>${fmtD(w.total_pnl)}</strong></td>
                <td>${fmtP(((w.win_rate || 0) * 100))}</td>
                <td>${w.active_positions || 0}</td>
                <td><strong>${fmt(w.score, 0)}</strong></td>
                <td>${shortDate(w.last_scanned)}</td>
            </tr>`;
        }).join('');
        safeHTML($('#tracked-wallets-body'), wRows);
    }
}

// ═══════════════════════════════════════════════════════════════
//  REFRESH ORCHESTRATION
// ═══════════════════════════════════════════════════════════════

async function refreshAll() {
    const scrollY = window.scrollY;                    // preserve scroll

    await Promise.all([
        updatePortfolio(),
        updateRisk(),
        updatePositions(),
        updateCandidates(),
        updateDecisionLog(),
        updateForecasts(),
        updateTrades(),
        updateCharts(),
        updateEquityCurve(),
        updateEngineStatus(),
        updateDrawdown(),
        updateAudit(),
        updateAlerts(),
        updateConfig(),
        updateAnalytics(),
        updateRegime(),
        updateWhaleTracker(),
    ]);
    $('#last-updated-time').textContent = new Date().toLocaleTimeString();

    requestAnimationFrame(() => window.scrollTo(0, scrollY));  // restore scroll
}

// ─── Init ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    refreshAll();
    setInterval(refreshAll, 15000);
});
