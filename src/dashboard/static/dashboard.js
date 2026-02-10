/* ─── Polymarket Bot Dashboard — Client-Side Logic ──────────────── */

const REFRESH_INTERVAL = 15_000; // 15 seconds

// ─── Chart instances (re-used on updates) ──────────────────────
let chartDaily = null;
let chartEdgeEQ = null;
let chartMarketTypes = null;

// ─── Helpers ───────────────────────────────────────────────────
function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function fmt$(v) {
    if (v == null) return "$0.00";
    const n = Number(v);
    return (n < 0 ? "-" : "") + "$" + Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmtPct(v, decimals = 2) {
    if (v == null) return "0.00%";
    return (Number(v) * 100).toFixed(decimals) + "%";
}
function fmtNum(v, d = 3) { return v != null ? Number(v).toFixed(d) : "0"; }
function fmtTime(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" }) +
        " " + d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}
function truncate(s, n = 45) { return s && s.length > n ? s.slice(0, n) + "…" : s || "—"; }
function pnlClass(v) { return v > 0 ? "pnl-positive" : v < 0 ? "pnl-negative" : "pnl-zero"; }

async function fetchJSON(url) {
    try {
        const r = await fetch(url);
        return await r.json();
    } catch (e) {
        console.error("Fetch error:", url, e);
        return null;
    }
}

// ─── Portfolio Cards ───────────────────────────────────────────
async function updatePortfolio() {
    const d = await fetchJSON("/api/portfolio");
    if (!d) return;

    $("#bankroll").textContent = fmt$(d.bankroll);
    $("#available-capital").textContent = `Available: ${fmt$(d.available_capital)}`;

    const pnlEl = $("#total-pnl");
    pnlEl.textContent = fmt$(d.total_pnl);
    pnlEl.className = "card-value " + pnlClass(d.total_pnl);
    $("#unrealized-pnl").textContent = `Unrealized: ${fmt$(d.unrealized_pnl)}`;

    $("#open-positions").textContent = d.open_positions;
    $("#total-invested").textContent = `Invested: ${fmt$(d.total_invested)}`;

    $("#total-trades").textContent = d.total_trades;
    $("#trade-breakdown").textContent = `Live: ${d.live_trades} | Paper: ${d.paper_trades}`;

    const edgeEl = $("#avg-edge");
    edgeEl.textContent = fmtPct(d.avg_edge);
    $("#avg-evidence-quality").textContent = `Avg EQ: ${fmtNum(d.avg_evidence_quality)}`;

    $("#today-trades").textContent = `${d.today_trades} trades`;
    $("#daily-volume").textContent = `Volume: ${fmt$(d.daily_volume)}`;

    // Mode badge
    const modeBadge = $("#mode-badge");
    if (d.live_trading_enabled && !d.dry_run) {
        modeBadge.textContent = "LIVE TRADING";
        modeBadge.className = "badge badge-live";
    } else {
        modeBadge.textContent = "PAPER MODE";
        modeBadge.className = "badge badge-paper";
    }
}

// ─── Risk Monitor ──────────────────────────────────────────────
async function updateRisk() {
    const d = await fetchJSON("/api/risk");
    if (!d) return;

    // Kill switch badge
    const ksBadge = $("#kill-switch-badge");
    if (d.kill_switch) {
        ksBadge.style.display = "inline-block";
        ksBadge.textContent = "⛔ KILL SWITCH ON";
        ksBadge.className = "badge badge-danger";
    } else {
        ksBadge.style.display = "none";
    }

    // Daily exposure bar
    const dailyPct = d.current.daily_loss_pct;
    setRiskBar("risk-bar-daily", dailyPct);
    $("#risk-daily-current").textContent = fmt$(d.current.daily_exposure);
    $("#risk-daily-limit").textContent = fmt$(d.limits.max_daily_loss);

    // Positions bar
    const posPct = d.current.positions_pct;
    setRiskBar("risk-bar-positions", posPct);
    $("#risk-pos-current").textContent = d.current.open_positions;
    $("#risk-pos-limit").textContent = d.limits.max_open_positions;

    // Evidence quality bar (inverted — higher is better)
    const eqPct = d.current.avg_evidence_quality * 100;
    const eqBar = document.getElementById("risk-bar-eq");
    eqBar.style.width = Math.min(eqPct, 100) + "%";
    eqBar.className = "risk-bar bar-inverted" + (eqPct < d.forecasting.min_evidence_quality * 100 ? " danger" : "");
    $("#risk-eq-current").textContent = fmtNum(d.current.avg_evidence_quality);
    $("#risk-eq-limit").textContent = fmtNum(d.forecasting.min_evidence_quality);

    // Risk params
    const paramsEl = $("#risk-params");
    paramsEl.innerHTML = "";
    const params = [
        ["Min Edge", fmtPct(d.limits.min_edge)],
        ["Max Stake/Market", fmt$(d.limits.max_stake_per_market)],
        ["Kelly Fraction", d.limits.kelly_fraction],
        ["Max Bankroll %", fmtPct(d.limits.max_bankroll_fraction)],
        ["Min Liquidity", fmt$(d.limits.min_liquidity)],
        ["Max Spread", fmtPct(d.limits.max_spread)],
        ["Slippage Tolerance", fmtPct(d.execution.slippage_tolerance)],
        ["LLM Model", d.forecasting.llm_model],
    ];
    params.forEach(([label, val]) => {
        const div = document.createElement("div");
        div.className = "risk-param";
        div.innerHTML = `<div class="rp-label">${label}</div><div class="rp-value">${val}</div>`;
        paramsEl.appendChild(div);
    });
}

function setRiskBar(id, pct) {
    const bar = document.getElementById(id);
    const clamped = Math.min(Math.max(pct, 0), 100);
    bar.style.width = clamped + "%";
    bar.className = "risk-bar" + (clamped >= 90 ? " danger" : clamped >= 60 ? " warning" : "");
}

// ─── Positions Table ───────────────────────────────────────────
async function updatePositions() {
    const d = await fetchJSON("/api/positions");
    if (!d) return;
    const tbody = $("#positions-body");

    if (!d.positions || d.positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="empty-state">No active positions</td></tr>';
        return;
    }

    tbody.innerHTML = d.positions.map(p => `
        <tr>
            <td title="${p.question || ''}">${truncate(p.question || p.market_id, 40)}</td>
            <td>${p.market_type || "—"}</td>
            <td><span class="pill ${p.direction === 'BUY_YES' ? 'pill-buy' : 'pill-sell'}">${p.direction || "—"}</span></td>
            <td>${fmtPct(p.entry_price)}</td>
            <td>${fmtPct(p.current_price)}</td>
            <td>${fmtNum(p.size, 1)}</td>
            <td>${fmt$(p.stake_usd)}</td>
            <td class="${pnlClass(p.pnl)}">${fmt$(p.pnl)}</td>
            <td class="${pnlClass(p.pnl_pct)}">${(p.pnl_pct || 0).toFixed(1)}%</td>
            <td>${fmtTime(p.opened_at)}</td>
        </tr>
    `).join("");
}

// ─── Forecasts Table ───────────────────────────────────────────
async function updateForecasts() {
    const d = await fetchJSON("/api/forecasts");
    if (!d) return;
    const tbody = $("#forecasts-body");

    if (!d.forecasts || d.forecasts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="empty-state">No forecasts yet</td></tr>';
        return;
    }

    tbody.innerHTML = d.forecasts.map(f => {
        const decisionClass = f.decision === "TRADE" ? "pill-trade" : "pill-no-trade";
        const edgeVal = f.edge != null ? fmtPct(f.edge) : "—";
        return `
        <tr>
            <td title="${f.question || ''}">${truncate(f.question || f.market_id, 40)}</td>
            <td>${f.market_type || "—"}</td>
            <td>${fmtPct(f.implied_probability)}</td>
            <td>${fmtPct(f.model_probability)}</td>
            <td>${edgeVal}</td>
            <td>${fmtNum(f.evidence_quality)}</td>
            <td>${f.num_sources || 0}</td>
            <td>${f.confidence_level || "—"}</td>
            <td><span class="pill ${decisionClass}">${f.decision || "—"}</span></td>
            <td>${fmtTime(f.created_at)}</td>
        </tr>`;
    }).join("");
}

// ─── Trades Table ──────────────────────────────────────────────
async function updateTrades() {
    const d = await fetchJSON("/api/trades");
    if (!d) return;
    const tbody = $("#trades-body");

    if (!d.trades || d.trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="empty-state">No trades yet</td></tr>';
        return;
    }

    tbody.innerHTML = d.trades.map(t => {
        const sideClass = (t.side || "").toUpperCase().includes("BUY") ? "pill-buy" : "pill-sell";
        const modeClass = t.dry_run ? "pill-dry" : "pill-filled";
        const modeText = t.dry_run ? "PAPER" : "LIVE";
        return `
        <tr>
            <td title="${t.question || ''}">${truncate(t.question || t.market_id, 40)}</td>
            <td>${t.market_type || "—"}</td>
            <td><span class="pill ${sideClass}">${t.side || "—"}</span></td>
            <td>${fmtPct(t.price)}</td>
            <td>${fmtNum(t.size, 1)}</td>
            <td>${fmt$(t.stake_usd)}</td>
            <td>${t.status || "—"}</td>
            <td><span class="pill ${modeClass}">${modeText}</span></td>
            <td>${fmtTime(t.created_at)}</td>
        </tr>`;
    }).join("");
}

// ─── Charts ────────────────────────────────────────────────────
const CHART_COLORS = {
    blue:   "rgba(76, 141, 255, 0.8)",
    green:  "rgba(0, 214, 143, 0.8)",
    orange: "rgba(255, 159, 67, 0.8)",
    purple: "rgba(168, 85, 247, 0.8)",
    red:    "rgba(255, 77, 106, 0.8)",
    teal:   "rgba(20, 184, 166, 0.8)",
    pink:   "rgba(244, 114, 182, 0.8)",
    yellow: "rgba(251, 191, 36, 0.8)",
};
const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { color: "#8b8fa3", font: { size: 11 } } },
    },
    scales: {
        x: { ticks: { color: "#5a5e72", font: { size: 10 } }, grid: { color: "rgba(42,45,58,0.5)" } },
        y: { ticks: { color: "#5a5e72", font: { size: 10 } }, grid: { color: "rgba(42,45,58,0.5)" } },
    },
};

