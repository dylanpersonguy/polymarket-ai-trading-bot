"""Database — SQLite persistence layer.

Manages connections, runs migrations, and provides CRUD operations.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from src.config import StorageConfig
from src.storage.migrations import run_migrations
from src.storage.models import ForecastRecord, MarketRecord, PositionRecord, TradeRecord
from src.observability.logger import get_logger

log = get_logger(__name__)


class Database:
    """SQLite database for the bot."""

    def __init__(self, config: StorageConfig):
        self._config = config
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Open database connection and run migrations."""
        db_path = Path(self._config.sqlite_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        run_migrations(self._conn)
        log.info("database.connected", path=str(db_path))

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    # ── Markets ──────────────────────────────────────────────────────

    def upsert_market(self, market: MarketRecord) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO markets
                (id, condition_id, question, market_type, category,
                 volume, liquidity, end_date, resolution_source,
                 first_seen, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                market.id, market.condition_id, market.question,
                market.market_type, market.category, market.volume,
                market.liquidity, market.end_date, market.resolution_source,
                market.first_seen, market.last_updated,
            ),
        )
        self.conn.commit()

    def get_market(self, market_id: str) -> MarketRecord | None:
        row = self.conn.execute(
            "SELECT * FROM markets WHERE id = ?", (market_id,)
        ).fetchone()
        if row:
            return MarketRecord(**dict(row))
        return None

    # ── Forecasts ────────────────────────────────────────────────────

    def insert_forecast(self, forecast: ForecastRecord) -> str:
        fid = forecast.id or str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO forecasts
                (id, market_id, question, market_type,
                 implied_probability, model_probability, edge,
                 confidence_level, evidence_quality, num_sources,
                 decision, reasoning, evidence_json,
                 invalidation_triggers_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fid, forecast.market_id, forecast.question,
                forecast.market_type, forecast.implied_probability,
                forecast.model_probability, forecast.edge,
                forecast.confidence_level, forecast.evidence_quality,
                forecast.num_sources, forecast.decision,
                forecast.reasoning, forecast.evidence_json,
                forecast.invalidation_triggers_json, forecast.created_at,
            ),
        )
        self.conn.commit()
        return fid

    def get_forecasts(
        self, market_id: str | None = None, limit: int = 50
    ) -> list[ForecastRecord]:
        if market_id:
            rows = self.conn.execute(
                "SELECT * FROM forecasts WHERE market_id = ? ORDER BY created_at DESC LIMIT ?",
                (market_id, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM forecasts ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [ForecastRecord(**dict(r)) for r in rows]

    # ── Trades ───────────────────────────────────────────────────────

    def insert_trade(self, trade: TradeRecord) -> str:
        tid = trade.id or str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO trades
                (id, order_id, market_id, token_id, side,
                 price, size, stake_usd, status, dry_run, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tid, trade.order_id, trade.market_id, trade.token_id,
                trade.side, trade.price, trade.size, trade.stake_usd,
                trade.status, int(trade.dry_run), trade.created_at,
            ),
        )
        self.conn.commit()
        return tid

    def get_daily_pnl(self) -> float:
        """Get total PnL for today (placeholder — real impl would track fills)."""
        row = self.conn.execute(
            "SELECT COALESCE(SUM(stake_usd), 0) FROM trades WHERE date(created_at) = date('now')"
        ).fetchone()
        return float(row[0]) if row else 0.0

    # ── Positions ────────────────────────────────────────────────────

    def get_open_positions_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM positions").fetchone()
        return int(row[0]) if row else 0

    def upsert_position(self, pos: PositionRecord) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO positions
                (market_id, token_id, direction, entry_price,
                 size, stake_usd, current_price, pnl, opened_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pos.market_id, pos.token_id, pos.direction,
                pos.entry_price, pos.size, pos.stake_usd,
                pos.current_price, pos.pnl, pos.opened_at,
            ),
        )
        self.conn.commit()

    def remove_position(self, market_id: str) -> None:
        self.conn.execute("DELETE FROM positions WHERE market_id = ?", (market_id,))
        self.conn.commit()

    # ── Engine State ─────────────────────────────────────────────────

    def set_engine_state(self, key: str, value: str) -> None:
        """Persist engine state (for cross-process dashboard reads)."""
        import time as _time
        self.conn.execute(
            "INSERT OR REPLACE INTO engine_state (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, _time.time()),
        )
        self.conn.commit()

    def get_engine_state(self, key: str) -> str | None:
        row = self.conn.execute(
            "SELECT value FROM engine_state WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def get_all_engine_state(self) -> dict[str, str]:
        rows = self.conn.execute("SELECT key, value FROM engine_state").fetchall()
        return {r["key"]: r["value"] for r in rows}

    # ── Candidate Log ────────────────────────────────────────────────

    def insert_candidate(
        self,
        cycle_id: int,
        market_id: str,
        question: str,
        market_type: str,
        implied_prob: float,
        model_prob: float,
        edge: float,
        evidence_quality: float,
        num_sources: int,
        confidence: str,
        decision: str,
        decision_reasons: str,
        stake_usd: float,
        order_status: str,
    ) -> None:
        import datetime as _dt
        self.conn.execute(
            """INSERT INTO candidates
                (cycle_id, market_id, question, market_type, implied_prob,
                 model_prob, edge, evidence_quality, num_sources, confidence,
                 decision, decision_reasons, stake_usd, order_status, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                cycle_id, market_id, question, market_type, implied_prob,
                model_prob, edge, evidence_quality, num_sources, confidence,
                decision, decision_reasons, stake_usd, order_status,
                _dt.datetime.now(_dt.timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()

    def get_candidates(self, limit: int = 100) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM candidates ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Alerts Log ───────────────────────────────────────────────────

    def insert_alert(self, level: str, message: str, channel: str = "system", market_id: str = "") -> None:
        import datetime as _dt
        self.conn.execute(
            "INSERT INTO alerts_log (level, channel, message, market_id, created_at) VALUES (?,?,?,?,?)",
            (level, channel, message, market_id, _dt.datetime.now(_dt.timezone.utc).isoformat()),
        )
        self.conn.commit()

    def get_alerts(self, limit: int = 50) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM alerts_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Trades (extended) ────────────────────────────────────────────

    def get_trades(self, limit: int = 100) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM trades ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_open_positions(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM positions").fetchall()
        return [dict(r) for r in rows]
