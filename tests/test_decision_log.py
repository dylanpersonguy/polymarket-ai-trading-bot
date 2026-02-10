"""Tests for the /api/decision-log endpoint."""
from __future__ import annotations

import json
import sqlite3
import os
import tempfile
import uuid
from datetime import datetime, timedelta

import pytest

# The dashboard app uses a DB_PATH env var


@pytest.fixture()
def client():
    """Create a test client with a temporary database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    import importlib
    import src.dashboard.app as app_mod

    importlib.reload(app_mod)
    # Override the module-level DB path
    app_mod._db_path = db_path
    app_mod.app.config["TESTING"] = True
    with app_mod.app.test_client() as c:
        # Ensure tables exist
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        app_mod._ensure_tables(conn)
        conn.close()
        yield c, db_path

    os.unlink(db_path)


def _seed_data(db_path: str) -> None:
    """Insert sample candidates and forecasts for testing."""
    conn = sqlite3.connect(db_path)
    now = datetime.utcnow().isoformat()
    market_id = "0x_test_market_123"

    # Insert market metadata
    conn.execute(
        """INSERT OR REPLACE INTO markets
           (id, condition_id, question, market_type, category, volume,
            liquidity, end_date, resolution_source, first_seen, last_updated)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (market_id, "cond_1", "Will BTC exceed 100k?", "CRYPTO", "crypto",
         50000.0, 12000.0, "2025-03-01", "CoinGecko", now, now),
    )

    # Insert a forecast with evidence & reasoning
    evidence = [
        {
            "text": "Bitcoin has been trending upward for 3 months",
            "citation": {"url": "https://example.com", "publisher": "CoinDesk", "date": "2025-01-15", "title": "BTC Analysis"},
            "relevance": 0.85,
            "is_numeric": False,
            "confidence": 0.8,
        },
        {
            "text": "Institutional inflows reached $2.1B this week",
            "citation": {"url": "https://example2.com", "publisher": "Bloomberg", "date": "2025-01-14", "title": "Crypto Flows"},
            "relevance": 0.92,
            "is_numeric": True,
            "metric_name": "inflows",
            "metric_value": "2.1B",
            "confidence": 0.9,
        },
    ]
    triggers = ["Fed rate decision reversal", "Major exchange hack"]

    conn.execute(
        """INSERT INTO forecasts
           (id, market_id, question, market_type, implied_probability,
            model_probability, edge, confidence_level, evidence_quality,
            num_sources, decision, reasoning, evidence_json,
            invalidation_triggers_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (str(uuid.uuid4()), market_id, "Will BTC exceed 100k?", "CRYPTO",
         0.45, 0.62, 0.17, "HIGH", 0.78, 2, "TRADE",
         "The model estimates 62% probability based on strong institutional inflows and bullish technicals. The market at 45% underestimates momentum.",
         json.dumps(evidence), json.dumps(triggers), now),
    )

    # Insert a candidate (TRADE)
    conn.execute(
        """INSERT INTO candidates
           (cycle_id, market_id, question, market_type, implied_prob,
            model_prob, edge, evidence_quality, num_sources, confidence,
            decision, decision_reasons, stake_usd, order_status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (1, market_id, "Will BTC exceed 100k?", "CRYPTO",
         0.45, 0.62, 0.17, 0.78, 2, "HIGH",
         "TRADE", "All checks passed", 25.0, "simulated", now),
    )

    # Insert a NO TRADE candidate
    market_id2 = "0x_test_market_456"
    conn.execute(
        """INSERT INTO candidates
           (cycle_id, market_id, question, market_type, implied_prob,
            model_prob, edge, evidence_quality, num_sources, confidence,
            decision, decision_reasons, stake_usd, order_status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (1, market_id2, "Will it rain tomorrow?", "WEATHER",
         0.50, 0.52, 0.02, 0.3, 1, "LOW",
         "NO TRADE", "Edge below minimum; Low confidence", 0.0, "", now),
    )

    conn.commit()
    conn.close()


def test_decision_log_empty(client):
    """Empty DB returns empty entries."""
    c, _ = client
    resp = c.get("/api/decision-log")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "entries" in data
    assert "cycles" in data
    assert data["entries"] == []


def test_decision_log_with_data(client):
    """Returns rich decision entries with pipeline stages."""
    c, db_path = client
    _seed_data(db_path)

    resp = c.get("/api/decision-log")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["entries"]) == 2

    # Check the TRADE entry (should be first — most recent or same time)
    trade_entry = next(e for e in data["entries"] if e["decision"] == "TRADE")
    assert trade_entry["question"] == "Will BTC exceed 100k?"
    assert trade_entry["market_type"] == "CRYPTO"
    assert trade_entry["edge"] == 0.17
    assert trade_entry["confidence"] == "HIGH"
    assert trade_entry["reasoning"] != ""
    assert len(trade_entry["evidence_bullets"]) == 2
    assert len(trade_entry["invalidation_triggers"]) == 2

    # Check stages
    stages = trade_entry["stages"]
    assert len(stages) == 5  # Discovery, Research, Forecast, Risk, Execution
    assert stages[0]["name"] == "Discovery & Filter"
    assert stages[0]["status"] == "passed"
    assert stages[1]["name"] == "Research"
    assert stages[1]["details"]["num_sources"] == 2
    assert stages[2]["name"] == "Forecast"
    assert stages[2]["details"]["reasoning"] != ""
    assert stages[3]["name"] == "Risk Check"
    assert stages[3]["status"] == "passed"
    assert stages[4]["name"] == "Execution"
    assert stages[4]["details"]["stake_usd"] == 25.0


def test_decision_log_no_trade_entry(client):
    """NO TRADE entries have violations in risk stage."""
    c, db_path = client
    _seed_data(db_path)

    resp = c.get("/api/decision-log")
    data = resp.get_json()
    no_trade = next(e for e in data["entries"] if e["decision"] == "NO TRADE")
    assert no_trade["question"] == "Will it rain tomorrow?"

    stages = no_trade["stages"]
    assert len(stages) == 4  # No Execution stage for NO TRADE
    risk_stage = stages[3]
    assert risk_stage["name"] == "Risk Check"
    assert risk_stage["status"] == "blocked"
    assert len(risk_stage["details"]["violations"]) >= 1


def test_decision_log_cycle_filter(client):
    """Can filter by cycle ID."""
    c, db_path = client
    _seed_data(db_path)

    resp = c.get("/api/decision-log?cycle=1")
    data = resp.get_json()
    assert len(data["entries"]) == 2

    resp = c.get("/api/decision-log?cycle=999")
    data = resp.get_json()
    assert len(data["entries"]) == 0


def test_decision_log_cycles_list(client):
    """Returns list of available cycle IDs."""
    c, db_path = client
    _seed_data(db_path)

    resp = c.get("/api/decision-log")
    data = resp.get_json()
    assert 1 in data["cycles"]


def test_decision_log_limit(client):
    """Respects limit parameter."""
    c, db_path = client
    _seed_data(db_path)

    resp = c.get("/api/decision-log?limit=1")
    data = resp.get_json()
    assert len(data["entries"]) == 1


def test_decision_log_evidence_structure(client):
    """Evidence bullets preserve citation structure."""
    c, db_path = client
    _seed_data(db_path)

    resp = c.get("/api/decision-log")
    data = resp.get_json()
    trade_entry = next(e for e in data["entries"] if e["decision"] == "TRADE")
    bullets = trade_entry["evidence_bullets"]
    assert bullets[0]["citation"]["publisher"] == "CoinDesk"
    assert bullets[1]["relevance"] == 0.92
