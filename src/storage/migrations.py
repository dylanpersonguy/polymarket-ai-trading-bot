"""Database migrations — create and upgrade schema."""

from __future__ import annotations

import sqlite3

from src.observability.logger import get_logger

log = get_logger(__name__)

SCHEMA_VERSION = 1

_MIGRATIONS: dict[int, list[str]] = {
    1: [
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS markets (
            id TEXT PRIMARY KEY,
            condition_id TEXT,
            question TEXT,
            market_type TEXT,
            category TEXT,
            volume REAL DEFAULT 0,
            liquidity REAL DEFAULT 0,
            end_date TEXT,
            resolution_source TEXT,
            first_seen TEXT,
            last_updated TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS forecasts (
            id TEXT PRIMARY KEY,
            market_id TEXT NOT NULL,
            question TEXT,
            market_type TEXT,
            implied_probability REAL,
            model_probability REAL,
            edge REAL,
            confidence_level TEXT,
            evidence_quality REAL,
            num_sources INTEGER,
            decision TEXT,
            reasoning TEXT,
            evidence_json TEXT,
            invalidation_triggers_json TEXT,
            created_at TEXT,
            FOREIGN KEY (market_id) REFERENCES markets(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            order_id TEXT UNIQUE,
            market_id TEXT NOT NULL,
            token_id TEXT,
            side TEXT,
            price REAL,
            size REAL,
            stake_usd REAL,
            status TEXT,
            dry_run INTEGER DEFAULT 1,
            created_at TEXT,
            FOREIGN KEY (market_id) REFERENCES markets(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS positions (
            market_id TEXT PRIMARY KEY,
            token_id TEXT,
            direction TEXT,
            entry_price REAL,
            size REAL,
            stake_usd REAL,
            current_price REAL,
            pnl REAL,
            opened_at TEXT
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_forecasts_market ON forecasts(market_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_trades_market ON trades(market_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_forecasts_created ON forecasts(created_at);
        """,
    ],
}


def run_migrations(conn: sqlite3.Connection) -> None:
    """Run all pending migrations."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")
    conn.commit()

    current = _get_current_version(conn)

    for version in sorted(_MIGRATIONS.keys()):
        if version <= current:
            continue
        log.info("migrations.running", version=version)
        for sql in _MIGRATIONS[version]:
            conn.execute(sql)
        conn.execute(
            "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
            (version,),
        )
        conn.commit()
        log.info("migrations.applied", version=version)

    final = _get_current_version(conn)
    log.info("migrations.complete", version=final)


def _get_current_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] if row and row[0] else 0
    except Exception:
        return 0
