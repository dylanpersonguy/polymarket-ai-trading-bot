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

from flask import Flask, jsonify, render_template, request, send_from_directory

import yaml

from src.config import BotConfig, load_config, is_live_trading_enabled
from src.observability.metrics import metrics

# ─── Flask app ──────────────────────────────────────────────────────

_here = Path(__file__).resolve().parent
_PROJECT_ROOT = _here.parent.parent
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
            evidence_json TEXT, invalidation_triggers_json TEXT,
            research_evidence_json TEXT DEFAULT '{}', created_at TEXT
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
        CREATE TABLE IF NOT EXISTS engine_state (
            key TEXT PRIMARY KEY, value TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id INTEGER, market_id TEXT, question TEXT, market_type TEXT,
            implied_prob REAL, model_prob REAL, edge REAL,
            evidence_quality REAL, num_sources INTEGER, confidence TEXT,
            decision TEXT, decision_reasons TEXT,
            stake_usd REAL DEFAULT 0, order_status TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS alerts_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT DEFAULT 'info', channel TEXT DEFAULT 'system',
            message TEXT, market_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
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
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        row = conn.execute(
            "SELECT value FROM engine_state WHERE key = 'drawdown'"
        ).fetchone()
        if row:
            dd = json.loads(row["value"])
            return jsonify({
                "peak_equity": dd.get("peak_equity", cfg.risk.bankroll),
                "current_equity": dd.get("current_equity", cfg.risk.bankroll),
                "drawdown_pct": dd.get("drawdown_pct", 0.0),
                "heat_level": dd.get("heat_level", 0),
                "kelly_multiplier": dd.get("kelly_multiplier", 1.0),
                "is_killed": dd.get("is_killed", False),
                "kill_switch_pct": cfg.drawdown.max_drawdown_pct,
                "warning_pct": cfg.drawdown.warning_drawdown_pct,
                "critical_pct": cfg.drawdown.critical_drawdown_pct,
                "max_drawdown_pct": cfg.drawdown.max_drawdown_pct,
            })
    except Exception:
        pass
    finally:
        conn.close()
    # Fallback when engine hasn't started yet
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
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        row = conn.execute(
            "SELECT value FROM engine_state WHERE key = 'engine_status'"
        ).fetchone()
        if row:
            state = json.loads(row["value"])
            return jsonify({
                "running": state.get("running", False),
                "scan_interval_minutes": state.get("scan_interval_minutes", cfg.engine.scan_interval_minutes),
                "max_markets_per_cycle": state.get("max_markets_per_cycle", cfg.engine.max_markets_per_cycle),
                "auto_start": state.get("auto_start", cfg.engine.auto_start),
                "paper_mode": state.get("paper_mode", cfg.engine.paper_mode),
                "cycles": state.get("cycle_count", 0),
                "last_cycle": state.get("last_cycle"),
                "live_trading": state.get("live_trading", False),
                "positions": state.get("positions", 0),
            })
    except Exception:
        pass
    finally:
        conn.close()
    # Fallback when engine hasn't started yet
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
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        # Check if alerts_log table exists
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='alerts_log'"
        ).fetchone()
        if not table_exists:
            return jsonify({"alerts": []})

        rows = conn.execute(
            "SELECT * FROM alerts_log ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        alerts = [dict(r) for r in rows]
        return jsonify({"alerts": alerts})
    finally:
        conn.close()


# ─── API: Candidates Log ────────────────────────────────────────

@app.route("/api/candidates")
def api_candidates() -> Any:
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        # Check if candidates table exists
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='candidates'"
        ).fetchone()
        if not table_exists:
            return jsonify({"candidates": []})

        limit = request.args.get("limit", 100, type=int)
        rows = conn.execute(
            "SELECT * FROM candidates ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        candidates = [dict(r) for r in rows]
        return jsonify({"candidates": candidates})
    finally:
        conn.close()


# ─── API: Filter Stats ──────────────────────────────────────────

@app.route("/api/filter-stats")
def api_filter_stats() -> Any:
    """Return the last pre-research filter stats from the engine."""
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        row = conn.execute(
            "SELECT value FROM engine_state WHERE key = 'engine_status'"
        ).fetchone()
        if not row:
            return jsonify({"filter_stats": None, "research_cache_size": 0})
        state = json.loads(row["value"])
        return jsonify({
            "filter_stats": state.get("filter_stats"),
            "research_cache_size": state.get("research_cache_size", 0),
        })
    finally:
        conn.close()


# ─── API: Decision Log ──────────────────────────────────────────

@app.route("/api/decision-log")
def api_decision_log() -> Any:
    """Rich decision log joining candidates with forecast evidence & reasoning."""
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        limit = request.args.get("limit", 50, type=int)
        cycle_id = request.args.get("cycle", None, type=int)

        # Get candidates (most recent first)
        if cycle_id is not None:
            cand_rows = conn.execute(
                "SELECT * FROM candidates WHERE cycle_id = ? ORDER BY created_at DESC",
                (cycle_id,),
            ).fetchall()
        else:
            cand_rows = conn.execute(
                "SELECT * FROM candidates ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()

        entries: list[dict[str, Any]] = []
        for c in cand_rows:
            cd = dict(c)
            market_id = cd.get("market_id", "")

            # Find matching forecast (closest in time)
            f_row = conn.execute(
                """SELECT * FROM forecasts
                   WHERE market_id = ?
                   ORDER BY ABS(julianday(created_at) - julianday(?)) ASC
                   LIMIT 1""",
                (market_id, cd.get("created_at", "")),
            ).fetchone()

            # Parse forecast enrichment data
            evidence_bullets: list[dict] = []
            reasoning = ""
            invalidation_triggers: list[str] = []
            research_evidence: dict[str, Any] = {}
            if f_row:
                fd = dict(f_row)
                reasoning = fd.get("reasoning", "") or ""

                # Parse rich research evidence (original sources with real URLs)
                try:
                    raw_research = fd.get("research_evidence_json", "{}") or "{}"
                    research_evidence = json.loads(raw_research)
                    if not isinstance(research_evidence, dict):
                        research_evidence = {}
                except (json.JSONDecodeError, TypeError):
                    research_evidence = {}

                # Use research evidence bullets if available (real citations),
                # fall back to LLM evidence
                if research_evidence.get("evidence"):
                    evidence_bullets = research_evidence["evidence"]
                else:
                    try:
                        evidence_bullets = json.loads(
                            fd.get("evidence_json", "[]") or "[]"
                        )
                        if not isinstance(evidence_bullets, list):
                            evidence_bullets = []
                    except (json.JSONDecodeError, TypeError):
                        evidence_bullets = []

                try:
                    invalidation_triggers = json.loads(
                        fd.get("invalidation_triggers_json", "[]") or "[]"
                    )
                    if not isinstance(invalidation_triggers, list):
                        invalidation_triggers = []
                except (json.JSONDecodeError, TypeError):
                    invalidation_triggers = []

            # Look up market metadata
            m_row = conn.execute(
                "SELECT volume, liquidity, end_date, resolution_source, category "
                "FROM markets WHERE id = ? LIMIT 1",
                (market_id,),
            ).fetchone()
            market_meta = dict(m_row) if m_row else {}

            # Build pipeline stages
            stages: list[dict[str, Any]] = []

            # Stage 1: Discovery & Filter
            stages.append({
                "name": "Discovery & Filter",
                "icon": "🔍",
                "status": "passed",
                "details": {
                    "market_type": cd.get("market_type", "UNKNOWN"),
                    "volume": market_meta.get("volume"),
                    "liquidity": market_meta.get("liquidity"),
                    "end_date": market_meta.get("end_date"),
                    "resolution_source": market_meta.get("resolution_source", ""),
                    "category": market_meta.get("category", ""),
                },
            })

            # Stage 2: Research
            research_status = "passed" if cd.get("num_sources", 0) > 0 else "skipped"
            research_details: dict[str, Any] = {
                "num_sources": cd.get("num_sources", 0),
                "evidence_quality": cd.get("evidence_quality", 0),
                "evidence_bullets": evidence_bullets[:5],
            }
            # Add rich research package data when available
            if research_evidence:
                research_details["summary"] = research_evidence.get("summary", "")
                research_details["contradictions"] = research_evidence.get(
                    "contradictions", []
                )
                research_details["quality_breakdown"] = research_evidence.get(
                    "independent_quality", {}
                )
                research_details["llm_quality_score"] = research_evidence.get(
                    "llm_quality_score", 0
                )
            stages.append({
                "name": "Research",
                "icon": "📚",
                "status": research_status,
                "details": research_details,
            })

            # Stage 3: Forecast
            has_forecast = cd.get("model_prob", 0) > 0
            stages.append({
                "name": "Forecast",
                "icon": "🎯",
                "status": "passed" if has_forecast else "skipped",
                "details": {
                    "implied_prob": cd.get("implied_prob", 0),
                    "model_prob": cd.get("model_prob", 0),
                    "edge": cd.get("edge", 0),
                    "confidence": cd.get("confidence", ""),
                    "reasoning": reasoning,
                    "invalidation_triggers": invalidation_triggers,
                },
            })

            # Stage 4: Risk Check
            decision = (cd.get("decision") or "").upper()
            reasons = cd.get("decision_reasons", "") or ""
            risk_passed = decision == "TRADE"
            stages.append({
                "name": "Risk Check",
                "icon": "⚠️",
                "status": "passed" if risk_passed else "blocked",
                "details": {
                    "decision": decision,
                    "reasons": reasons,
                    "violations": (
                        [r.strip() for r in reasons.split(";") if r.strip()]
                        if not risk_passed and reasons
                        else []
                    ),
                },
            })

            # Stage 5: Execution
            if decision == "TRADE":
                stages.append({
                    "name": "Execution",
                    "icon": "⚡",
                    "status": "executed",
                    "details": {
                        "stake_usd": cd.get("stake_usd", 0),
                        "order_status": cd.get("order_status", ""),
                    },
                })

            entries.append({
                "cycle_id": cd.get("cycle_id"),
                "market_id": market_id,
                "question": cd.get("question", ""),
                "market_type": cd.get("market_type", ""),
                "decision": decision,
                "implied_prob": cd.get("implied_prob", 0),
                "model_prob": cd.get("model_prob", 0),
                "edge": cd.get("edge", 0),
                "evidence_quality": cd.get("evidence_quality", 0),
                "num_sources": cd.get("num_sources", 0),
                "confidence": cd.get("confidence", ""),
                "stake_usd": cd.get("stake_usd", 0),
                "created_at": cd.get("created_at", ""),
                "stages": stages,
                "reasoning": reasoning,
                "evidence_bullets": evidence_bullets[:5],
                "invalidation_triggers": invalidation_triggers,
                "research_summary": research_evidence.get("summary", ""),
                "contradictions": research_evidence.get("contradictions", []),
                "quality_breakdown": research_evidence.get(
                    "independent_quality", {}
                ),
            })

        # Gather unique cycle IDs for the cycle selector
        cycle_rows = conn.execute(
            "SELECT DISTINCT cycle_id FROM candidates ORDER BY cycle_id DESC LIMIT 20"
        ).fetchall()
        cycles = [r["cycle_id"] for r in cycle_rows if r["cycle_id"] is not None]

        return jsonify({"entries": entries, "cycles": cycles})
    finally:
        conn.close()


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


# ─── API: Configuration (Full — all sections) ─────────────────────

@app.route("/api/config")
def api_config() -> Any:
    cfg = _get_config()
    return jsonify({
        "scanning": cfg.scanning.model_dump(),
        "research": cfg.research.model_dump(),
        "forecasting": cfg.forecasting.model_dump(),
        "ensemble": cfg.ensemble.model_dump(),
        "risk": cfg.risk.model_dump(),
        "drawdown": cfg.drawdown.model_dump(),
        "portfolio": cfg.portfolio.model_dump(),
        "timeline": cfg.timeline.model_dump(),
        "microstructure": cfg.microstructure.model_dump(),
        "execution": cfg.execution.model_dump(),
        "cache": cfg.cache.model_dump(),
        "engine": cfg.engine.model_dump(),
        "alerts": cfg.alerts.model_dump(),
        "observability": cfg.observability.model_dump(),
    })


# ─── API: Save Configuration ──────────────────────────────────────

_CONFIG_PATH: Path = _PROJECT_ROOT / "config.yaml"

@app.route("/api/config", methods=["POST"])
def api_config_save() -> Any:
    """Validate and save config changes to config.yaml, then hot-reload."""
    global _config
    data = request.get_json(force=True)
    if not data or not isinstance(data, dict):
        return jsonify({"ok": False, "error": "Invalid JSON body"}), 400

    try:
        # Load current config as dict, merge changes
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH) as f:
                current_raw: dict[str, Any] = yaml.safe_load(f) or {}
        else:
            current_raw = {}

        # Deep-merge incoming sections into current raw config
        for section, values in data.items():
            if isinstance(values, dict):
                if section not in current_raw:
                    current_raw[section] = {}
                current_raw[section].update(values)
            else:
                current_raw[section] = values

        # Validate with Pydantic (raises if invalid)
        new_config = BotConfig(**current_raw)

        # Write to YAML
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_CONFIG_PATH, "w") as f:
            yaml.dump(
                current_raw,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        # Hot-reload in memory
        _config = new_config

        return jsonify({
            "ok": True,
            "message": "Configuration saved and reloaded",
            "sections_updated": list(data.keys()),
        })
    except Exception as exc:
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 422


# ─── API: Reset Configuration ─────────────────────────────────────

@app.route("/api/config/reset", methods=["POST"])
def api_config_reset() -> Any:
    """Reset config to defaults (delete config.yaml), reload."""
    global _config
    try:
        if _CONFIG_PATH.exists():
            _CONFIG_PATH.unlink()
        _config = BotConfig()
        return jsonify({"ok": True, "message": "Configuration reset to defaults"})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


# ─── API: Export Data ──────────────────────────────────────────────

@app.route("/api/export/<table_name>")
def api_export(table_name: str) -> Any:
    """Export table data as JSON (for CSV conversion on client)."""
    allowed = {"forecasts", "trades", "positions", "markets"}
    if table_name not in allowed:
        return jsonify({"error": f"Unknown table: {table_name}"}), 404
    conn = _get_conn()
    _ensure_tables(conn)
    try:
        rows = conn.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC").fetchall()
        data = [dict(r) for r in rows]
        return jsonify({"table": table_name, "count": len(data), "rows": data})
    finally:
        conn.close()


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
