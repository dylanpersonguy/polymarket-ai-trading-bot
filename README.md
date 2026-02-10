# Polymarket Research & Trading Bot

> **Production-grade** AI-powered research agent that discovers Polymarket prediction markets, gathers authoritative evidence, generates calibrated probability forecasts, and executes trades with strict risk controls.

⚠️ **This bot trades real money.** Start with `dry_run: true` (the default) and `paper-trade` commands.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLI (Click)                            │
│  scan │ research │ forecast │ paper-trade │ trade               │
├───────┴──────────┴──────────┴─────────────┴─────────────────────┤
│                                                                 │
│  Connectors        Research           Forecast                  │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐     │
│  │ Gamma API   │   │ Query Builder│   │ Feature Builder   │     │
│  │ CLOB API    │──▶│ Source Fetch │──▶│ LLM Forecaster   │     │
│  │ Web Search  │   │ Evidence Ext │   │ Calibrator        │     │
│  └─────────────┘   └──────────────┘   └──────────────────┘     │
│                                               │                 │
│  Policy                                       ▼                 │
│  ┌──────────────────────────────────────────────────┐           │
│  │ Edge Calc │ Risk Limits │ Position Sizer          │           │
│  └──────────────────────────────────────────────────┘           │
│                       │                                         │
│  Execution            ▼              Storage / Observability    │
│  ┌──────────────────────────┐   ┌───────────────────────┐      │
│  │ Order Builder            │   │ SQLite + Migrations   │      │
│  │ Order Router (dry/live)  │   │ structlog + Metrics   │      │
│  │ Cancel Manager           │   │ JSON Reports          │      │
│  └──────────────────────────┘   └───────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Details |
|---|---|
| **Market Discovery** | Gamma API scanning with volume/liquidity filters |
| **Market Classification** | Auto-classifies into MACRO, ELECTION, CORPORATE, WEATHER, SPORTS |
| **Source Whitelisting** | Primary domains per market type (bls.gov, sec.gov, etc.) |
| **Blocked Domains** | wikipedia.org, reddit.com, medium.com, twitter.com, etc. |
| **Evidence Extraction** | LLM-powered: metric_name, value, unit, date per bullet |
| **Calibrated Forecasts** | Platt-like logistic shrinkage + evidence quality penalties |
| **Risk Controls** | 9 independent checks, kill switch, daily loss limits |
| **Position Sizing** | Fractional Kelly criterion with confidence scaling |
| **Execution Safety** | Triple dry-run gate: order, config, env var |
| **Observability** | structlog JSON logging, metrics, run reports |

---

## Quick Start

### 1. Clone & Install

```bash
git clone <repo-url> polymarket-bot
cd polymarket-bot
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys:
#   POLYMARKET_API_KEY, SERPAPI_KEY (or BING_API_KEY or TAVILY_API_KEY), OPENAI_API_KEY
```

Review `config.yaml` for risk limits, scanning preferences, and research settings.

### 3. Run

```bash
# Scan for active markets
bot scan --limit 20

# Deep research on a specific market
bot research <CONDITION_ID>

# Full forecast pipeline (research → forecast → risk check → sizing)
bot forecast <CONDITION_ID>

# Paper trade (dry run, logged to DB)
bot paper-trade <CONDITION_ID>

# Live trade (requires ENABLE_LIVE_TRADING=true + config dry_run: false)
bot trade <CONDITION_ID>
```

### 4. Docker

```bash
docker compose build
docker compose run bot scan --limit 10
docker compose run bot forecast <CONDITION_ID>
```

---

## CLI Commands

| Command | Description |
|---|---|
| `bot scan` | Discover active markets from Gamma API |
| `bot research <id>` | Gather sources & extract evidence for a market |
| `bot forecast <id>` | Full pipeline: research → LLM forecast → calibrate → edge → risk → size |
| `bot paper-trade <id>` | Forecast + build order (always dry run) |
| `bot trade <id>` | Forecast + execute order (requires live trading enabled) |

### Common Flags

- `--limit N` — max markets to scan (default 50)
- `--config PATH` — path to config YAML (default `config.yaml`)
- `--verbose` — enable debug logging

---

## Market Type Classification

Markets are auto-classified by keyword matching:

| Type | Keywords (examples) | Primary Sources |
|---|---|---|
| MACRO | CPI, inflation, GDP, unemployment, Fed | bls.gov, federalreserve.gov, treasury.gov |
| ELECTION | election, vote, president, senate, poll | fec.gov, realclearpolitics.com, 538 |
| CORPORATE | earnings, revenue, stock, IPO, SEC | sec.gov, investor relations, bloomberg.com |
| WEATHER | hurricane, temperature, wildfire, NOAA | weather.gov, nhc.noaa.gov |
| SPORTS | NFL, NBA, FIFA, championship, playoff | espn.com, sports-reference.com |

