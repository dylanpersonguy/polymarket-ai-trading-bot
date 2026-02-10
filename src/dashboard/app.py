"""Dashboard — Flask web application for monitoring the bot.

Serves a single-page dashboard at http://localhost:2345 with:
  - Portfolio overview (bankroll, P&L, win rate)
  - Active positions table
  - Recent forecasts with evidence quality
  - Trade history
  - Risk monitor (limits vs current values)
  - System health & metrics

All data is read from the SQLite database and in-process metrics.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, send_from_directory

from src.config import BotConfig, load_config, is_live_trading_enabled
from src.observability.metrics import metrics

# ─── Flask app ──────────────────────────────────────────────────────

_here = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(_here / "templates"),
    static_folder=str(_here / "static"),
)

_config: BotConfig | None = None
_db_path: str = "data/bot.db"


def _get_config() -> BotConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist (for fresh dashboards)."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS markets (
            id TEXT PRIMARY KEY, condition_id TEXT, question TEXT,
            market_type TEXT, category TEXT, volume REAL DEFAULT 0,
            liquidity REAL DEFAULT 0, end_date TEXT, resolution_source TEXT,
            first_seen TEXT, last_updated TEXT
        );
        CREATE TABLE IF NOT EXISTS forecasts (
            id TEXT PRIMARY KEY, market_id TEXT NOT NULL, question TEXT,
            market_type TEXT, implied_probability REAL, model_probability REAL,
            edge REAL, confidence_level TEXT, evidence_quality REAL,
            num_sources INTEGER, decision TEXT, reasoning TEXT,
            evidence_json TEXT, invalidation_triggers_json TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY, order_id TEXT, market_id TEXT NOT NULL,
            token_id TEXT, side TEXT, price REAL, size REAL, stake_usd REAL,
            status TEXT, dry_run INTEGER DEFAULT 1, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS positions (
            market_id TEXT PRIMARY KEY, token_id TEXT, direction TEXT,
            entry_price REAL, size REAL, stake_usd REAL,
            current_price REAL, pnl REAL, opened_at TEXT
        );
    """)


# ─── Pages ──────────────────────────────────────────────────────────

@app.route("/")
def index() -> str:
    return render_template("index.html")


# ─── API: Portfolio Overview ────────────────────────────────────────

@app.route("/api/portfolio")
def api_portfolio() -> Any:
    cfg = _get_config()
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        # Bankroll from config
        bankroll = cfg.risk.bankroll

        # Open positions
        positions = conn.execute("SELECT * FROM positions").fetchall()
        open_count = len(positions)
        total_invested = sum(r["stake_usd"] or 0 for r in positions)
        unrealized_pnl = sum(r["pnl"] or 0 for r in positions)

        # Trades today
        today = dt.date.today().isoformat()
        today_trades = conn.execute(
            "SELECT * FROM trades WHERE date(created_at) = ?", (today,)
        ).fetchall()
        daily_volume = sum(r["stake_usd"] or 0 for r in today_trades)

        # All-time trades
        all_trades = conn.execute("SELECT * FROM trades").fetchall()
        total_trades = len(all_trades)
        live_trades = [t for t in all_trades if not t["dry_run"]]
        paper_trades = [t for t in all_trades if t["dry_run"]]

        # P&L (sum of closed position P&L via trades)
        filled = [t for t in all_trades if t["status"] == "FILLED"]
        total_pnl = unrealized_pnl  # simplified

        # Win rate from forecasts
        forecasts = conn.execute("SELECT * FROM forecasts").fetchall()
        trade_decisions = [f for f in forecasts if f["decision"] == "TRADE"]
        no_trade_decisions = [f for f in forecasts if f["decision"] == "NO TRADE"]

        # Average evidence quality
        eq_values = [f["evidence_quality"] for f in forecasts if f["evidence_quality"]]
        avg_evidence_quality = sum(eq_values) / len(eq_values) if eq_values else 0.0

        # Average edge
        edge_values = [f["edge"] for f in forecasts if f["edge"]]
        avg_edge = sum(edge_values) / len(edge_values) if edge_values else 0.0

        return jsonify({
            "bankroll": bankroll,
            "available_capital": bankroll - total_invested,
            "total_invested": total_invested,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "open_positions": open_count,
            "total_trades": total_trades,
            "live_trades": len(live_trades),
            "paper_trades": len(paper_trades),
            "daily_volume": daily_volume,
            "today_trades": len(today_trades),
            "total_forecasts": len(forecasts),
            "trade_decisions": len(trade_decisions),
            "no_trade_decisions": len(no_trade_decisions),
            "avg_evidence_quality": round(avg_evidence_quality, 3),
            "avg_edge": round(avg_edge, 4),
            "dry_run": cfg.execution.dry_run,
            "live_trading_enabled": is_live_trading_enabled(),
        })
    finally:
        conn.close()


