<p align="center"># Polymarket Research & Trading Bot

  <h1 align="center">Polymarket AI Research Trading Bot</h1>

  <p align="center">> **Production-grade** AI-powered research agent that discovers Polymarket prediction markets, gathers authoritative evidence, generates calibrated probability forecasts, and executes trades with strict risk controls.

    <strong>Production-grade autonomous trading system for Polymarket prediction markets, powered by multi-model AI ensemble forecasting, real-time evidence gathering, and institutional-grade risk management.</strong>

  </p>⚠️ **This bot trades real money.** Start with `dry_run: true` (the default) and `paper-trade` commands.

  <p align="center">

    <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">---

    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">

    <img src="https://img.shields.io/badge/docker-ready-2496ED.svg" alt="Docker Ready">## Architecture

    <img src="https://img.shields.io/badge/status-active-success.svg" alt="Active">

  </p>```

</p>┌─────────────────────────────────────────────────────────────────┐

│                          CLI (Click)                            │

---│  scan │ research │ forecast │ paper-trade │ trade               │

├───────┴──────────┴──────────┴─────────────┴─────────────────────┤

## Table of Contents│                                                                 │

│  Connectors        Research           Forecast                  │

- [Overview](#overview)│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐     │

- [Architecture](#architecture)│  │ Gamma API   │   │ Query Builder│   │ Feature Builder   │     │

- [Core Pipeline](#core-pipeline)│  │ CLOB API    │──▶│ Source Fetch │──▶│ LLM Forecaster   │     │

- [Feature Breakdown](#feature-breakdown)│  │ Web Search  │   │ Evidence Ext │   │ Calibrator        │     │

  - [Market Discovery & Classification](#1-market-discovery--classification)│  └─────────────┘   └──────────────┘   └──────────────────┘     │

  - [Autonomous Research Engine](#2-autonomous-research-engine)│                                               │                 │

  - [Multi-Model AI Forecasting](#3-multi-model-ai-forecasting)│  Policy                                       ▼                 │

  - [Calibration & Self-Improvement](#4-calibration--self-improvement)│  ┌──────────────────────────────────────────────────┐           │

  - [Risk Management Framework](#5-risk-management-framework)│  │ Edge Calc │ Risk Limits │ Position Sizer          │           │

  - [Intelligent Execution](#6-intelligent-execution)│  └──────────────────────────────────────────────────┘           │

  - [Whale & Smart Money Intelligence](#7-whale--smart-money-intelligence)│                       │                                         │

  - [Liquid Market Scanner](#8-liquid-market-scanner)│  Execution            ▼              Storage / Observability    │

  - [Real-Time Monitoring Dashboard](#9-real-time-monitoring-dashboard)│  ┌──────────────────────────┐   ┌───────────────────────┐      │

  - [Observability & Alerting](#10-observability--alerting)│  │ Order Builder            │   │ SQLite + Migrations   │      │

- [Tech Stack](#tech-stack)│  │ Order Router (dry/live)  │   │ structlog + Metrics   │      │

- [Quick Start](#quick-start)│  │ Cancel Manager           │   │ JSON Reports          │      │

- [Configuration](#configuration)│  └──────────────────────────┘   └───────────────────────┘      │

- [CLI Reference](#cli-reference)└─────────────────────────────────────────────────────────────────┘

- [Deployment](#deployment)```