---

## Evidence Quality Gates

Every evidence bullet **must** include:

```json
{
  "text": "CPI-U increased 3.1% YoY in January 2026",
  "metric_name": "CPI-U YoY",
  "metric_value": "3.1",
  "metric_unit": "percent",
  "metric_date": "2026-01-31",
  "confidence": 0.97,
  "citation": {
    "url": "https://www.bls.gov/...",
    "publisher": "Bureau of Labor Statistics",
    "authority_score": 1.0
  }
}
```

Markets with `evidence_quality < min_evidence_quality` (default 0.3) are **rejected** by risk limits.

---

## Risk Controls

Nine independent checks, **all** must pass:

1. **Kill Switch** — global halt
2. **Minimum Edge** — default 2%
3. **Max Daily Loss** — default $100
4. **Max Open Positions** — default 20
5. **Min Liquidity** — default $500
6. **Max Spread** — default 12%
7. **Evidence Quality** — default 0.3
8. **Market Type Restrictions** — configurable blocked types
9. **Clear Resolution** — market must have unambiguous resolution criteria

---

## Position Sizing

Uses **fractional Kelly criterion**:

$$f^* = \frac{p \cdot b - q}{b}$$

Where $p$ = calibrated probability, $q = 1-p$, $b$ = odds.

The raw Kelly fraction is then scaled by:
- `kelly_fraction` (default 0.25 = quarter-Kelly)
- `confidence` from forecaster
- Capped by `max_stake_per_trade_usd` and `max_bankroll_fraction`

---

## Execution Safety

Three independent dry-run gates prevent accidental live trading:

1. `order.dry_run` flag on the order itself
2. `config.execution.dry_run` in config.yaml
3. `ENABLE_LIVE_TRADING` environment variable

**All three** must allow live trading for an order to be submitted.

---

## Project Structure

```
polymarket-bot/
├── src/
│   ├── __init__.py
│   ├── cli.py                    # Click CLI entry point
│   ├── config.py                 # Pydantic config models
│   ├── connectors/
│   │   ├── polymarket_gamma.py   # Gamma REST API client
│   │   ├── polymarket_clob.py    # CLOB orderbook + signing
│   │   └── web_search.py         # SerpAPI / Bing / Tavily
│   ├── research/
│   │   ├── query_builder.py      # Site-restricted query generation
│   │   ├── source_fetcher.py     # Concurrent source gathering
│   │   └── evidence_extractor.py # LLM evidence extraction
│   ├── forecast/
│   │   ├── feature_builder.py    # 30+ market features
│   │   ├── llm_forecaster.py     # GPT-4 probability estimation
│   │   └── calibrator.py         # Platt-like calibration
│   ├── policy/
│   │   ├── edge_calc.py          # Edge & EV calculation
│   │   ├── risk_limits.py        # 9 independent risk checks
│   │   └── position_sizer.py     # Fractional Kelly sizing
│   ├── execution/
│   │   ├── order_builder.py      # Order construction
│   │   ├── order_router.py       # Dry/live routing
│   │   └── cancels.py            # Order cancellation
│   ├── storage/
│   │   ├── models.py             # Pydantic DB models
│   │   ├── migrations.py         # SQLite schema migrations
│   │   └── database.py           # CRUD operations
│   └── observability/
│       ├── logger.py             # structlog with redaction
│       ├── metrics.py            # In-process metrics
│       └── reports.py            # JSON run reports
├── tests/
│   ├── conftest.py
│   ├── test_market_parsing.py
│   ├── test_orderbook.py
│   ├── test_evidence_extraction.py
│   └── test_policy.py
├── config.yaml
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── example_output.json
└── README.md
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_policy.py -v

# Type checking
mypy src/

# Linting
ruff check src/ tests/
```

---

## Configuration Reference

See `config.yaml` for the full configuration. Key sections:

| Section | Purpose |
|---|---|
| `scanning` | Market discovery filters (preferred/restricted types) |
| `research` | Primary domains per market type, blocked domains |
| `forecasting` | Model name, min evidence quality, calibration params |
| `risk` | All risk limit thresholds |
| `execution` | Dry run toggle, slippage tolerance |
| `storage` | SQLite path |
| `observability` | Log level, file paths, metrics |

---

## Security Notes

- **Private keys** are never logged (structlog redaction processor)
- **API keys** loaded from environment only, never committed
- **Triple dry-run gate** prevents accidental live trading
- **Kill switch** immediately halts all trading
- Run as non-root user in Docker

---

## License

MIT