# ─── API: Active Positions ─────────────────────────────────────────

@app.route("/api/positions")
def api_positions() -> Any:
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        rows = conn.execute("""
            SELECT p.*, m.question, m.market_type
            FROM positions p
            LEFT JOIN markets m ON p.market_id = m.id
            ORDER BY p.opened_at DESC
        """).fetchall()
        positions = []
        for r in rows:
            rd = dict(r)
            pnl_pct = 0.0
            if rd.get("entry_price") and rd["entry_price"] > 0:
                pnl_pct = ((rd.get("current_price", 0) - rd["entry_price"]) / rd["entry_price"]) * 100
            rd["pnl_pct"] = round(pnl_pct, 2)
            positions.append(rd)
        return jsonify({"positions": positions})
    finally:
        conn.close()


# ─── API: Recent Forecasts ─────────────────────────────────────────

@app.route("/api/forecasts")
def api_forecasts() -> Any:
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        rows = conn.execute("""
            SELECT * FROM forecasts ORDER BY created_at DESC LIMIT 50
        """).fetchall()
        forecasts = []
        for r in rows:
            rd = dict(r)
            # Parse evidence JSON for bullet count
            try:
                evidence = json.loads(rd.get("evidence_json", "[]"))
                rd["evidence_count"] = len(evidence) if isinstance(evidence, list) else 0
            except (json.JSONDecodeError, TypeError):
                rd["evidence_count"] = 0
            forecasts.append(rd)
        return jsonify({"forecasts": forecasts})
    finally:
        conn.close()


# ─── API: Trade History ────────────────────────────────────────────

@app.route("/api/trades")
def api_trades() -> Any:
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        rows = conn.execute("""
            SELECT t.*, m.question, m.market_type
            FROM trades t
            LEFT JOIN markets m ON t.market_id = m.id
            ORDER BY t.created_at DESC
            LIMIT 100
        """).fetchall()
        trades = [dict(r) for r in rows]
        return jsonify({"trades": trades})
    finally:
        conn.close()


# ─── API: Risk Monitor ─────────────────────────────────────────────