- [Project Structure](#project-structure)

- [Safety & Risk Controls](#safety--risk-controls)## Key Features

- [License](#license)

| Feature | Details |

---|---|---|

| **Market Discovery** | Gamma API scanning with volume/liquidity filters |

## Overview| **Market Classification** | Auto-classifies into MACRO, ELECTION, CORPORATE, WEATHER, SPORTS |

| **Source Whitelisting** | Primary domains per market type (bls.gov, sec.gov, etc.) |

This bot implements a complete, end-to-end autonomous trading pipeline for [Polymarket](https://polymarket.com) prediction markets. It combines web-scale evidence gathering, multi-model LLM probabilistic forecasting, and institutional-grade risk management into a single, self-contained system.| **Blocked Domains** | wikipedia.org, reddit.com, medium.com, twitter.com, etc. |

| **Evidence Extraction** | LLM-powered: metric_name, value, unit, date per bullet |

### What It Does| **Calibrated Forecasts** | Platt-like logistic shrinkage + evidence quality penalties |

| **Risk Controls** | 9 independent checks, kill switch, daily loss limits |

1. **Discovers** active prediction markets via the Polymarket Gamma API| **Position Sizing** | Fractional Kelly criterion with confidence scaling |

2. **Classifies** each market into 11 categories with researchability scoring| **Execution Safety** | Triple dry-run gate: order, config, env var |

3. **Researches** markets autonomously using site-restricted web searches against authoritative sources| **Observability** | structlog JSON logging, metrics, run reports |

4. **Extracts** structured evidence (metrics, dates, citations) using LLM-powered analysis

5. **Forecasts** independent probability estimates via a multi-model ensemble (GPT-4o, Claude 3.5, Gemini 1.5 Pro)---

6. **Calibrates** raw forecasts using Platt scaling, historical calibration, and evidence quality adjustments

7. **Calculates edge** over the market price with full transaction cost awareness## Quick Start

8. **Enforces 15+ risk checks** before any trade is allowed

9. **Sizes positions** using fractional Kelly criterion with drawdown-aware multipliers### 1. Clone & Install

10. **Executes** orders with smart routing (TWAP, iceberg, adaptive pricing)

11. **Monitors** positions in real-time with stop-loss, trailing stop, and resolution exit strategies```bash

12. **Learns** from resolved markets to improve future forecasts (calibration feedback loop)git clone <repo-url> polymarket-bot

cd polymarket-bot

> ⚠️ **This bot can trade real money.** It ships with `dry_run: true` by default. Paper trading mode is the default — no real orders are placed unless explicitly enabled via environment variable and configuration.python -m venv .venv

source .venv/bin/activate

---pip install -e ".[dev]"

```

## Architecture

### 2. Configure

```

┌──────────────────────────────────────────────────────────────────────────────┐```bash

│                          MONITORING DASHBOARD (Flask)                        │cp .env.example .env

│   9 Tabs: Overview │ Engine │ Positions │ Forecasts │ Risk │ Whales │ ...    │# Edit .env with your API keys:

├──────────────────────────────────────────────────────────────────────────────┤#   POLYMARKET_API_KEY, SERPAPI_KEY (or BING_API_KEY or TAVILY_API_KEY), OPENAI_API_KEY

│                                                                              │```

│  ┌──────────────┐   ┌──────────────────┐   ┌─────────────────────────────┐  │

│  │  CONNECTORS  │   │     RESEARCH     │   │         FORECAST            │  │Review `config.yaml` for risk limits, scanning preferences, and research settings.

│  │              │   │                  │   │                             │  │

│  │ Gamma API    │   │ Query Builder    │   │ Feature Builder             │  │### 3. Run

│  │ CLOB API     │──▶│ Source Fetcher   │──▶│ Multi-Model Ensemble        │  │

│  │ Data API     │   │ Evidence Extract │   │ (GPT-4o/Claude/Gemini)      │  │```bash

│  │ Web Search   │   │ Quality Scoring  │   │ Calibrator (Platt/Hist.)    │  │# Scan for active markets

│  │ WebSocket    │   └──────────────────┘   └─────────────────────────────┘  │bot scan --limit 20

│  │ API Pool     │                                      │                    │

│  │ Rate Limiter │                                      ▼                    │# Deep research on a specific market

│  └──────────────┘   ┌──────────────────────────────────────────────────┐    │bot research <CONDITION_ID>

│                     │                   POLICY                         │    │

│                     │                                                  │    │# Full forecast pipeline (research → forecast → risk check → sizing)

│                     │ Edge Calculator │ Risk Limits (15 checks)        │    │bot forecast <CONDITION_ID>

│                     │ Position Sizer (Kelly) │ Drawdown Manager        │    │

│                     │ Portfolio Risk │ Arbitrage │ Timeline Intel       │    │# Paper trade (dry run, logged to DB)

│                     └──────────────────────────────────────────────────┘    │bot paper-trade <CONDITION_ID>

│                                        │                                    │

│  ┌──────────────┐                      ▼              ┌──────────────────┐  │# Live trade (requires ENABLE_LIVE_TRADING=true + config dry_run: false)

│  │  ANALYTICS   │   ┌──────────────────────────┐      │    STORAGE       │  │bot trade <CONDITION_ID>

│  │              │   │       EXECUTION          │      │                  │  │```

│  │ Regime Det.  │   │                          │      │ SQLite + WAL     │  │

│  │ Whale Scan   │   │ Order Builder (TWAP/ICE) │      │ Schema Migr.     │  │### 4. Docker

│  │ Smart Entry  │   │ Order Router (dry/live)  │      │ Audit Trail      │  │

│  │ Adaptive Wt. │   │ Fill Tracker             │      │ TTL Cache        │  │```bash

│  │ Perf Track   │   │ Cancel Manager           │      │ Auto Backup      │  │docker compose build

│  │ Calib. Loop  │   └──────────────────────────┘      └──────────────────┘  │docker compose run bot scan --limit 10

│  └──────────────┘                                                           │docker compose run bot forecast <CONDITION_ID>

│                                                                              │```

│  ┌──────────────────────────────────────────────────────────────────────┐    │

│  │                        OBSERVABILITY                                 │    │---

│  │  Structured Logging (structlog) │ Metrics │ Alerts (TG/Discord/Slack)│    │

│  │  Sentry Integration │ JSON Reports │ API Cost Tracking               │    │## CLI Commands

│  └──────────────────────────────────────────────────────────────────────┘    │

└──────────────────────────────────────────────────────────────────────────────┘| Command | Description |

```|---|---|

| `bot scan` | Discover active markets from Gamma API |

---| `bot research <id>` | Gather sources & extract evidence for a market |

| `bot forecast <id>` | Full pipeline: research → LLM forecast → calibrate → edge → risk → size |

## Core Pipeline| `bot paper-trade <id>` | Forecast + build order (always dry run) |

| `bot trade <id>` | Forecast + execute order (requires live trading enabled) |

Each trading cycle follows a deterministic pipeline:

### Common Flags

```

Market Discovery ──▶ Classification ──▶ Pre-Research Filter ──▶ Web Research- `--limit N` — max markets to scan (default 50)

        │                   │                    │                    │- `--config PATH` — path to config YAML (default `config.yaml`)

        │            11 categories         Score 0-100          Site-restricted- `--verbose` — enable debug logging

        │            + researchability     Blocks junk          queries to .gov,

        │              scoring             markets              .edu, official---

        ▼                                                       sources

   Gamma API                                                        │## Market Type Classification

   (volume,                                                         ▼

    liquidity,                                              Evidence ExtractionMarkets are auto-classified by keyword matching:

    spread                                                  (LLM-powered)

    filters)                                                        │| Type | Keywords (examples) | Primary Sources |

                                                                    ▼|---|---|---|

                    Position Sizing ◀── Risk Check ◀── Edge Calc ◀── Forecast| MACRO | CPI, inflation, GDP, unemployment, Fed | bls.gov, federalreserve.gov, treasury.gov |

                         │               (15 gates)                (ensemble +| ELECTION | election, vote, president, senate, poll | fec.gov, realclearpolitics.com, 538 |

                    Kelly criterion                                calibration)| CORPORATE | earnings, revenue, stock, IPO, SEC | sec.gov, investor relations, bloomberg.com |

                    + drawdown adj.| WEATHER | hurricane, temperature, wildfire, NOAA | weather.gov, nhc.noaa.gov |

                         │| SPORTS | NFL, NBA, FIFA, championship, playoff | espn.com, sports-reference.com |

                         ▼

                    Order Execution ──▶ Position Monitoring ──▶ Exit Management---

                    (TWAP/Iceberg/       (WebSocket feed,       (stop-loss,

                     Adaptive)            event triggers)        trailing stop,## Evidence Quality Gates

                                                                 resolution)

```Every evidence bullet **must** include:



---```json

{

## Feature Breakdown  "text": "CPI-U increased 3.1% YoY in January 2026",

  "metric_name": "CPI-U YoY",

### 1. Market Discovery & Classification  "metric_value": "3.1",

  "metric_unit": "percent",

| Feature | Details |  "metric_date": "2026-01-31",

|---------|---------|  "confidence": 0.97,

| **Gamma API Integration** | Discovers active markets with volume, liquidity, and spread filtering |  "citation": {

| **11-Category Classifier** | MACRO, ELECTION, CORPORATE, LEGAL, TECHNOLOGY, SCIENCE, CRYPTO, REGULATION, GEOPOLITICS, SPORTS, ENTERTAINMENT |    "url": "https://www.bls.gov/...",

| **Researchability Scoring** | 0–100 score per market determining research budget allocation |    "publisher": "Bureau of Labor Statistics",

| **Pre-Research Filter** | Blocks low-quality markets before expensive API calls (reduces costs ~90%) |    "authority_score": 1.0

| **Keyword Blocking** | Auto-skips meme, social media, and untradeable markets |  }

| **Research Cooldown** | Prevents redundant re-research within configurable windows |}

```

The classifier uses 100+ regex rules mapping market questions to categories, subcategories, and recommended data sources — all without requiring any LLM calls.

Markets with `evidence_quality < min_evidence_quality` (default 0.3) are **rejected** by risk limits.

### 2. Autonomous Research Engine

---

The research pipeline gathers evidence autonomously using web search and full-content extraction:

## Risk Controls

- **Query Builder** — Generates targeted search queries per market type:

  - **Site-restricted queries** to authoritative sources (BLS.gov for macro, SEC.gov for corporate, FEC.gov for elections)Nine independent checks, **all** must pass:

  - **Metric-specific queries** with date scoping

  - **Contrarian queries** to surface opposing evidence1. **Kill Switch** — global halt

  - **Tiered budget** — research query count scales with researchability score2. **Minimum Edge** — default 2%

3. **Max Daily Loss** — default $100

- **Source Fetcher** — Orchestrates search execution:4. **Max Open Positions** — default 20

  - Pluggable search backends: SerpAPI, Bing, Tavily (with automatic fallback)5. **Min Liquidity** — default $500

  - Domain authority scoring (primary > secondary > unknown)6. **Max Spread** — default 12%

  - Full HTML content extraction via BeautifulSoup (not just snippets)7. **Evidence Quality** — default 0.3

  - Deduplication and blocked domain filtering8. **Market Type Restrictions** — configurable blocked types

  - Built-in caching with configurable TTL9. **Clear Resolution** — market must have unambiguous resolution criteria



- **Evidence Extractor** — LLM-powered structured extraction:---

  - Extracts: metric name, value, unit, date, source, URL for every fact

  - Identifies contradictions between sources## Position Sizing

  - Computes independent quality score (recency, authority, agreement, numeric density)

  - Strict extraction rules — only numbers, official statements, dates, and direct quotesUses **fractional Kelly criterion**:



### 3. Multi-Model AI Forecasting$$f^* = \frac{p \cdot b - q}{b}$$



The forecasting system produces calibrated probability estimates using an ensemble of frontier LLMs:Where $p$ = calibrated probability, $q = 1-p$, $b$ = odds.



| Model | Role | Default Weight |The raw Kelly fraction is then scaled by:

|-------|------|---------------|- `kelly_fraction` (default 0.25 = quarter-Kelly)

| **GPT-4o** (OpenAI) | Primary forecaster | 40% |- `confidence` from forecaster

| **Claude 3.5 Sonnet** (Anthropic) | Second opinion | 35% |- Capped by `max_stake_per_trade_usd` and `max_bankroll_fraction`

| **Gemini 1.5 Pro** (Google) | Third opinion | 25% |

---

**Ensemble Aggregation Methods:**

- **Trimmed Mean** (default) — Removes highest/lowest, averages remaining## Execution Safety

- **Median** — Robust to outlier models

- **Weighted** — Configurable per-model weightsThree independent dry-run gates prevent accidental live trading:



**Key Design Principles:**1. `order.dry_run` flag on the order itself

- Models forecast **independently** from evidence — they do not anchor to market price2. `config.execution.dry_run` in config.yaml

- Confidence levels (LOW / MEDIUM / HIGH) are calibrated to evidence quality3. `ENABLE_LIVE_TRADING` environment variable

- Graceful degradation — if some models fail, the system continues with remaining ones

- `min_models_required` ensures minimum quorum for a valid forecast**All three** must allow live trading for an order to be submitted.



### 4. Calibration & Self-Improvement---



The bot continuously improves through multiple feedback loops:## Project Structure



- **Platt Scaling** — Logistic compression that shrinks extreme probabilities toward 0.50```

- **Historical Calibration** — Learns from own forecast vs. outcome history using logistic regressionpolymarket-bot/

- **Evidence Quality Penalty** — Penalizes forecasts with low evidence quality├── src/

- **Contradiction Penalty** — Applies uncertainty discount when sources disagree│   ├── __init__.py

- **Calibration Feedback Loop** — Records every (forecast, outcome) pair; retrains calibrator every N resolutions│   ├── cli.py                    # Click CLI entry point

- **Adaptive Model Weighting** — Tracks per-model, per-category Brier scores; dynamically reweights ensemble based on historical accuracy│   ├── config.py                 # Pydantic config models

- **Brier Score Tracking** — Monitors forecast calibration quality over time│   ├── connectors/

│   │   ├── polymarket_gamma.py   # Gamma REST API client

### 5. Risk Management Framework│   │   ├── polymarket_clob.py    # CLOB orderbook + signing

│   │   └── web_search.py         # SerpAPI / Bing / Tavily

Institutional-grade risk controls with **15+ independent checks** — any single violation blocks the trade:│   ├── research/

│   │   ├── query_builder.py      # Site-restricted query generation

| # | Risk Check | Description |│   │   ├── source_fetcher.py     # Concurrent source gathering

|---|-----------|-------------|│   │   └── evidence_extractor.py # LLM evidence extraction

| 1 | Kill Switch | Manual emergency halt of all trading |│   ├── forecast/

| 2 | Drawdown Kill | Auto-engages when drawdown exceeds max threshold |│   │   ├── feature_builder.py    # 30+ market features

| 3 | Drawdown Heat | Reduces position size at warning/critical drawdown levels |│   │   ├── llm_forecaster.py     # GPT-4 probability estimation

| 4 | Max Stake | Per-market maximum bet size |│   │   └── calibrator.py         # Platt-like calibration

| 5 | Daily Loss Limit | Cumulative loss cap per day |│   ├── policy/

| 6 | Max Open Positions | Limits number of concurrent positions |│   │   ├── edge_calc.py          # Edge & EV calculation

| 7 | Minimum Edge | Net edge after fees must exceed threshold |│   │   ├── risk_limits.py        # 9 independent risk checks

| 8 | Minimum Liquidity | Skips illiquid markets |│   │   └── position_sizer.py     # Fractional Kelly sizing

| 9 | Maximum Spread | Rejects wide-spread markets |│   ├── execution/

| 10 | Evidence Quality | Minimum evidence quality threshold |│   │   ├── order_builder.py      # Order construction

| 11 | Confidence Filter | Rejects LOW confidence forecasts |│   │   ├── order_router.py       # Dry/live routing

| 12 | Implied Probability Floor | Blocks micro-probability markets |│   │   └── cancels.py            # Order cancellation

| 13 | Positive Edge Direction | Net edge must be positive after costs |│   ├── storage/

| 14 | Market Type Allowed | Enforces category whitelist/blacklist |│   │   ├── models.py             # Pydantic DB models

| 15 | Portfolio Exposure | Category and event concentration limits |│   │   ├── migrations.py         # SQLite schema migrations

│   │   └── database.py           # CRUD operations

**Additional Risk Modules:**│   └── observability/

│       ├── logger.py             # structlog with redaction

- **Drawdown Manager** — Heat-based system (4 levels) that progressively reduces Kelly fraction as drawdown deepens; auto-engages kill switch at max drawdown│       ├── metrics.py            # In-process metrics

- **Portfolio Risk Manager** — Monitors category exposure, event concentration, and correlated position limits│       └── reports.py            # JSON run reports

- **Position Sizer** — Fractional Kelly criterion with confidence, drawdown, timeline, volatility, regime, and category multipliers; capped by max stake and max bankroll fraction├── tests/

- **Arbitrage Detector** — Scans for pricing inconsistencies in complementary and multi-outcome markets│   ├── conftest.py

- **Timeline Intelligence** — Adjusts sizing and entry strategy based on resolution proximity│   ├── test_market_parsing.py

│   ├── test_orderbook.py

### 6. Intelligent Execution│   ├── test_evidence_extraction.py

│   └── test_policy.py

Smart order execution to minimize market impact and improve fill quality:├── config.yaml

├── pyproject.toml

- **Order Builder** — Constructs orders from position sizing with automatic strategy selection:├── Dockerfile

  - **Simple** — Single limit or market order for small positions├── docker-compose.yml

  - **TWAP** (Time-Weighted Average Price) — Splits large orders across time intervals├── .env.example

  - **Iceberg** — Hides true order size, showing only a fraction at a time├── .gitignore

  - **Adaptive Pricing** — Adjusts limit price based on orderbook depth and queue position├── example_output.json

└── README.md

- **Order Router** — Triple dry-run safety gate:```

  1. Order-level `dry_run` flag on each `OrderSpec`

  2. Config-level `execution.dry_run` setting---

  3. Environment variable `ENABLE_LIVE_TRADING` check

## Testing

- **Fill Tracker** — Monitors execution quality:

  - Fill rate, slippage (bps), time-to-fill```bash

  - Per-strategy performance stats# Run all tests

  - Feeds back into strategy selectionpytest



- **Position Manager** — Monitors all open positions with multiple exit strategies:# Run with coverage

  - Dynamic stop-loss (scaled by confidence/edge)pytest --cov=src --cov-report=term-missing

  - Trailing stop-loss (locks in gains)

  - Take-profit at resolution ($1.00 YES / $0.00 NO)# Run specific test file

  - Time-based exit (configurable max holding period)pytest tests/test_policy.py -v

  - Edge reversal exit (model probability flips)

  - Kill switch forced exit# Type checking

mypy src/

- **Smart Entry Calculator** — Optimizes entry prices using:

  - Orderbook depth analysis (support/resistance levels)# Linting

  - VWAP divergence (enter when price is below VWAP for buys)ruff check src/ tests/

  - Microstructure signals (flow imbalance, whale activity)```

  - Price momentum confirmation

---

### 7. Whale & Smart Money Intelligence

## Configuration Reference

Tracks top Polymarket traders and generates conviction signals:

See `config.yaml` for the full configuration. Key sections:

- **Wallet Scanner** — Monitors tracked wallets for position changes:

  - Delta detection (new entries, exits, size changes)| Section | Purpose |

  - Conviction scoring per market (whale count × dollar size)|---|---|

  - Signal strength classification (STRONG / MODERATE / WEAK)| `scanning` | Market discovery filters (preferred/restricted types) |

  - Edge boost/penalty based on whale-model agreement| `research` | Primary domains per market type, blocked domains |

| `forecasting` | Model name, min evidence quality, calibration params |

- **Leaderboard Integration** — Auto-discovers top wallets from the Polymarket leaderboard API:| `risk` | All risk limit thresholds |

  - Seeds top 50 by profit + top 50 by volume| `execution` | Dry run toggle, slippage tolerance |

  - Deduplicates and scores wallets by PnL, win rate, and activity| `storage` | SQLite path |

| `observability` | Log level, file paths, metrics |

- **Market Microstructure Analysis**:

  - Order flow imbalance across multiple time windows---

  - VWAP divergence from current price

  - Whale order detection (large trade alerts)## Security Notes

  - Trade arrival rate acceleration

  - Book depth ratio changes- **Private keys** are never logged (structlog redaction processor)

  - Smart money vs. retail flow estimation- **API keys** loaded from environment only, never committed

- **Triple dry-run gate** prevents accidental live trading

### 8. Liquid Market Scanner- **Kill switch** immediately halts all trading

- Run as non-root user in Docker

Multi-source whale discovery engine (v4) with API-level rate limit bypass:

---

- **7-Phase Discovery Pipeline:**

  1. **Phase 0 — Leaderboard Seeding:** Seeds top wallets from Polymarket Leaderboard API## License

  2. **Phase 1 — Market Discovery:** Fetches active markets via Gamma API

  3. **Phase 2 — Global Trade Scanning:** Scans recent trades from Data API with rotating offsetsMIT

  4. **Phase 2b — Per-Market Trade Scanning:** Targets top liquid markets for concentrated whale activity
  5. **Phase 3 — Address Ranking:** Ranks discovered addresses by volume, trade count, and size
  6. **Phase 4 — Deep Wallet Analysis:** Fetches full position data for top candidates
  7. **Phase 5 — Score & Save:** Computes composite whale scores and persists to database

- **API Pool (Multi-Endpoint Rate Limit Bypass):**
  - Rotates requests across multiple API endpoints with independent per-endpoint rate limiters
  - 3 selection strategies: round-robin, least-loaded, weighted-random
  - Auto-health management: endpoints auto-disable after consecutive failures, auto-recover after cooldown
  - Path-based routing: directs requests to compatible endpoints
  - Custom endpoint support via `config.yaml` for proxy servers

- **Smart Deduplication:** Skips recently-scanned addresses with configurable cooldown windows

### 9. Real-Time Monitoring Dashboard

Full-featured Flask web dashboard with glassmorphism UI and 9 interactive tabs:

| Tab | Features |
|-----|----------|
| **Overview** | Engine status, cycle count, markets scanned, live P&L, equity curve |
| **Trading Engine** | Start/stop engine, cycle history, current phase, pipeline visualization |
| **Positions** | Open positions with live P&L, closed trade history, resolution tracking |
| **Forecasts** | Recent forecasts with evidence, probability comparison, confidence levels |
| **Risk & Drawdown** | Drawdown gauge, heat level, Kelly multiplier, portfolio exposure |
| **Smart Money** | Tracked wallets, conviction signals, whale activity feed |
| **Liquid Scanner** | 7-phase pipeline status, discovered candidates, API pool stats |
| **Performance** | Win rate, ROI, Sharpe ratio, category breakdown, model accuracy |
| **Settings** | Environment status, config viewer, kill switch toggle |

- **API-key authentication** for dashboard access
- **Hot-reload** — config changes apply without restart
- **Real-time updates** via polling with live status indicators
- **Responsive design** with dark theme and glassmorphism styling

### 10. Observability & Alerting

- **Structured Logging** (structlog) — JSON-formatted logs with automatic sensitive data scrubbing
- **In-Process Metrics** — Counters, gauges, and histograms for all operations
- **API Cost Tracking** — Per-call cost estimation for all LLM and search API usage
- **Multi-Channel Alerts:**
  - Console (always on)
  - Telegram bot notifications
  - Discord webhooks
  - Slack webhooks
  - Configurable cooldowns and minimum alert levels
- **Alert Triggers:** Trade executions, drawdown warnings, kill switch activation, system errors, daily summaries
- **Sentry Integration** — Optional error tracking with automatic sensitive data scrubbing
- **JSON Run Reports** — Exportable reports with full forecast and trade data

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Language** | Python 3.9+ |
| **AI/LLM** | OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet), Google (Gemini 1.5 Pro) |
| **Web Framework** | Flask (dashboard) |
| **Database** | SQLite with WAL mode, schema migrations, auto-backup |
| **HTTP** | httpx (async), aiohttp, tenacity (retry logic) |
| **WebSocket** | websockets (real-time price streaming) |
| **ML** | scikit-learn (calibration), NumPy |
| **Web Scraping** | BeautifulSoup4, lxml |
| **CLI** | Click, Rich (formatted tables) |
| **Logging** | structlog (JSON structured logging) |
| **Config** | Pydantic (validation), YAML (hot-reloadable) |
| **Search** | SerpAPI, Bing, Tavily (pluggable backends) |
| **Deployment** | Docker, Docker Compose, systemd, Gunicorn |
| **Error Tracking** | Sentry (optional) |

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- API keys for at least one LLM provider (OpenAI recommended)
- API key for at least one search provider (SerpAPI recommended)

### 1. Clone & Install

```bash
git clone https://github.com/dylanpersonguy/polymarket-bot.git
cd polymarket-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# Required for forecasting
OPENAI_API_KEY=your-openai-key

# Required for research
SERPAPI_KEY=your-serpapi-key

# Optional: ensemble models
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Optional: dashboard authentication
DASHBOARD_API_KEY=your-dashboard-secret
```

### 3. Launch Dashboard

```bash
make dashboard
# Or directly:
.venv/bin/python -m src.cli dashboard
```

Visit `http://localhost:2345` to access the monitoring dashboard.

### 4. CLI Commands

```bash
# Scan for active markets
bot scan --limit 20

# Research a specific market
bot research --market <CONDITION_ID>

# Full forecast pipeline
bot forecast --market <CONDITION_ID>

# Paper trading simulation
bot paper-trade --days 30

# Start continuous trading engine
bot engine start

# View portfolio risk
bot portfolio

# Scan for arbitrage
bot arbitrage
```

---

## Configuration

All runtime configuration is managed via `config.yaml` with hot-reload support — changes take effect on the next cycle without restarting.

### Key Configuration Sections

| Section | Purpose |
|---------|---------|
| `scanning` | Market discovery filters (volume, liquidity, spread, categories) |
| `research` | Search settings (max sources, timeouts, domain whitelist/blacklist) |
| `forecasting` | LLM model selection, temperature, confidence thresholds |
| `ensemble` | Multi-model config, aggregation method, per-model weights |
| `risk` | Bankroll, max stake, daily loss limit, Kelly fraction, stop-loss/take-profit |
| `drawdown` | Heat system thresholds, auto-kill, recovery requirements |
| `portfolio` | Category exposure limits, event concentration, correlation limits |
| `execution` | Dry run toggle, order type, TWAP/iceberg settings, slippage tolerance |
| `storage` | Database path and type |
| `cache` | TTL settings for search, orderbook, LLM, and market list caches |
| `observability` | Log level/format, metrics, report output directory |
| `alerts` | Notification channels (Telegram, Discord, Slack), alert triggers |
| `wallet_scanner` | Whale tracking settings, conviction thresholds |
| `scanner.apiPool` | API endpoint pool strategy, custom proxy endpoints |
| `engine` | Cycle interval, max markets per cycle, paper mode toggle |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | GPT-4o for forecasting and evidence extraction |
| `SERPAPI_KEY` | Yes | Web search for research pipeline |
| `ANTHROPIC_API_KEY` | Optional | Claude 3.5 Sonnet for ensemble |
| `GOOGLE_API_KEY` | Optional | Gemini 1.5 Pro for ensemble |
| `BING_API_KEY` | Optional | Alternative search provider |
| `TAVILY_API_KEY` | Optional | Alternative search provider |
| `DASHBOARD_API_KEY` | Recommended | Protects dashboard with API key authentication |
| `POLYMARKET_API_KEY` | Live only | Polymarket CLOB API credentials |
| `POLYMARKET_API_SECRET` | Live only | CLOB API secret |
| `POLYMARKET_API_PASSPHRASE` | Live only | CLOB API passphrase |
| `POLYMARKET_PRIVATE_KEY` | Live only | Polygon wallet private key for signing |
| `ENABLE_LIVE_TRADING` | Live only | Must be `true` to enable real order placement |
| `SENTRY_DSN` | Optional | Sentry error tracking |

---

## CLI Reference

```
Usage: bot [OPTIONS] COMMAND [ARGS]...

Commands:
  scan          Scan and list candidate markets
  research      Research a specific market (evidence gathering)
  forecast      Full forecast pipeline (research → forecast → risk → sizing)
  paper-trade   Run paper trading simulation
  trade         Execute live trades (requires ENABLE_LIVE_TRADING=true)
  dashboard     Launch the monitoring dashboard web UI
  engine start  Start the continuous trading engine
  engine status Show engine status
  portfolio     Show portfolio risk report
  drawdown      Show current drawdown state
  arbitrage     Scan for arbitrage opportunities
  alerts        Show recent alerts
```

---

## Deployment

### Docker

```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f bot

# Run CLI commands
docker compose run bot scan --limit 20
docker compose run bot forecast --market <ID>

# Stop
docker compose down
```

### Makefile Shortcuts

```bash
make install     # Install production dependencies
make dev         # Install with dev dependencies
make dashboard   # Start Flask dashboard
make engine      # Start trading engine (headless)
make test        # Run test suite
make lint        # Run ruff linter
make format      # Auto-format code
make typecheck   # Run mypy type checker
make test-cov    # Run tests with coverage
```

### Production (Gunicorn + systemd)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions including systemd service configuration and Gunicorn setup.

---

## Project Structure

```
polymarket-bot/
├── config.yaml                 # Runtime configuration (hot-reloadable)
├── pyproject.toml              # Project metadata and dependencies
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Container orchestration
├── Makefile                    # Development shortcuts
├── .env.example                # Environment variable template
│
├── src/
│   ├── cli.py                  # Click CLI entry point
│   ├── config.py               # Pydantic config loader with hot-reload
│   │
│   ├── connectors/             # External API integrations
│   │   ├── polymarket_gamma.py # Market discovery & metadata (Gamma API)
│   │   ├── polymarket_clob.py  # Orderbook & order placement (CLOB API)
│   │   ├── polymarket_data.py  # Wallet positions & trades (Data API)
│   │   ├── web_search.py       # Pluggable search (SerpAPI/Bing/Tavily)
│   │   ├── ws_feed.py          # WebSocket real-time price streaming
│   │   ├── microstructure.py   # Order flow, VWAP, whale detection
│   │   ├── api_pool.py         # Multi-endpoint rate limit bypass
│   │   └── rate_limiter.py     # Token-bucket rate limiting
│   │
│   ├── research/               # Evidence gathering pipeline
│   │   ├── query_builder.py    # Site-restricted search query generation
│   │   ├── source_fetcher.py   # Source ranking & full-content extraction
│   │   └── evidence_extractor.py # LLM-powered structured evidence extraction
│   │
│   ├── forecast/               # Probability estimation
│   │   ├── feature_builder.py  # Market feature vector construction
│   │   ├── llm_forecaster.py   # Single-model LLM forecasting
│   │   ├── ensemble.py         # Multi-model ensemble (GPT-4o/Claude/Gemini)
│   │   └── calibrator.py       # Platt scaling & historical calibration
│   │
│   ├── policy/                 # Trading rules & risk management
│   │   ├── edge_calc.py        # Edge calculation with cost awareness
│   │   ├── risk_limits.py      # 15+ independent risk checks
│   │   ├── position_sizer.py   # Fractional Kelly criterion
│   │   ├── drawdown.py         # Heat-based drawdown management
│   │   ├── portfolio_risk.py   # Category/event exposure limits
│   │   ├── arbitrage.py        # Cross-market arbitrage detection
│   │   └── timeline.py         # Resolution timeline intelligence
│   │
│   ├── engine/                 # Core trading loop
│   │   ├── loop.py             # Main trading engine (coordinator)
│   │   ├── market_classifier.py# 11-category classifier (100+ rules)
│   │   ├── market_filter.py    # Pre-research quality filter
│   │   ├── position_manager.py # Position monitoring & exit strategies
│   │   └── event_monitor.py    # Price/volume spike re-research triggers
│   │
│   ├── execution/              # Order management
│   │   ├── order_builder.py    # TWAP, iceberg, adaptive order construction
│   │   ├── order_router.py     # Dry-run / live routing with triple safety
│   │   ├── fill_tracker.py     # Execution quality analytics
│   │   └── cancels.py          # Order cancellation (individual + kill switch)
│   │
│   ├── analytics/              # Intelligence & self-improvement
│   │   ├── wallet_scanner.py   # Whale/smart-money position tracking
│   │   ├── regime_detector.py  # Market regime detection
│   │   ├── calibration_feedback.py # Forecast vs. outcome learning loop
│   │   ├── adaptive_weights.py # Dynamic per-model weighting
│   │   ├── smart_entry.py      # Optimal entry price calculation
│   │   └── performance_tracker.py # Win rate, Sharpe, category breakdown
│   │
│   ├── storage/                # Persistence
│   │   ├── database.py         # SQLite with WAL mode
│   │   ├── models.py           # Pydantic data models
│   │   ├── migrations.py       # Schema versioning (10 migrations)
│   │   ├── audit.py            # Immutable decision audit trail (SHA-256)
│   │   ├── cache.py            # TTL cache with LRU eviction
│   │   └── backup.py           # Automated SQLite backup with rotation
│   │
│   ├── observability/          # Monitoring & alerting
│   │   ├── logger.py           # structlog with sensitive data scrubbing
│   │   ├── metrics.py          # In-process counters, gauges, histograms
│   │   ├── alerts.py           # Multi-channel (Telegram/Discord/Slack)
│   │   ├── reports.py          # JSON run report generation
│   │   └── sentry_integration.py # Optional Sentry error tracking
│   │
│   └── dashboard/              # Web monitoring UI
│       ├── app.py              # Flask application + scanner + engine
│       ├── templates/
│       │   └── index.html      # 9-tab dashboard (glassmorphism UI)
│       └── static/
│           ├── dashboard.js    # Frontend logic (live updates, charts)
│           └── style.css       # Dark theme styling
│
├── tests/                      # Test suite (pytest)
├── scripts/                    # Utility scripts
└── data/                       # Runtime data (gitignored)
```

---

## Safety & Risk Controls

This bot is designed with multiple layers of safety to prevent accidental or runaway trading:

### Triple Dry-Run Gate
Every order must pass three independent checks before reaching the Polymarket CLOB:
1. **Order-level** `dry_run` flag on each `OrderSpec`
2. **Config-level** `execution.dry_run: true` in `config.yaml`
3. **Environment-level** `ENABLE_LIVE_TRADING=true` must be explicitly set

### Drawdown Protection
- **4-level heat system** progressively reduces position sizes as drawdown deepens
- **Auto kill-switch** halts all trading when maximum drawdown is reached
- **Recovery requirements** — must demonstrate profitable trades before resuming full sizing

### Portfolio Guardrails
- Maximum exposure per market category (e.g., 40% MACRO, 35% ELECTION)
- Maximum exposure per single event
- Correlated position limits
- Per-category stake multipliers

### Sensitive Data Protection
- All credentials loaded exclusively from environment variables
- Structured logger automatically scrubs sensitive fields (private keys, API secrets, passwords)
- Sentry integration includes before-send scrubber
- `.env` files excluded from version control

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <sub>Built for the prediction market community</sub>
</p>