async function updateCharts() {
    const perf = await fetchJSON("/api/performance");
    const types = await fetchJSON("/api/market-types");

    // ── Daily Activity Chart ──
    if (perf && perf.daily_forecasts && perf.daily_forecasts.length > 0) {
        const days = perf.daily_forecasts.reverse();
        const labels = days.map(d => d.day);
        const forecasts = days.map(d => d.forecasts);
        const trades = days.map(d => d.trades);

        if (chartDaily) chartDaily.destroy();
        chartDaily = new Chart(document.getElementById("chart-daily-activity"), {
            type: "bar",
            data: {
                labels,
                datasets: [
                    { label: "Forecasts", data: forecasts, backgroundColor: CHART_COLORS.blue, borderRadius: 4 },
                    { label: "Trades", data: trades, backgroundColor: CHART_COLORS.green, borderRadius: 4 },
                ],
            },
            options: { ...CHART_DEFAULTS },
        });

        // ── Edge & EQ Chart ──
        const edges = days.map(d => d.avg_edge != null ? (d.avg_edge * 100).toFixed(2) : 0);
        const eqs = days.map(d => d.avg_eq != null ? (d.avg_eq * 100).toFixed(1) : 0);

        if (chartEdgeEQ) chartEdgeEQ.destroy();
        chartEdgeEQ = new Chart(document.getElementById("chart-edge-eq"), {
            type: "line",
            data: {
                labels,
                datasets: [
                    { label: "Avg Edge (%)", data: edges, borderColor: CHART_COLORS.green, backgroundColor: "rgba(0,214,143,0.1)", fill: true, tension: 0.3 },
                    { label: "Avg Evidence Quality (%)", data: eqs, borderColor: CHART_COLORS.blue, backgroundColor: "rgba(76,141,255,0.1)", fill: true, tension: 0.3 },
                ],
            },
            options: {
                ...CHART_DEFAULTS,
                plugins: { ...CHART_DEFAULTS.plugins },
                elements: { point: { radius: 3, hoverRadius: 5 } },
            },
        });
    }

    // ── Market Types Doughnut ──
    if (types && types.market_types && types.market_types.length > 0) {
        const mt = types.market_types;
        const mtLabels = mt.map(t => t.market_type || "UNKNOWN");
        const mtData = mt.map(t => t.count);
        const mtColors = [CHART_COLORS.blue, CHART_COLORS.green, CHART_COLORS.orange, CHART_COLORS.purple, CHART_COLORS.teal, CHART_COLORS.pink];

        if (chartMarketTypes) chartMarketTypes.destroy();
        chartMarketTypes = new Chart(document.getElementById("chart-market-types"), {
            type: "doughnut",
            data: {
                labels: mtLabels,
                datasets: [{ data: mtData, backgroundColor: mtColors.slice(0, mtData.length), borderWidth: 0 }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { color: "#8b8fa3", font: { size: 11 }, padding: 12 } },
                },
                cutout: "65%",
            },
        });
    }
}