@app.route("/api/risk")
def api_risk() -> Any:
    cfg = _get_config()
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        today = dt.date.today().isoformat()
        # Daily loss
        daily_trades = conn.execute(
            "SELECT COALESCE(SUM(stake_usd), 0) as total FROM trades WHERE date(created_at) = ?",
            (today,)
        ).fetchone()
        daily_exposure = float(daily_trades["total"]) if daily_trades else 0.0

        # Open positions count
        pos_count = conn.execute("SELECT COUNT(*) as cnt FROM positions").fetchone()
        open_positions = int(pos_count["cnt"]) if pos_count else 0

        # Recent forecasts average evidence quality
        recent = conn.execute(
            "SELECT evidence_quality FROM forecasts ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        recent_eq = [r["evidence_quality"] for r in recent if r["evidence_quality"]]
        avg_recent_eq = sum(recent_eq) / len(recent_eq) if recent_eq else 0.0

        return jsonify({
            "kill_switch": cfg.risk.kill_switch,
            "limits": {
                "max_daily_loss": cfg.risk.max_daily_loss,
                "max_open_positions": cfg.risk.max_open_positions,
                "max_stake_per_market": cfg.risk.max_stake_per_market,
                "max_bankroll_fraction": cfg.risk.max_bankroll_fraction,
                "min_edge": cfg.risk.min_edge,
                "min_liquidity": cfg.risk.min_liquidity,
                "max_spread": cfg.risk.max_spread,
                "kelly_fraction": cfg.risk.kelly_fraction,
            },
            "current": {
                "daily_exposure": daily_exposure,
                "open_positions": open_positions,
                "avg_evidence_quality": round(avg_recent_eq, 3),
                "daily_loss_pct": round(
                    (daily_exposure / cfg.risk.max_daily_loss * 100) if cfg.risk.max_daily_loss > 0 else 0, 1
                ),
                "positions_pct": round(
                    (open_positions / cfg.risk.max_open_positions * 100) if cfg.risk.max_open_positions > 0 else 0, 1
                ),
            },
            "execution": {
                "dry_run": cfg.execution.dry_run,
                "live_trading_enabled": is_live_trading_enabled(),
                "slippage_tolerance": cfg.execution.slippage_tolerance,
            },
            "forecasting": {
                "min_evidence_quality": cfg.forecasting.min_evidence_quality,
                "low_evidence_penalty": cfg.forecasting.low_evidence_penalty,
                "llm_model": cfg.forecasting.llm_model,
            },
        })
    finally:
        conn.close()


# ─── API: Market Type Breakdown ────────────────────────────────────

@app.route("/api/market-types")
def api_market_types() -> Any:
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        rows = conn.execute("""
            SELECT market_type, COUNT(*) as count,
                   AVG(evidence_quality) as avg_eq,
                   AVG(edge) as avg_edge
            FROM forecasts
            GROUP BY market_type
        """).fetchall()
        types = [dict(r) for r in rows]
        return jsonify({"market_types": types})
    finally:
        conn.close()


# ─── API: Performance Over Time ────────────────────────────────────

@app.route("/api/performance")
def api_performance() -> Any:
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        # Daily forecast counts and avg edge
        rows = conn.execute("""
            SELECT date(created_at) as day,
                   COUNT(*) as forecasts,
                   SUM(CASE WHEN decision = 'TRADE' THEN 1 ELSE 0 END) as trades,
                   AVG(edge) as avg_edge,
                   AVG(evidence_quality) as avg_eq
            FROM forecasts
            GROUP BY date(created_at)
            ORDER BY day DESC
            LIMIT 30
        """).fetchall()
        daily = [dict(r) for r in rows]

        # Daily trade volume
        trade_rows = conn.execute("""
            SELECT date(created_at) as day,
                   COUNT(*) as count,
                   SUM(stake_usd) as volume
            FROM trades
            GROUP BY date(created_at)
            ORDER BY day DESC
            LIMIT 30
        """).fetchall()
        trade_daily = [dict(r) for r in trade_rows]

        return jsonify({
            "daily_forecasts": daily,
            "daily_trades": trade_daily,
        })
    finally:
        conn.close()


# ─── API: System Metrics ───────────────────────────────────────────

@app.route("/api/metrics")
def api_metrics() -> Any:
    snapshot = metrics.snapshot()
    return jsonify(snapshot)


# ─── API: Drawdown State ──────────────────────────────────────────

@app.route("/api/drawdown")
def api_drawdown() -> Any:
    cfg = _get_config()
    return jsonify({
        "peak_equity": cfg.risk.bankroll,
        "current_equity": cfg.risk.bankroll,
        "drawdown_pct": 0.0,
        "heat_level": 0,
        "kelly_multiplier": 1.0,
        "is_killed": False,
        "kill_switch_pct": cfg.drawdown.max_drawdown_pct,
        "warning_pct": cfg.drawdown.warning_drawdown_pct,
        "critical_pct": cfg.drawdown.critical_drawdown_pct,
        "max_drawdown_pct": cfg.drawdown.max_drawdown_pct,
    })


# ─── API: Portfolio Risk ─────────────────────────────────────────

@app.route("/api/portfolio-risk")
def api_portfolio_risk() -> Any:
    cfg = _get_config()
    return jsonify({
        "max_exposure_per_category": cfg.portfolio.max_category_exposure_pct,
        "max_exposure_per_event": cfg.portfolio.max_single_event_exposure_pct,
        "max_correlated_positions": cfg.portfolio.max_correlated_positions,
        "correlation_threshold": cfg.portfolio.correlation_similarity_threshold,
        "category_exposures": {},
        "event_exposures": {},
        "is_healthy": True,
        "violations": [],
    })


# ─── API: Engine Status ─────────────────────────────────────────

@app.route("/api/engine-status")
def api_engine() -> Any:
    cfg = _get_config()
    return jsonify({
        "running": False,
        "scan_interval_minutes": cfg.engine.scan_interval_minutes,
        "max_markets_per_cycle": cfg.engine.max_markets_per_cycle,
        "auto_start": cfg.engine.auto_start,
        "paper_mode": cfg.engine.paper_mode,
        "cycles": 0,
        "last_cycle": None,
    })


# ─── API: Alerts History ────────────────────────────────────────

@app.route("/api/alerts")
def api_alerts() -> Any:
    return jsonify({"alerts": []})


# ─── API: Audit Trail ───────────────────────────────────────────

@app.route("/api/audit")
def api_audit() -> Any:
    conn = _get_conn()
    try:
        # Check if audit_trail table exists
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_trail'"
        ).fetchone()
        if not tables:
            return jsonify({"entries": [], "summary": {"total_entries": 0}})

        rows = conn.execute(
            "SELECT * FROM audit_trail ORDER BY timestamp DESC LIMIT 50"
        ).fetchall()
        entries = [dict(r) for r in rows]
        return jsonify({
            "entries": entries,
            "summary": {"total_entries": len(entries)},
        })
    finally:
        conn.close()


