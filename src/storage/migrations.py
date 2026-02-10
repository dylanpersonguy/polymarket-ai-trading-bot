"""Database migrations — create and upgrade schema."""

from __future__ import annotations

import sqlite3

from src.observability.logger import get_logger

log = get_logger(__name__)

SCHEMA_VERSION = 3

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
    2: [
        # Audit trail table
        """
        CREATE TABLE IF NOT EXISTS audit_trail (
            id TEXT PRIMARY KEY,
            timestamp REAL NOT NULL,
            market_id TEXT,
            decision TEXT,
            stage TEXT,
            data_json TEXT,
            checksum TEXT
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_trail(timestamp);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_market ON audit_trail(market_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_audit_decision ON audit_trail(decision);
        """,

        # Calibration history
        """
        CREATE TABLE IF NOT EXISTS calibration_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forecast_prob REAL NOT NULL,
            actual_outcome REAL NOT NULL,
            recorded_at REAL NOT NULL,
            market_id TEXT
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_calibration_recorded ON calibration_history(recorded_at);
        """,

        # Fill tracking
        """
        CREATE TABLE IF NOT EXISTS fill_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            market_id TEXT,
            expected_price REAL,
            fill_price REAL,
            size_ordered REAL,
            size_filled REAL,
            slippage_bps REAL,
            time_to_fill_secs REAL,
            execution_strategy TEXT,
            timestamp REAL
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_fills_order ON fill_records(order_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_fills_market ON fill_records(market_id);
        """,

        # Enhanced positions table with more tracking fields
        """
        CREATE TABLE IF NOT EXISTS positions_v2 (
            market_id TEXT PRIMARY KEY,
            question TEXT,
            category TEXT,
            event_slug TEXT,
            side TEXT,
            size_usd REAL,
            entry_price REAL,
            entry_time REAL,
            current_price REAL DEFAULT 0,
            unrealised_pnl REAL DEFAULT 0,
            realised_pnl REAL DEFAULT 0,
            status TEXT DEFAULT 'open',
            exit_time REAL DEFAULT 0,
            exit_price REAL DEFAULT 0,
            exit_reason TEXT DEFAULT '',
            entry_model_prob REAL DEFAULT 0,
            entry_edge REAL DEFAULT 0,
            entry_confidence TEXT DEFAULT 'LOW',
            stop_loss_price REAL DEFAULT 0,
            take_profit_price REAL DEFAULT 0,
            max_unrealised_pnl REAL DEFAULT 0,
            min_unrealised_pnl REAL DEFAULT 0
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_posv2_status ON positions_v2(status);
        """,

        # Drawdown state
        """
        CREATE TABLE IF NOT EXISTS drawdown_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            equity REAL,
            peak_equity REAL,
            drawdown_pct REAL,
            heat_level INTEGER
        );
        """,

        # Event triggers
        """
        CREATE TABLE IF NOT EXISTS event_triggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id TEXT,
            trigger_type TEXT,
            severity TEXT,
            details TEXT,
            timestamp REAL
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_events_market ON event_triggers(market_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_events_timestamp ON event_triggers(timestamp);
        """,
    ],
    3: [
        # Engine state — persisted between engine and dashboard processes
        """
        CREATE TABLE IF NOT EXISTS engine_state (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at REAL
        );
        """,
        # Candidate log — every market evaluated per cycle
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id INTEGER NOT NULL,
            market_id TEXT NOT NULL,
            question TEXT,
            market_type TEXT,
            implied_prob REAL,
            model_prob REAL,
            edge REAL,
            evidence_quality REAL,
            num_sources INTEGER DEFAULT 0,
            confidence TEXT,
            decision TEXT,
            decision_reasons TEXT,
            stake_usd REAL DEFAULT 0,
            order_status TEXT DEFAULT '',
            created_at TEXT
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_candidates_cycle ON candidates(cycle_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_candidates_created ON candidates(created_at);
        """,
        # Alerts log — persisted alerts for dashboard
        """
        CREATE TABLE IF NOT EXISTS alerts_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            channel TEXT DEFAULT 'system',
            message TEXT NOT NULL,
            market_id TEXT DEFAULT '',
            created_at TEXT
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts_log(created_at);
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