// ─── Configuration Panel ───────────────────────────────────────
async function updateConfig() {
    const d = await fetchJSON("/api/config");
    if (!d) return;
    const grid = $("#config-grid");
    grid.innerHTML = "";

    const sections = [
        ["Scanning", d.scanning],
        ["Research", d.research],
        ["Forecasting", d.forecasting],
        ["Risk", d.risk],
        ["Execution", d.execution],
    ];

    sections.forEach(([title, obj]) => {
        if (!obj) return;
        const sec = document.createElement("div");
        sec.className = "config-section";
        let rows = "";
        Object.entries(obj).forEach(([k, v]) => {
            let display = v;
            if (Array.isArray(v)) display = v.join(", ") || "—";
            if (typeof v === "boolean") display = v ? "✅ Yes" : "❌ No";
            if (typeof v === "object" && !Array.isArray(v)) display = JSON.stringify(v);
            rows += `<div class="config-row"><span class="config-key">${k.replace(/_/g, " ")}</span><span class="config-val">${display}</span></div>`;
        });
        sec.innerHTML = `<h4>${title}</h4>${rows}`;
        grid.appendChild(sec);
    });
}

// ─── Refresh Loop ──────────────────────────────────────────────
async function refreshAll() {
    await Promise.all([
        updatePortfolio(),
        updateRisk(),
        updatePositions(),
        updateForecasts(),
        updateTrades(),
        updateCharts(),
        updateConfig(),
    ]);
    $("#last-updated-time").textContent = new Date().toLocaleTimeString();
}

// Boot
refreshAll();
setInterval(refreshAll, REFRESH_INTERVAL);