# ─── API: Kill Switch Toggle ────────────────────────────────────

@app.route("/api/kill-switch", methods=["POST"])
def api_kill_switch() -> Any:
    """Toggle kill switch (for dashboard button)."""
    cfg = _get_config()
    # In production this would persist to config file
    current = cfg.risk.kill_switch
    # Note: this only affects the in-memory config
    cfg.risk.kill_switch = not current
    return jsonify({
        "kill_switch": cfg.risk.kill_switch,
        "message": f"Kill switch {'ENGAGED' if cfg.risk.kill_switch else 'DISENGAGED'}",
    })


# ─── API: Execution Quality ─────────────────────────────────────

@app.route("/api/execution-quality")
def api_execution_quality() -> Any:
    conn = _get_conn()
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='fill_records'"
        ).fetchone()
        if not tables:
            return jsonify({
                "total_orders": 0,
                "avg_fill_rate": 0,
                "avg_slippage_bps": 0,
                "strategy_stats": {},
            })

        rows = conn.execute(
            "SELECT * FROM fill_records ORDER BY timestamp DESC LIMIT 100"
        ).fetchall()
        fills = [dict(r) for r in rows]
        return jsonify({
            "total_orders": len(fills),
            "fills": fills[:20],
        })
    finally:
        conn.close()


# ─── API: Configuration Summary ────────────────────────────────────

@app.route("/api/config")
def api_config() -> Any:
    cfg = _get_config()
    return jsonify({
        "scanning": {
            "min_volume_usd": cfg.scanning.min_volume_usd,
            "min_liquidity_usd": cfg.scanning.min_liquidity_usd,
            "preferred_types": cfg.scanning.preferred_types,
            "restricted_types": cfg.scanning.restricted_types,
        },
        "research": {
            "search_provider": cfg.research.search_provider,
            "max_sources": cfg.research.max_sources,
            "blocked_domains_count": len(cfg.research.blocked_domains),
        },
        "forecasting": {
            "llm_model": cfg.forecasting.llm_model,
            "min_evidence_quality": cfg.forecasting.min_evidence_quality,
            "calibration_method": cfg.forecasting.calibration_method,
        },
        "risk": cfg.risk.dict(),
        "execution": {
            "dry_run": cfg.execution.dry_run,
            "live_trading_enabled": is_live_trading_enabled(),
            "order_type": cfg.execution.default_order_type,
            "slippage_tolerance": cfg.execution.slippage_tolerance,
        },
    })


# ─── Runner ────────────────────────────────────────────────────────

def run_dashboard(
    config_path: str | None = None,
    host: str = "127.0.0.1",
    port: int = 2345,
    debug: bool = False,
) -> None:
    """Start the dashboard Flask server."""
    global _config, _db_path

    _config = load_config(config_path)
    _db_path = _config.storage.sqlite_path

    # Ensure DB directory exists
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

    # Ensure tables exist
    conn = _get_conn()
    _ensure_tables(conn)
    conn.close()

    print(f"\n  🚀 Polymarket Bot Dashboard")
    print(f"  ➜  http://{host}:{port}\n")

    app.run(host=host, port=port, debug=debug)
