# 🤖 Polymarket AI Trading Bot<div align="center"><div align="center"><p align="center"># Polymarket Research & Trading Bot



### Autonomous AI-Powered Trading System for Polymarket Prediction Markets



[![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org) [![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?style=flat)](LICENSE) [![Docker Ready](https://img.shields.io/badge/docker-ready-2496ED.svg?style=flat&logo=docker&logoColor=white)](Dockerfile)# 🤖 Polymarket AI Trading Bot



Multi-model AI ensemble forecasting · Autonomous evidence gathering · 15+ risk checks · Whale intelligence · Real-time dashboard



> ⚠️ **This bot trades real money.** It ships with `dry_run: true` by default. Three independent safety gates must be unlocked before any real order is placed.**Autonomous prediction market trading powered by AI research & multi-model forecasting**# Polymarket AI Research Trading Bot  <h1 align="center">Polymarket AI Research Trading Bot</h1>



---



[Features](#-features) · [Quick Start](#-quick-start) · [CLI Commands](#-cli-commands) · [Configuration](#-configuration) · [Dashboard](#-real-time-dashboard) · [Architecture](#-architecture) · [Deployment](#-deployment) · [Testing](#-testing) · [License](#-license)[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)



---[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)



## 📖 Overview[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](Dockerfile)**Production-grade autonomous trading system for [Polymarket](https://polymarket.com) prediction markets**  <p align="center">> **Production-grade** AI-powered research agent that discovers Polymarket prediction markets, gathers authoritative evidence, generates calibrated probability forecasts, and executes trades with strict risk controls.



A production-grade autonomous trading system for [Polymarket](https://polymarket.com) prediction markets. The bot runs a continuous loop that discovers markets, gathers evidence from authoritative sources, forecasts probabilities using an ensemble of frontier LLMs, applies institutional-grade risk management, and executes trades — all without human intervention.



### The 12-Step Pipeline*Discovers markets · Researches evidence · Forecasts probabilities · Manages risk · Executes trades*



Every 5 minutes, the bot runs this full cycle:



```> ⚠️ **Trades real money.** Ships with `dry_run: true` by default. Three safety gates must be unlocked for live trading.*Multi-model AI ensemble forecasting · Autonomous evidence gathering · 15+ risk checks · Whale intelligence · Real-time dashboard*    <strong>Production-grade autonomous trading system for Polymarket prediction markets, powered by multi-model AI ensemble forecasting, real-time evidence gathering, and institutional-grade risk management.</strong>

1.  Scan         →  Discover active markets via Polymarket Gamma API

2.  Classify     →  Categorize into 11 market types using 100+ regex rules

3.  Filter       →  Block low-quality markets before expensive API calls

4.  Research     →  Web search against authoritative sources per category</div>

5.  Extract      →  Pull structured evidence with metrics, dates, citations

6.  Forecast     →  Run GPT-4o, Claude 3.5, Gemini 1.5 Pro in parallel

7.  Calibrate    →  Apply Platt scaling + historical accuracy correction

8.  Edge Calc    →  Calculate net edge over market price (after fees)---[![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)  </p>⚠️ **This bot trades real money.** Start with `dry_run: true` (the default) and `paper-trade` commands.

9.  Risk Check   →  Run 15+ independent risk checks (any fail = no trade)

10. Size         →  Fractional Kelly criterion with 7 adjustment multipliers

11. Execute      →  TWAP, iceberg, or simple orders through triple safety gate

12. Monitor      →  Stop-loss, trailing stops, hold-to-resolution## 📋 What It Does[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?style=flat)](LICENSE)

```



---

This bot runs a fully autonomous trading loop on [Polymarket](https://polymarket.com). Every 5 minutes it:[![Docker Ready](https://img.shields.io/badge/docker-ready-2496ED.svg?style=flat&logo=docker&logoColor=white)](Dockerfile)  <p align="center">

## ✨ Features



### 🔍 Market Discovery & Classification

1. **Scans** for active prediction markets via the Polymarket API[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?style=flat)](https://github.com/astral-sh/ruff)

- Discovers markets from the **Polymarket Gamma API** with volume, liquidity, and spread filters

- **11-category classifier** — MACRO, ELECTION, CORPORATE, LEGAL, TECHNOLOGY, SCIENCE, CRYPTO, REGULATION, GEOPOLITICS, SPORTS, ENTERTAINMENT2. **Classifies** each market into 11 categories using 100+ pattern rules

- Pure regex classification — 100+ pattern rules, no LLM cost

- Each market gets a **researchability score** (0–100) that determines research budget3. **Filters** out low-quality markets before wasting API calls (~90% cost savings)    <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">---

- Pre-research filter blocks junk markets before expensive API calls (~90% cost savings)

- Configurable research cooldowns to prevent re-scanning the same market4. **Researches** top candidates using web search against authoritative sources



### 📚 Autonomous Research Engine5. **Extracts** structured evidence (every fact needs a metric, value, date, and citation)---



- **Query Builder** generates site-restricted searches per category:6. **Forecasts** probabilities using GPT-4o, Claude 3.5, and Gemini 1.5 Pro in parallel

  - `site:bls.gov` for macro, `site:sec.gov` for corporate, `site:fec.gov` for elections

- Includes **contrarian queries** to avoid confirmation bias7. **Calibrates** raw forecasts with Platt scaling and historical accuracy data    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">

- **3 pluggable search backends** — SerpAPI, Bing, Tavily — with automatic fallback chain

- **Full HTML extraction** via BeautifulSoup (not just search snippets)8. **Calculates edge** over the market price (after fees)

- **Domain authority scoring** — primary sources (1.0) > secondary (0.6) > unknown (0.3)

- Auto-filters low-quality domains (Wikipedia, Reddit, Medium, Twitter, TikTok)9. **Runs 15+ risk checks** — any single failure blocks the trade> ⚠️ **This bot can trade real money.** It ships with `dry_run: true` by default and requires three independent safety gates to be unlocked before any real order is placed. Always start with paper trading.

- Source caching with configurable TTL (default 1 hour)

10. **Sizes the position** with fractional Kelly criterion

### 🧠 Multi-Model AI Forecasting

11. **Executes** via TWAP, iceberg, or simple orders with a triple dry-run safety gate    <img src="https://img.shields.io/badge/docker-ready-2496ED.svg" alt="Docker Ready">## Architecture

- **Ensemble of 3 frontier LLMs** running in parallel:

  - GPT-4o (40% weight) — primary forecaster12. **Monitors** open positions with stop-loss, trailing stops, and hold-to-resolution

  - Claude 3.5 Sonnet (35% weight) — second opinion

  - Gemini 1.5 Pro (25% weight) — third opinion</div>

- **3 aggregation methods** — trimmed mean, median, or weighted average

- Models forecast independently from evidence — explicitly told not to anchor to market price---

- **Graceful degradation** — if a model fails, the ensemble continues with the rest

- **Adaptive weighting** — tracks per-model Brier scores by category and reweights over time    <img src="https://img.shields.io/badge/status-active-success.svg" alt="Active">



### 📐 Calibration & Self-Improvement## ✨ Features



- **Platt scaling** — logistic compression pulling extreme probabilities toward 0.50---

- **Historical calibration** — learns from past (forecast, outcome) pairs via logistic regression

- **Evidence quality penalty** — weak evidence → forecast pulled toward 0.50### 🔍 Market Discovery & Classification

- **Contradiction penalty** — conflicting sources → increased uncertainty

- **Ensemble spread penalty** — when models disagree (>10%), adds uncertainty  </p>```

- **Calibration feedback loop** — retrains automatically after 30+ resolved markets

- **Brier score tracking** — monitors forecast accuracy over time- Discovers markets from the **Polymarket Gamma API** with volume, liquidity, and spread filters



### 🛡️ Risk Management (15+ Checks)- **11-category classifier** (MACRO, ELECTION, CORPORATE, LEGAL, TECHNOLOGY, SCIENCE, CRYPTO, REGULATION, GEOPOLITICS, SPORTS, ENTERTAINMENT) — pure regex, no LLM needed## Table of Contents



Every trade must pass ALL of these — one failure blocks the trade:- Each market gets a **researchability score** (0–100) that determines research budget



- **Kill switch** — manual emergency halt- **Pre-research filter** blocks junk markets before expensive API calls</p>┌─────────────────────────────────────────────────────────────────┐

- **Drawdown auto-kill** — 20% max drawdown

- **Drawdown heat system** — 4 levels that progressively cut position sizes:- Configurable **research cooldowns** to prevent re-scanning the same market

  - Normal (< 10%) → full sizing

  - Warning (≥ 10%) → half sizing- [Overview](#overview)

  - Critical (≥ 15%) → quarter sizing

  - Max (≥ 20%) → all trading halted### 📚 Autonomous Research Engine

- **Max stake per market** — $50 default

- **Daily loss limit** — $500 default- [System Architecture](#system-architecture)│                          CLI (Click)                            │

- **Max open positions** — 25

- **Minimum net edge** — 4% after fees- **Query Builder** generates site-restricted searches per category — `site:bls.gov` for macro, `site:sec.gov` for corporate, `site:fec.gov` for elections

- **Minimum liquidity** — $2,000

- **Maximum spread** — 6%- Includes **contrarian queries** to avoid confirmation bias- [Core Pipeline](#core-pipeline)

- **Evidence quality threshold** — 0.55

- **Confidence filter** — MEDIUM minimum- **3 pluggable search backends** — SerpAPI, Bing, Tavily — with automatic fallback

- **Implied probability floor** — 5%

- **Positive edge direction** — must be positive after costs- **Full HTML extraction** via BeautifulSoup (not just search snippets)- [Feature Deep Dive](#feature-deep-dive)---│  scan │ research │ forecast │ paper-trade │ trade               │

- **Market type whitelist/blacklist** — configurable

- **Portfolio category exposure** — 35% max per category- **Domain authority scoring** — primary sources (1.0) > secondary (0.6) > unknown (0.3)

- **Timeline endgame check** — 48h near resolution

- **Blocked domains** — auto-filters Wikipedia, Reddit, Medium, Twitter, TikTok, etc.  - [1. Market Discovery & Classification](#1-market-discovery--classification)

**Portfolio risk** — caps exposure per category, per event, and limits correlated positions.

- **Source caching** with configurable TTL (default 1 hour)

**Arbitrage detection** — scans for mispriced complementary/multi-outcome markets.

  - [2. Autonomous Research Engine](#2-autonomous-research-engine)├───────┴──────────┴──────────┴─────────────┴─────────────────────┤

### ⚡ Execution Engine

### 🧠 Multi-Model AI Forecasting

- **Position sizing** — fractional Kelly criterion with 7 multipliers (confidence, drawdown, timeline, volatility, regime, category, liquidity)

- **Auto strategy selection:**  - [3. Multi-Model AI Forecasting](#3-multi-model-ai-forecasting)

  - Simple — single limit order for small trades

  - TWAP — splits large orders into 5 time-weighted slices- **Ensemble of 3 frontier LLMs** running in parallel:

  - Iceberg — shows only 20% of true order size

  - Adaptive — adjusts pricing based on orderbook depth  - GPT-4o (40% weight) — primary forecaster  - [4. Calibration & Self-Improvement](#4-calibration--self-improvement)## Table of Contents│                                                                 │

- **Triple dry-run safety gate:**

  - `dry_run` flag on each order object  - Claude 3.5 Sonnet (35% weight) — second opinion

  - `execution.dry_run` in config.yaml

  - `ENABLE_LIVE_TRADING` environment variable  - Gemini 1.5 Pro (25% weight) — third opinion  - [5. Risk Management Framework](#5-risk-management-framework)

  - All three must allow it for a real order to go through

- **Fill tracker** — monitors fill rate, slippage, and time-to-fill per strategy- **3 aggregation methods** — trimmed mean, median, or weighted average

- **6 exit strategies** — dynamic stop-loss, trailing stop, hold-to-resolution, time-based exit, edge reversal, kill switch forced exit

- Models forecast **independently from evidence** — explicitly told not to anchor to market price  - [6. Intelligent Execution Engine](#6-intelligent-execution-engine)│  Connectors        Research           Forecast                  │

### 🐋 Whale & Smart Money Intelligence

- **Graceful degradation** — if a model fails, the ensemble continues with the rest

- **Wallet scanner** — tracks top Polymarket traders seeded from the leaderboard

- **Delta detection** — spots new entries, exits, size increases/decreases- **Adaptive weighting** — tracks per-model Brier scores by category and reweights over time  - [7. Whale & Smart Money Intelligence](#7-whale--smart-money-intelligence)

- **Conviction scoring** — combines whale count × dollar size into a signal

- **Edge integration** — whales agree with model → +8% edge boost; disagree → -2% penalty

- **Leaderboard seeding** — auto-discovers top 50 wallets by profit + top 50 by volume

### 📐 Calibration & Self-Improvement  - [8. Multi-Source Liquid Scanner](#8-multi-source-liquid-scanner)- [Overview](#overview)│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐     │

### 🔎 Liquid Market Scanner (7-Phase Pipeline)



- **Phase 0** — Seeds top wallets from Polymarket leaderboard

- **Phase 1** — Fetches active markets via Gamma API- **Platt scaling** — logistic compression pulling extreme probabilities toward 0.50  - [9. Market Microstructure Analysis](#9-market-microstructure-analysis)

- **Phase 2** — Scans recent global trades to discover whale addresses

- **Phase 2b** — Targets top liquid markets for per-market whale scanning- **Historical calibration** — learns from past (forecast, outcome) pairs using logistic regression

- **Phase 3** — Ranks discovered addresses by volume and trade size

- **Phase 4** — Deep wallet analysis (full position data for top candidates)- **Evidence quality penalty** — weak evidence → forecast pulled toward 0.50  - [10. Real-Time Monitoring Dashboard](#10-real-time-monitoring-dashboard)- [Architecture](#architecture)│  │ Gamma API   │   │ Query Builder│   │ Feature Builder   │     │

- **Phase 5** — Scores and saves whale data to database

- **Contradiction penalty** — conflicting sources → increased uncertainty

**API Pool** — rotates requests across multiple endpoints with independent rate limiters:

- 3 strategies: round-robin, least-loaded, weighted-random- **Ensemble spread penalty** — when models disagree (>10%), adds uncertainty  - [11. Observability & Alerting](#11-observability--alerting)

- Auto-disables unhealthy endpoints, auto-recovers after cooldown

- Add custom proxy endpoints via config to multiply throughput- **Calibration feedback loop** — retrains calibrator automatically after 30+ resolved markets



### 📊 Market Microstructure- **Brier score tracking** — monitors forecast accuracy over time  - [12. Storage & Audit Trail](#12-storage--audit-trail)- [Core Pipeline](#core-pipeline)│  │ CLOB API    │──▶│ Source Fetch │──▶│ LLM Forecaster   │     │



- **Order flow imbalance** across 60min / 4hr / 24hr windows

- **VWAP divergence** — enter when price is below volume-weighted average

- **Whale order detection** — flags individual trades > $2,000### 🛡️ Risk Management (15+ Checks)- [Tech Stack](#tech-stack)

- **Trade acceleration** — detects unusual activity surges (>2× baseline)

- **Book depth ratio** — bid vs. ask pressure

- **Smart entry calculator** — combines all signals to find optimal entry price

Every trade must pass ALL of these — one failure = no trade:- [Installation & Setup](#installation--setup)- [Feature Breakdown](#feature-breakdown)│  │ Web Search  │   │ Evidence Ext │   │ Calibrator        │     │

### 📺 Real-Time Dashboard



9-tab Flask dashboard with glassmorphism dark theme on port `2345`:

| Check | Default |- [Configuration Reference](#configuration-reference)

- **Overview** — Engine status, cycle count, P&L, equity curve

- **Trading Engine** — Start/stop controls, cycle history, pipeline visualization|-------|---------|

- **Positions** — Open positions with live P&L, closed trade history

- **Forecasts** — Evidence breakdown, model vs. market probability, reasoning| Kill switch (manual emergency halt) | Off |- [CLI Reference](#cli-reference)  - [Market Discovery & Classification](#1-market-discovery--classification)│  └─────────────┘   └──────────────┘   └──────────────────┘     │

- **Risk & Drawdown** — Drawdown gauge, heat level, Kelly multiplier, exposure breakdown

- **Smart Money** — Tracked wallets, conviction signals, whale activity feed| Drawdown auto-kill | 20% max drawdown |

- **Liquid Scanner** — 7-phase pipeline status, discovered candidates, API pool health

- **Performance** — Win rate, ROI, Sharpe, category breakdown, model accuracy| Drawdown heat (progressive sizing reduction) | 4 levels |- [Deployment](#deployment)

- **Settings** — Environment status, config viewer, kill switch toggle

| Max stake per market | $50 |

Protected by `DASHBOARD_API_KEY`. Config hot-reloads without restart. Auto-refreshing with live status indicators.

| Daily loss limit | $500 |- [Testing](#testing)  - [Autonomous Research Engine](#2-autonomous-research-engine)│                                               │                 │

### 📡 Observability & Alerting

| Max open positions | 25 |

- **structlog** JSON logging with automatic sensitive data redaction

- **Multi-channel alerts** — Telegram, Discord, Slack (with cooldowns)| Minimum net edge (after fees) | 4% |- [Project Structure](#project-structure)

- **Alert triggers** — trades, drawdown warnings, kill switch, errors, daily summaries

- **Sentry integration** — optional error tracking with data scrubbing| Minimum liquidity | $2,000 |

- **API cost tracking** — per-call cost estimation for LLM and search usage

- **JSON run reports** — exportable reports saved to `reports/`| Maximum spread | 6% |- [Safety & Risk Controls](#safety--risk-controls)  - [Multi-Model AI Forecasting](#3-multi-model-ai-forecasting)│  Policy                                       ▼                 │



### 💾 Storage & Audit| Evidence quality threshold | 0.55 |



- **SQLite with WAL mode** — concurrent reads/writes, 10 auto-migrations| Confidence filter | MEDIUM minimum |- [API Cost Estimates](#api-cost-estimates)

- **Immutable audit trail** — every decision recorded with SHA-256 integrity checksums

- **TTL cache** — search (1hr), orderbook (30s), LLM (30min), market list (5min)| Implied probability floor | 5% |

- **Auto backup** — SQLite backup with rotation (max 10), triggered via `make backup`

| Positive edge direction | Must be positive after costs |- [License](#license)  - [Calibration & Self-Improvement](#4-calibration--self-improvement)│  ┌──────────────────────────────────────────────────┐           │

---

| Market type whitelist/blacklist | Configurable |

## 🚀 Quick Start

| Portfolio category exposure | 35% max per category |

### Prerequisites

| Timeline endgame check | 48h near resolution |

- Python 3.9+

- Git---  - [Risk Management Framework](#5-risk-management-framework)│  │ Edge Calc │ Risk Limits │ Position Sizer          │           │



### Installation**Drawdown heat system** — 4 levels that progressively cut position sizes:



```bash- Normal (< 10% drawdown) → full sizing

# Clone the repository

git clone https://github.com/dylanpersonguy/polymarket-ai-trading-bot.git- Warning (≥ 10%) → half sizing

cd polymarket-ai-trading-bot

- Critical (≥ 15%) → quarter sizing## Overview  - [Intelligent Execution](#6-intelligent-execution)│  └──────────────────────────────────────────────────┘           │

# Create virtual environment

python3 -m venv .venv- Max (≥ 20%) → all trading halted

source .venv/bin/activate



# Install

pip install -e ".[dev]"**Portfolio risk** — caps exposure per category, per event, and limits correlated positions.

```

This system implements a complete, end-to-end autonomous trading pipeline for Polymarket prediction markets. It combines web-scale evidence gathering, multi-model LLM probabilistic forecasting, and institutional-grade risk management into a single, self-contained platform.  - [Whale & Smart Money Intelligence](#7-whale--smart-money-intelligence)│                       │                                         │

### Configure

**Arbitrage detection** — scans for mispriced complementary/multi-outcome markets.

```bash

# Copy environment template

cp .env.example .env

### ⚡ Execution Engine

# Edit .env and add your API keys (at minimum OPENAI_API_KEY and SERPAPI_KEY)

```### What It Does — The 12-Step Pipeline  - [Liquid Market Scanner](#8-liquid-market-scanner)│  Execution            ▼              Storage / Observability    │



### Launch- **Position sizing** — fractional Kelly criterion with 7 multipliers (confidence, drawdown, timeline, volatility, regime, category, liquidity)



```bash- **Auto strategy selection:**

# Start the dashboard (paper trading, safe by default)

make dashboard  - **Simple** — single limit order for small trades



# Dashboard available at http://localhost:2345  - **TWAP** — splits large orders into 5 time-weighted slicesEvery trading cycle follows a deterministic pipeline, from market discovery through order execution and continuous monitoring:  - [Real-Time Monitoring Dashboard](#9-real-time-monitoring-dashboard)│  ┌──────────────────────────┐   ┌───────────────────────┐      │

```

  - **Iceberg** — shows only 20% of true order size

### Verify It's Working

  - **Adaptive pricing** — adjusts based on orderbook depth

```bash

# Scan for markets- **Triple dry-run safety gate:**

bot scan --limit 20

  1. `dry_run` flag on each order object| Step | Stage | Description |  - [Observability & Alerting](#10-observability--alerting)│  │ Order Builder            │   │ SQLite + Migrations   │      │

# Research a specific market

bot research --market <MARKET_ID>  2. `execution.dry_run` in config.yaml



# Run a full forecast pipeline  3. `ENABLE_LIVE_TRADING` environment variable|:----:|-------|-------------|

bot forecast --market <MARKET_ID>

```  - All three must be off for a real order to go through



### Docker- **Fill tracker** — monitors fill rate, slippage, and time-to-fill per strategy| 1 | **Discover** | Scans active prediction markets via the Polymarket Gamma API with volume, liquidity, and spread filters |- [Tech Stack](#tech-stack)│  │ Order Router (dry/live)  │   │ structlog + Metrics   │      │



```bash- **6 exit strategies** — dynamic stop-loss, trailing stop, hold-to-resolution, time-based exit, edge reversal, kill switch forced exit

cp .env.example .env   # add your API keys

docker compose up -d| 2 | **Classify** | Categorizes each market into 11 categories (MACRO, ELECTION, CORPORATE, LEGAL, TECHNOLOGY, SCIENCE, CRYPTO, REGULATION, GEOPOLITICS, SPORTS, ENTERTAINMENT) with researchability scoring using 100+ regex rules |

# Dashboard at http://localhost:2345

```### 🐋 Whale & Smart Money Intelligence



---| 3 | **Filter** | Pre-research quality filter blocks low-quality, unresearchable, and recently-scanned markets before expensive API calls (~90% cost reduction) |- [Quick Start](#quick-start)│  │ Cancel Manager           │   │ JSON Reports          │      │



## 🛠️ CLI Commands- **Wallet scanner** — tracks top Polymarket traders seeded from the leaderboard



```bash- **Delta detection** — spots new entries, exits, size increases/decreases| 4 | **Research** | Gathers evidence autonomously using site-restricted web searches against authoritative sources (BLS.gov, SEC.gov, FEC.gov, NOAA.gov, etc.) with full HTML content extraction |

bot scan --limit 20              # Discover active markets

bot research --market <ID>       # Research a specific market- **Conviction scoring** — combines whale count × dollar size into a signal

bot forecast --market <ID>       # Full pipeline: research → forecast → risk → size

bot paper-trade --market <ID>    # Simulated trade (always dry run)- **Edge integration** — whales agree with model → +8% edge boost; disagree → -2% penalty| 5 | **Extract** | LLM-powered structured evidence extraction — every fact must include metric name, value, unit, date, source URL, and publisher with authority scoring |- [Configuration](#configuration)│  └──────────────────────────┘   └───────────────────────┘      │

bot trade --market <ID>          # Live trade (requires ENABLE_LIVE_TRADING=true)

bot engine start                 # Start continuous trading loop- **Leaderboard seeding** — auto-discovers top 50 wallets by profit + top 50 by volume

bot engine status                # Show engine health

bot dashboard                    # Launch web dashboard| 6 | **Forecast** | Independent probability estimates via a multi-model ensemble (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro) with trimmed mean/median/weighted aggregation |

bot portfolio                    # Portfolio risk report

bot drawdown                     # Current drawdown state### 🔎 Liquid Market Scanner (7-Phase Pipeline)

bot arbitrage                    # Scan for arbitrage

bot alerts                       # Recent alert history| 7 | **Calibrate** | Adjusts raw forecasts using Platt scaling, historical logistic regression, evidence quality penalties, contradiction discounts, and ensemble disagreement penalties |- [CLI Reference](#cli-reference)└─────────────────────────────────────────────────────────────────┘

```

| Phase | What It Does |

---

|-------|-------------|| 8 | **Edge** | Calculates directional edge over market price with full transaction cost awareness (fees + gas), expected value per dollar, and break-even probability |

## ⚙️ Configuration

| 0 | Seeds top wallets from Polymarket leaderboard |

All configuration lives in `config.yaml` and `.env`. Here are the key environment variables:

| 1 | Fetches active markets via Gamma API || 9 | **Risk** | Enforces 15+ independent risk checks — any single violation blocks the trade. Includes kill switch, drawdown heat, daily loss limit, evidence quality gate, portfolio exposure limits, and more |- [Deployment](#deployment)```

### Required

| 2 | Scans recent global trades to discover whale addresses |

- `OPENAI_API_KEY` — GPT-4o forecasting & evidence extraction

- `SERPAPI_KEY` — Web search for research| 2b | Targets top liquid markets for per-market whale scanning || 10 | **Size** | Positions are sized using fractional Kelly criterion with 7 independent multipliers: confidence, drawdown heat, timeline proximity, volatility, regime, category, and liquidity caps |



### Optional (Ensemble & Search)| 3 | Ranks discovered addresses by volume and trade size |



- `ANTHROPIC_API_KEY` — Claude for ensemble forecasting| 4 | Deep wallet analysis — full position data for top candidates || 11 | **Execute** | Smart order routing with automatic strategy selection (Simple, TWAP, Iceberg, Adaptive Pricing) and triple dry-run safety gate |- [Project Structure](#project-structure)

- `GOOGLE_API_KEY` — Gemini for ensemble forecasting

- `BING_API_KEY` — Fallback search backend| 5 | Scores and saves whale data to database |

- `TAVILY_API_KEY` — Fallback search backend

| 12 | **Monitor** | Continuous position monitoring with dynamic stop-loss, trailing stops, edge reversal exits, time-based exits, and hold-to-resolution strategy |

### Dashboard & Alerts

**API Pool** — rotates requests across multiple endpoints with independent rate limiters:

- `DASHBOARD_API_KEY` — Dashboard authentication

- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — Telegram alerts- 3 strategies: round-robin, least-loaded, weighted-random- [Safety & Risk Controls](#safety--risk-controls)## Key Features

- `DISCORD_WEBHOOK_URL` — Discord alerts

- `SLACK_WEBHOOK_URL` — Slack alerts- Auto-disables unhealthy endpoints, auto-recovers after cooldown

- `SENTRY_DSN` — Error tracking

- Add custom proxy endpoints via config to multiply throughput---

### Live Trading (All Required for Real Orders)



- `POLYMARKET_API_KEY` — CLOB API credentials

- `POLYMARKET_API_SECRET` — CLOB API secret### 📊 Market Microstructure- [License](#license)

- `POLYMARKET_API_PASSPHRASE` — CLOB passphrase

- `POLYMARKET_PRIVATE_KEY` — Polygon wallet key for signing

- `ENABLE_LIVE_TRADING=true` — Must be explicitly set

- **Order flow imbalance** across 60min / 4hr / 24hr windows## System Architecture

### Enabling Live Trading

- **VWAP divergence** — enter when price is below volume-weighted average

```bash

# Live trading requires explicit opt-in via environment variable- **Whale order detection** — flags individual trades > $2,000| Feature | Details |

ENABLE_LIVE_TRADING=true bot engine start

```- **Trade acceleration** — detects unusual activity surges (>2× baseline)



> ⚠️ **Warning:** LIVE mode executes real trades with real funds. Start with `paper-trade` commands to validate your setup first.- **Book depth ratio** — bid vs. ask pressure```



---- **Smart entry calculator** — combines all signals to find optimal entry price



## 📺 Real-Time Dashboard┌──────────────────────────────────────────────────────────────────────────────────┐---|---|---|



The dashboard is served at `http://localhost:2345` with 9 tabs:### 📺 Real-Time Dashboard



- 📈 **Overview** — Engine status, total P&L, equity curve│                           MONITORING DASHBOARD (Flask :2345)                     │

- ⚙️ **Trading Engine** — Start/stop, cycle history, pipeline view

- 💼 **Positions** — Open + closed positions with P&L9-tab Flask dashboard with glassmorphism dark theme on port `2345`:

- 🧠 **Forecasts** — Model outputs, evidence, reasoning

- 🛡️ **Risk** — Drawdown gauge, heat level, exposure│    9 Tabs: Overview │ Engine │ Positions │ Forecasts │ Risk │ Whales │ ...       │| **Market Discovery** | Gamma API scanning with volume/liquidity filters |

- 🐋 **Smart Money** — Whale wallets, conviction signals

- 🔍 **Scanner** — 7-phase pipeline, API pool health| Tab | What's There |

- 📊 **Performance** — Win rate, Sharpe, Sortino, Calmar

- ⚙️ **Settings** — Config viewer, kill switch|-----|-------------|├──────────────────────────────────────────────────────────────────────────────────┤



Protected by API key. Auto-refreshing. Glassmorphism dark theme.| **Overview** | Engine status, cycle count, P&L, equity curve |



---| **Trading Engine** | Start/stop controls, cycle history, pipeline visualization |│                                                                                  │## Overview| **Market Classification** | Auto-classifies into MACRO, ELECTION, CORPORATE, WEATHER, SPORTS |



## 🏗️ Architecture| **Positions** | Open positions with live P&L, closed trade history |



```| **Forecasts** | Evidence breakdown, model vs. market probability, reasoning |│  ┌──────────────────┐   ┌────────────────────┐   ┌───────────────────────────┐   │

src/

├── cli.py                    # Click CLI (12 commands)| **Risk & Drawdown** | Drawdown gauge, heat level, Kelly multiplier, exposure breakdown |

├── config.py                 # 16 Pydantic config models + hot-reload

├── connectors/               # Gamma API, CLOB API, Data API, WebSocket, search, API pool| **Smart Money** | Tracked wallets, conviction signals, whale activity feed |│  │    CONNECTORS     │   │      RESEARCH      │   │        FORECAST           │   │| **Source Whitelisting** | Primary domains per market type (bls.gov, sec.gov, etc.) |

├── research/                 # Query builder, source fetcher, evidence extractor

├── forecast/                 # Feature builder, LLM forecaster, ensemble, calibrator| **Liquid Scanner** | 7-phase pipeline status, discovered candidates, API pool health |

├── policy/                   # Edge calc, risk limits, Kelly sizer, drawdown, portfolio, arbitrage

├── engine/                   # Trading loop, classifier, filter, position manager| **Performance** | Win rate, ROI, Sharpe, category breakdown, model accuracy |│  │                   │   │                    │   │                           │   │

├── execution/                # Order builder, router, fill tracker, cancels

├── analytics/                # Whale scanner, regime detector, calibration loop, performance| **Settings** | Environment status, config viewer, kill switch toggle |

├── storage/                  # SQLite + WAL, migrations, audit trail, cache, backup

├── observability/            # structlog, metrics, alerts, Sentry, reports│  │  Gamma API        │   │  Query Builder     │   │  Feature Builder (30+)    │   │This bot implements a complete, end-to-end autonomous trading pipeline for [Polymarket](https://polymarket.com) prediction markets. It combines web-scale evidence gathering, multi-model LLM probabilistic forecasting, and institutional-grade risk management into a single, self-contained system.| **Blocked Domains** | wikipedia.org, reddit.com, medium.com, twitter.com, etc. |

└── dashboard/                # Flask app, glassmorphism UI, 9 tabs

```- Protected by `DASHBOARD_API_KEY`



Key design decisions:- Config hot-reloads without restart│  │  CLOB API         │──▶│  Source Fetcher    │──▶│  LLM Forecaster           │   │



- **Pipeline architecture** — 12 deterministic steps per cycle- Auto-refreshing with live status indicators

- **Triple safety gate** — 3 independent checks before any real order

- **Paper-first** — everything defaults to simulation mode│  │  Data API         │   │  Evidence Extract  │   │  Multi-Model Ensemble     │   │| **Evidence Extraction** | LLM-powered: metric_name, value, unit, date per bullet |

- **Zero external services** — SQLite, no Redis/Postgres/RabbitMQ required

- **Modular** — each subsystem is independently testable### 📡 Observability & Alerting



---│  │  Web Search       │   │  Quality Scoring   │   │  (GPT-4o/Claude/Gemini)   │   │



## 🚢 Deployment- **structlog** JSON logging with automatic sensitive data redaction



### Development- **Multi-channel alerts** — Telegram, Discord, Slack (with cooldowns)│  │  WebSocket Feed   │   └────────────────────┘   │  Calibrator               │   │### What It Does| **Calibrated Forecasts** | Platt-like logistic shrinkage + evidence quality penalties |



```bash- **Alert triggers** — trades, drawdown warnings, kill switch, errors, daily summaries

make dashboard

```- **Sentry integration** — optional error tracking with data scrubbing│  │  API Pool         │                            └───────────────────────────┘   │



### Docker- **API cost tracking** — per-call cost estimation for LLM and search usage



```bash- **JSON run reports** — exportable reports saved to `reports/`│  │  Rate Limiter     │                                        │                   │| **Risk Controls** | 9 independent checks, kill switch, daily loss limits |

docker compose up -d

```



### Production (systemd)### 💾 Storage & Audit│  └──────────────────┘                                         ▼                   │



```ini

[Unit]

Description=Polymarket AI Trading Bot- **SQLite with WAL mode** — concurrent reads/writes, 10 auto-migrations│                         ┌──────────────────────────────────────────────────────┐   │1. **Discovers** active prediction markets via the Polymarket Gamma API| **Position Sizing** | Fractional Kelly criterion with confidence scaling |

After=network.target

- **Immutable audit trail** — every decision recorded with SHA-256 integrity checksums

[Service]

Type=simple- **TTL cache** — search (1hr), orderbook (30s), LLM (30min), market list (5min)│                         │                     POLICY                           │   │

User=botuser

WorkingDirectory=/opt/polymarket-ai-trading-bot- **Auto backup** — SQLite backup with rotation (max 10), triggered via `make backup`

EnvironmentFile=/opt/polymarket-ai-trading-bot/.env

ExecStart=/opt/polymarket-ai-trading-bot/.venv/bin/gunicorn \│                         │                                                      │   │2. **Classifies** each market into 11 categories with researchability scoring| **Execution Safety** | Triple dry-run gate: order, config, env var |

    --bind 0.0.0.0:2345 --workers 2 --threads 4 --timeout 120 \

    src.dashboard.app:app---

Restart=always

│                         │  Edge Calculator │ Risk Limits (15+ checks)          │   │

[Install]

WantedBy=multi-user.target## 🚀 Quick Start

```

│                         │  Position Sizer (Kelly) │ Drawdown Manager (4 heat)  │   │3. **Researches** markets autonomously using site-restricted web searches against authoritative sources| **Observability** | structlog JSON logging, metrics, run reports |

**Going live:** Start on Mumbai testnet (`POLYMARKET_CHAIN_ID=80001`), validate everything, then switch to mainnet (`137`). See [DEPLOYMENT.md](DEPLOYMENT.md) for the full guide.

```bash

---

# Clone & install│                         │  Portfolio Risk │ Arbitrage │ Timeline Intelligence   │   │

## 🧪 Testing

git clone https://github.com/dylanpersonguy/polymarket-ai-trading-bot.git

```bash

make test        # Run all testscd polymarket-ai-trading-bot│                         └──────────────────────────────────────────────────────┘   │4. **Extracts** structured evidence (metrics, dates, citations) using LLM-powered analysis

make test-cov    # Tests with coverage

make lint        # Ruff linterpython3 -m venv .venv && source .venv/bin/activate

make format      # Auto-format

make typecheck   # mypy strict modepip install -e ".[dev]"│                                               │                                   │

```



---

# Configure│  ┌──────────────────┐                         ▼            ┌──────────────────┐   │5. **Forecasts** independent probability estimates via a multi-model ensemble (GPT-4o, Claude 3.5, Gemini 1.5 Pro)---

## 🔒 Security

cp .env.example .env

- ✅ No API keys or secrets in the codebase

- ✅ All credentials via environment variables# Edit .env → add OPENAI_API_KEY and SERPAPI_KEY at minimum│  │    ANALYTICS      │   ┌──────────────────────────────┐  │     STORAGE      │   │

- ✅ structlog auto-redacts sensitive fields

- ✅ Paper trading mode by default

- ✅ Live trading requires 3 independent opt-ins

- ✅ Docker runs as non-root `botuser`# Launch dashboard│  │                   │   │         EXECUTION             │  │                  │   │6. **Calibrates** raw forecasts using Platt scaling, historical calibration, and evidence quality adjustments

- ✅ Immutable audit trail with SHA-256 checksums

make dashboard

---

# Open http://localhost:2345│  │  Regime Detector  │   │                               │  │  SQLite + WAL    │   │

## 📄 License

```

This project is open-source under the [MIT License](LICENSE).

│  │  Whale Scanner    │   │  Order Builder (TWAP/ICE/ADT) │  │  10 Migrations   │   │7. **Calculates edge** over the market price with full transaction cost awareness## Quick Start

---

### Docker

Built for the prediction market community · Not financial advice

│  │  Smart Entry      │   │  Order Router (dry/live)      │  │  Audit Trail     │   │

```bash

cp .env.example .env   # add your API keys│  │  Adaptive Weights │   │  Fill Tracker                 │  │  TTL Cache       │   │8. **Enforces 15+ risk checks** before any trade is allowed

docker compose up -d

# Dashboard at http://localhost:2345│  │  Perf Tracker     │   │  Cancel Manager               │  │  Auto Backup     │   │

```

│  │  Calibration Loop │   └──────────────────────────────┘  └──────────────────┘   │9. **Sizes positions** using fractional Kelly criterion with drawdown-aware multipliers### 1. Clone & Install

---

│  └──────────────────┘                                                             │

## ⚙️ Environment Variables

│                                                                                   │10. **Executes** orders with smart routing (TWAP, iceberg, adaptive pricing)

| Variable | Required | What It's For |

|----------|:--------:|---------------|│  ┌──────────────────────────────────────────────────────────────────────────────┐  │

| `OPENAI_API_KEY` | ✅ | GPT-4o forecasting & evidence extraction |

| `SERPAPI_KEY` | ✅ | Web search for research |│  │                           OBSERVABILITY                                      │  │11. **Monitors** positions in real-time with stop-loss, trailing stop, and resolution exit strategies```bash

| `ANTHROPIC_API_KEY` | Optional | Claude for ensemble |

| `GOOGLE_API_KEY` | Optional | Gemini for ensemble |│  │  Structured Logging (structlog) │ Metrics │ Alerts (Telegram/Discord/Slack)  │  │

| `BING_API_KEY` | Optional | Fallback search |

| `TAVILY_API_KEY` | Optional | Fallback search |│  │  Sentry Integration │ JSON Reports │ API Cost Tracking                       │  │12. **Learns** from resolved markets to improve future forecasts (calibration feedback loop)git clone <repo-url> polymarket-bot

| `DASHBOARD_API_KEY` | Recommended | Dashboard authentication |

| `POLYMARKET_API_KEY` | Live only | CLOB API credentials |│  └──────────────────────────────────────────────────────────────────────────────┘  │

| `POLYMARKET_API_SECRET` | Live only | CLOB API secret |

| `POLYMARKET_API_PASSPHRASE` | Live only | CLOB passphrase |└──────────────────────────────────────────────────────────────────────────────────┘cd polymarket-bot

| `POLYMARKET_PRIVATE_KEY` | Live only | Polygon wallet key for signing |

| `ENABLE_LIVE_TRADING` | Live only | Must be `true` for real orders |```

| `SENTRY_DSN` | Optional | Error tracking |

> ⚠️ **This bot can trade real money.** It ships with `dry_run: true` by default. Paper trading mode is the default — no real orders are placed unless explicitly enabled via environment variable and configuration.python -m venv .venv

---

---

## 🖥️ CLI Commands

source .venv/bin/activate

```bash

bot scan --limit 20              # Discover active markets## Core Pipeline

bot research --market <ID>       # Research a specific market

bot forecast --market <ID>       # Full pipeline: research → forecast → risk → size---pip install -e ".[dev]"

bot paper-trade --market <ID>    # Simulated trade (always dry run)

bot trade --market <ID>          # Live trade (requires ENABLE_LIVE_TRADING=true)Each trading cycle follows a deterministic processing pipeline with clear data flow between stages:

bot engine start                 # Start continuous trading loop

bot engine status                # Show engine health```

bot dashboard                    # Launch web dashboard

bot portfolio                    # Portfolio risk report```

bot drawdown                     # Current drawdown state

bot arbitrage                    # Scan for arbitrageMarket Discovery ──▶ Classification ──▶ Pre-Research Filter ──▶ Web Research## Architecture

bot alerts                       # Recent alert history

```        │                   │                    │                    │



---        │            11 categories         Score 0-100          Site-restricted### 2. Configure



## 🏗️ Deployment        │            + researchability     Blocks junk          queries to .gov,



**Development:** `make dashboard`        │              scoring (100+       markets before       .edu, official```



**Docker:** `docker compose up -d`        │              regex rules)        API calls            sources



**Production (systemd):**        ▼                                                           │┌──────────────────────────────────────────────────────────────────────────────┐```bash



```ini   Gamma API                                                        ▼

[Unit]

Description=Polymarket AI Trading Bot   (volume,                                              Evidence Extraction│                          MONITORING DASHBOARD (Flask)                        │cp .env.example .env

After=network.target

    liquidity,                                           (LLM-powered: every

[Service]

Type=simple    spread                                                fact → metric, value,│   9 Tabs: Overview │ Engine │ Positions │ Forecasts │ Risk │ Whales │ ...    │# Edit .env with your API keys:

User=botuser

WorkingDirectory=/opt/polymarket-ai-trading-bot    filters)                                              unit, date, citation)

EnvironmentFile=/opt/polymarket-ai-trading-bot/.env

ExecStart=/opt/polymarket-ai-trading-bot/.venv/bin/gunicorn \                                                                    │├──────────────────────────────────────────────────────────────────────────────┤#   POLYMARKET_API_KEY, SERPAPI_KEY (or BING_API_KEY or TAVILY_API_KEY), OPENAI_API_KEY

    --bind 0.0.0.0:2345 --workers 2 --threads 4 --timeout 120 \

    src.dashboard.app:app                                                                    ▼

Restart=always

                    Position Sizing ◀── Risk Check ◀── Edge Calc ◀── Forecast│                                                                              │```

[Install]

WantedBy=multi-user.target                         │               (15+ gates     (net of      (multi-model

```

                    Kelly criterion       every one      fees +       ensemble +│  ┌──────────────┐   ┌──────────────────┐   ┌─────────────────────────────┐  │

**Going live:** Start on Mumbai testnet (`POLYMARKET_CHAIN_ID=80001`), validate everything works, then switch to mainnet (`137`). See [DEPLOYMENT.md](DEPLOYMENT.md) for the full guide.

                    + 7 multipliers       must pass)     gas)         calibration)

---

                         ││  │  CONNECTORS  │   │     RESEARCH     │   │         FORECAST            │  │Review `config.yaml` for risk limits, scanning preferences, and research settings.

## 🧪 Testing

                         ▼

```bash

make test        # Run all tests                    Order Execution ──▶ Position Monitoring ──▶ Exit Management│  │              │   │                  │   │                             │  │

make test-cov    # Tests with coverage

make lint        # Ruff linter                    (TWAP/Iceberg/       (WebSocket feed,       (stop-loss,

make format      # Auto-format

make typecheck   # mypy strict mode                     Adaptive)            whale signals,         trailing stop,│  │ Gamma API    │   │ Query Builder    │   │ Feature Builder             │  │### 3. Run

```

                                          regime detection)      edge reversal,

---

                                                                 resolution hold)│  │ CLOB API     │──▶│ Source Fetcher   │──▶│ Multi-Model Ensemble        │  │

## 📁 Project Structure

```

```

src/│  │ Data API     │   │ Evidence Extract │   │ (GPT-4o/Claude/Gemini)      │  │```bash

├── cli.py                    # Click CLI (12 commands)

├── config.py                 # 16 Pydantic config models + hot-reload---

├── connectors/               # Gamma API, CLOB API, Data API, WebSocket, search, API pool

├── research/                 # Query builder, source fetcher, evidence extractor│  │ Web Search   │   │ Quality Scoring  │   │ Calibrator (Platt/Hist.)    │  │# Scan for active markets

├── forecast/                 # Feature builder, LLM forecaster, ensemble, calibrator

├── policy/                   # Edge calc, risk limits, Kelly sizer, drawdown, portfolio, arbitrage## Feature Deep Dive

├── engine/                   # Trading loop, classifier, filter, position manager

├── execution/                # Order builder, router, fill tracker, cancels│  │ WebSocket    │   └──────────────────┘   └─────────────────────────────┘  │bot scan --limit 20

├── analytics/                # Whale scanner, regime detector, calibration loop, performance

├── storage/                  # SQLite + WAL, migrations, audit trail, cache, backup### 1. Market Discovery & Classification

├── observability/            # structlog, metrics, alerts, Sentry, reports

└── dashboard/                # Flask app, glassmorphism UI, 9 tabs│  │ API Pool     │                                      │                    │

```

The bot discovers and classifies prediction markets without any LLM calls, using a pure-Python classification engine with 100+ regex rules.

---

│  │ Rate Limiter │                                      ▼                    │# Deep research on a specific market

## 🔒 Safety

**Market Discovery (Gamma API):**

- **Triple dry-run gate** — order flag + config flag + env var must ALL allow live trading

- **4-level drawdown protection** — progressively cuts sizing, auto-kills at 20%│  └──────────────┘   ┌──────────────────────────────────────────────────┐    │bot research <CONDITION_ID>

- **Portfolio guardrails** — caps per-category and per-event exposure

- **Credential safety** — all secrets from env vars, structlog auto-redacts sensitive fields| Filter | Default | Purpose |

- **Docker** — runs as non-root `botuser`

|--------|---------|---------|│                     │                   POLICY                         │    │

---

| Minimum volume | $1,000 | Skip inactive markets |

## 📄 License

| Minimum liquidity | $500 | Ensure executable depth |│                     │                                                  │    │# Full forecast pipeline (research → forecast → risk check → sizing)

MIT — see [LICENSE](LICENSE)

| Maximum spread | 8% | Avoid illiquid orderbooks |

<div align="center">

<sub>Built for the prediction market community · Not financial advice</sub>| Max days to expiry | 120 | Focus on resolvable markets |│                     │ Edge Calculator │ Risk Limits (15 checks)        │    │bot forecast <CONDITION_ID>

</div>

| Preferred types | MACRO, ELECTION, CORPORATE, LEGAL, TECHNOLOGY, SCIENCE | Categories with researchable data sources |

| Restricted types | WEATHER | Categories with unreliable forecasting |│                     │ Position Sizer (Kelly) │ Drawdown Manager        │    │

| Keyword blocking | Auto-detects meme, social media, and untradeable markets | Eliminates noise |

│                     │ Portfolio Risk │ Arbitrage │ Timeline Intel       │    │# Paper trade (dry run, logged to DB)

**11-Category Classifier:**

│                     └──────────────────────────────────────────────────┘    │bot paper-trade <CONDITION_ID>

Each market is assigned a rich classification that includes category, subcategory, researchability score (0–100), recommended query budget (2–8), primary data sources, search strategy, and semantic tags. This determines the entire research approach.

│                                        │                                    │

| Category | Subcategories | Primary Sources | Researchability |

|----------|---------------|-----------------|:---------------:|│  ┌──────────────┐                      ▼              ┌──────────────────┐  │# Live trade (requires ENABLE_LIVE_TRADING=true + config dry_run: false)

| **MACRO** | CPI, GDP, unemployment, Fed rates | bls.gov, bea.gov, federalreserve.gov, fred.stlouisfed.org | 85–95 |

| **ELECTION** | Presidential, Senate, House, gubernatorial | fec.gov, ballotpedia.org, realclearpolitics.com | 70–90 |│  │  ANALYTICS   │   ┌──────────────────────────┐      │    STORAGE       │  │bot trade <CONDITION_ID>

| **CORPORATE** | Earnings, IPO, M&A, SEC filings | sec.gov, investor relations sites, bloomberg.com | 75–90 |

| **LEGAL** | Supreme Court, litigation, regulation | supremecourt.gov, courtlistener.com | 65–80 |│  │              │   │       EXECUTION          │      │                  │  │```

| **TECHNOLOGY** | Product launches, AI, patents | techcrunch.com, arxiv.org | 50–70 |

| **SCIENCE** | Research publications, clinical trials | nature.com, science.org, arxiv.org, clinicaltrials.gov | 60–80 |│  │ Regime Det.  │   │                          │      │ SQLite + WAL     │  │

| **CRYPTO** | Price, regulation, protocol updates | coinmarketcap.com, etherscan.io | 40–65 |

| **REGULATION** | SEC, FDA, FCC rulings | sec.gov, federalregister.gov, congress.gov | 65–85 |│  │ Whale Scan   │   │ Order Builder (TWAP/ICE) │      │ Schema Migr.     │  │### 4. Docker

| **GEOPOLITICS** | Conflicts, treaties, sanctions | state.gov, un.org, crisisgroup.org | 45–65 |

| **SPORTS** | NFL, NBA, FIFA outcomes | espn.com, sports-reference.com | 55–75 |│  │ Smart Entry  │   │ Order Router (dry/live)  │      │ Audit Trail      │  │

| **ENTERTAINMENT** | Awards, box office, cultural events | imdb.com, boxofficemojo.com | 35–50 |

│  │ Adaptive Wt. │   │ Fill Tracker             │      │ TTL Cache        │  │```bash

**Pre-Research Filter:**

- Assigns a 0–100 quality score per market before any expensive API calls│  │ Perf Track   │   │ Cancel Manager           │      │ Auto Backup      │  │docker compose build

- Blocks unknown/unresearchable market types

- Enforces configurable research cooldown windows (default 60 minutes) to prevent redundant re-research│  │ Calib. Loop  │   └──────────────────────────┘      └──────────────────┘  │docker compose run bot scan --limit 10

- Reduces API costs by approximately 90%

│  └──────────────┘                                                           │docker compose run bot forecast <CONDITION_ID>

---

│                                                                              │```

### 2. Autonomous Research Engine

│  ┌──────────────────────────────────────────────────────────────────────┐    │

The research pipeline gathers evidence autonomously using structured web search and full-content page extraction. No manual input is required.

│  │                        OBSERVABILITY                                 │    │---

**Query Builder** — Generates targeted, site-restricted search queries per market type:

│  │  Structured Logging (structlog) │ Metrics │ Alerts (TG/Discord/Slack)│    │

```

Market: "Will CPI exceed 3% in February 2026?"│  │  Sentry Integration │ JSON Reports │ API Cost Tracking               │    │## CLI Commands

Category: MACRO / cpi

│  └──────────────────────────────────────────────────────────────────────┘    │

Generated Queries:

  1. site:bls.gov CPI consumer price index February 2026└──────────────────────────────────────────────────────────────────────────────┘| Command | Description |

  2. site:fred.stlouisfed.org CPIAUCSL 2026

  3. CPI inflation forecast February 2026 -reddit -twitter```|---|---|

  4. CPI lower than expected 2026 (contrarian query)

```| `bot scan` | Discover active markets from Gamma API |



- **Site-restricted queries** target authoritative sources per category (BLS.gov for macro, SEC.gov for corporate, FEC.gov for elections, NOAA.gov for weather)---| `bot research <id>` | Gather sources & extract evidence for a market |

- **Metric-specific queries** with date scoping for precise data retrieval

- **Contrarian queries** systematically surface opposing evidence to avoid confirmation bias| `bot forecast <id>` | Full pipeline: research → LLM forecast → calibrate → edge → risk → size |

- **Tiered budget** — query count scales with the market's researchability score (2–8 queries per market)

## Core Pipeline| `bot paper-trade <id>` | Forecast + build order (always dry run) |

**Source Fetcher** — Orchestrates search execution and content extraction:

| `bot trade <id>` | Forecast + execute order (requires live trading enabled) |

- **Pluggable search backends:** SerpAPI, Bing Search, and Tavily — with automatic fallback chain if one provider fails

- **Domain authority scoring:** primary sources (score 1.0) > secondary (0.6) > unknown (0.3)Each trading cycle follows a deterministic pipeline:

- **Full HTML content extraction** via BeautifulSoup — fetches and parses the actual page content, not just search snippets (up to 15,000 characters per source)

- **Deduplication** across queries to avoid processing the same source twice### Common Flags

- **Blocked domain filtering:** automatically filters out unreliable sources (Wikipedia, Reddit, Medium, Twitter, TikTok, etc.)

- **Built-in caching** with configurable TTL (default 1 hour) to reduce API costs```



**Evidence Extractor** — LLM-powered structured extraction:Market Discovery ──▶ Classification ──▶ Pre-Research Filter ──▶ Web Research- `--limit N` — max markets to scan (default 50)



Every piece of evidence is extracted into a strict schema:        │                   │                    │                    │- `--config PATH` — path to config YAML (default `config.yaml`)



```json        │            11 categories         Score 0-100          Site-restricted- `--verbose` — enable debug logging

{

  "text": "CPI-U increased 3.1% year-over-year in January 2026",        │            + researchability     Blocks junk          queries to .gov,

  "metric_name": "CPI-U YoY",

  "metric_value": "3.1",        │              scoring             markets              .edu, official---

  "metric_unit": "percent",

  "metric_date": "2026-01-31",        ▼                                                       sources

  "confidence": 0.97,

  "citation": {   Gamma API                                                        │## Market Type Classification

    "url": "https://www.bls.gov/news.release/cpi.nr0.htm",

    "publisher": "Bureau of Labor Statistics",   (volume,                                                         ▼

    "authority_score": 1.0

  }    liquidity,                                              Evidence ExtractionMarkets are auto-classified by keyword matching:

}

```    spread                                                  (LLM-powered)



- **Strict extraction rules:** ONLY extracts numbers, official statements, dates, and direct quotes — never opinions or speculation    filters)                                                        │| Type | Keywords (examples) | Primary Sources |

- **Contradiction detection:** identifies when multiple sources disagree, lists both sides, and reduces overall confidence

- **Independent quality scoring** (not just LLM self-assessment):                                                                    ▼|---|---|---|

  - Source recency penalty (stale data > 7 days penalized, > 30 days heavily penalized)

  - Domain authority weighting                    Position Sizing ◀── Risk Check ◀── Edge Calc ◀── Forecast| MACRO | CPI, inflation, GDP, unemployment, Fed | bls.gov, federalreserve.gov, treasury.gov |

  - Cross-source agreement scoring

  - Numeric evidence density bonus                         │               (15 gates)                (ensemble +| ELECTION | election, vote, president, senate, poll | fec.gov, realclearpolitics.com, 538 |



---                    Kelly criterion                                calibration)| CORPORATE | earnings, revenue, stock, IPO, SEC | sec.gov, investor relations, bloomberg.com |



### 3. Multi-Model AI Forecasting                    + drawdown adj.| WEATHER | hurricane, temperature, wildfire, NOAA | weather.gov, nhc.noaa.gov |



The forecasting system produces calibrated probability estimates using an ensemble of frontier LLMs. Models forecast **independently from evidence** — they are explicitly instructed not to anchor to any market price.                         │| SPORTS | NFL, NBA, FIFA, championship, playoff | espn.com, sports-reference.com |



| Model | Provider | Role | Default Weight |                         ▼

|-------|----------|------|:--------------:|

| **GPT-4o** | OpenAI | Primary forecaster | 40% |                    Order Execution ──▶ Position Monitoring ──▶ Exit Management---

| **Claude 3.5 Sonnet** | Anthropic | Second opinion | 35% |

| **Gemini 1.5 Pro** | Google | Third opinion | 25% |                    (TWAP/Iceberg/       (WebSocket feed,       (stop-loss,



**Ensemble Aggregation Methods:**                     Adaptive)            event triggers)        trailing stop,## Evidence Quality Gates



| Method | Description | Best For |                                                                 resolution)

|--------|-------------|----------|

| `trimmed_mean` (default) | Removes highest and lowest predictions, averages remaining | Robust to outlier models |```Every evidence bullet **must** include:

| `median` | Takes the median probability across all models | Maximum robustness |

| `weighted` | Per-model configurable weights based on historical accuracy | Optimized performance |



**Key Design Principles:**---```json



- **Independent forecasting** — each model receives the same evidence package and produces its own probability estimate without seeing other models' outputs{

- **Graceful degradation** — if one or more models fail (timeout, rate limit, error), the ensemble continues with remaining models as long as `min_models_required` (default: 1) is met

- **Confidence assessment** — each model assigns LOW / MEDIUM / HIGH confidence calibrated to evidence quality:## Feature Breakdown  "text": "CPI-U increased 3.1% YoY in January 2026",

  - **HIGH:** Authoritative primary source data directly answers the question

  - **MEDIUM:** Strong secondary sources with consistent directional signal  "metric_name": "CPI-U YoY",

  - **LOW:** Limited, conflicting, or stale evidence

- **Ensemble spread tracking** — measures model disagreement (max−min probability) and applies uncertainty penalty when models diverge significantly (spread > 10%)### 1. Market Discovery & Classification  "metric_value": "3.1",

- **Adaptive model weighting** — tracks per-model, per-category Brier scores over time and dynamically reweights the ensemble based on historical accuracy

  "metric_unit": "percent",

---

| Feature | Details |  "metric_date": "2026-01-31",

### 4. Calibration & Self-Improvement

|---------|---------|  "confidence": 0.97,

The bot continuously improves its forecasting accuracy through multiple feedback loops:

| **Gamma API Integration** | Discovers active markets with volume, liquidity, and spread filtering |  "citation": {

**Calibration Methods:**

| **11-Category Classifier** | MACRO, ELECTION, CORPORATE, LEGAL, TECHNOLOGY, SCIENCE, CRYPTO, REGULATION, GEOPOLITICS, SPORTS, ENTERTAINMENT |    "url": "https://www.bls.gov/...",

| Method | Mechanism | When Used |

|--------|-----------|-----------|| **Researchability Scoring** | 0–100 score per market determining research budget allocation |    "publisher": "Bureau of Labor Statistics",

| **Platt Scaling** | Logistic compression with 10% shrinkage — pulls extreme probabilities toward 0.50 | Default (always) |

| **Historical Calibration** | Logistic regression learned from own (forecast, outcome) history using scikit-learn — finds optimal *a*, *b* such that calibrated = σ(*a* · logit(*p*) + *b*) | After 30+ resolved markets || **Pre-Research Filter** | Blocks low-quality markets before expensive API calls (reduces costs ~90%) |    "authority_score": 1.0

| **Evidence Quality Penalty** | Pulls forecast toward 0.50 proportional to evidence weakness (quality < 0.4) | Always |

| **Contradiction Penalty** | Applies increasing uncertainty discount for each detected contradiction between sources | When contradictions found || **Keyword Blocking** | Auto-skips meme, social media, and untradeable markets |  }

| **Ensemble Disagreement Penalty** | Pulls toward 0.50 when model spread exceeds 10% | When models disagree |

| **Research Cooldown** | Prevents redundant re-research within configurable windows |}

**Self-Improvement Loops:**

```

- **Calibration Feedback Loop** — Records every (forecast, actual outcome) pair in the database. When sufficient history accumulates (30+ resolved markets), retrains the historical calibrator using logistic regression. Tracks Brier score improvement over time.

- **Adaptive Model Weighting** — Monitors per-model Brier scores broken down by market category. Automatically reweights the ensemble to favor models that have historically performed better on specific market types (e.g., GPT-4o may outperform on MACRO while Claude excels at ELECTION markets).The classifier uses 100+ regex rules mapping market questions to categories, subcategories, and recommended data sources — all without requiring any LLM calls.

- **Brier Score Monitoring** — Continuously tracks calibration quality: Brier = (1/N) × Σ(fᵢ − oᵢ)² where fᵢ is the forecast probability and oᵢ is the binary outcome.

Markets with `evidence_quality < min_evidence_quality` (default 0.3) are **rejected** by risk limits.

---

### 2. Autonomous Research Engine

### 5. Risk Management Framework

---

Institutional-grade risk controls with **15+ independent checks.** Every check must pass — a single violation blocks the trade.

The research pipeline gathers evidence autonomously using web search and full-content extraction:

| # | Risk Check | Default Threshold | Description |

|:-:|-----------|:-----------------:|-------------|## Risk Controls

| 1 | **Kill Switch** | Manual | Emergency halt — immediately stops all trading |

| 2 | **Drawdown Kill** | 20% | Auto-engages when portfolio drawdown exceeds maximum threshold |- **Query Builder** — Generates targeted search queries per market type:

| 3 | **Drawdown Heat** | 4 levels | Progressive position size reduction as drawdown deepens |

| 4 | **Max Stake** | $50/market | Per-market maximum bet size cap |  - **Site-restricted queries** to authoritative sources (BLS.gov for macro, SEC.gov for corporate, FEC.gov for elections)Nine independent checks, **all** must pass:

| 5 | **Daily Loss Limit** | $500 | Cumulative loss cap per calendar day |

| 6 | **Max Open Positions** | 25 | Limits number of concurrent active positions |  - **Metric-specific queries** with date scoping

| 7 | **Minimum Net Edge** | 4% | Net edge (after fees + gas) must exceed threshold |

| 8 | **Minimum Liquidity** | $2,000 | Skips markets with insufficient orderbook depth |  - **Contrarian queries** to surface opposing evidence1. **Kill Switch** — global halt

| 9 | **Maximum Spread** | 6% | Rejects markets with wide bid-ask spreads |

| 10 | **Evidence Quality** | 0.55 | Minimum evidence quality score from extraction pipeline |  - **Tiered budget** — research query count scales with researchability score2. **Minimum Edge** — default 2%

| 11 | **Confidence Filter** | MEDIUM | Rejects LOW confidence forecasts (configurable minimum) |

| 12 | **Implied Probability Floor** | 5% | Blocks micro-probability markets (extreme long shots) |3. **Max Daily Loss** — default $100

| 13 | **Positive Edge Direction** | > 0 | Net edge must be genuinely positive after all costs |

| 14 | **Market Type Allowed** | Configurable | Enforces category whitelist/blacklist per strategy |- **Source Fetcher** — Orchestrates search execution:4. **Max Open Positions** — default 20

| 15 | **Portfolio Exposure** | 35% / category | Category and event concentration limits |

| 16 | **Timeline Endgame** | 48h | Special handling for markets near resolution |  - Pluggable search backends: SerpAPI, Bing, Tavily (with automatic fallback)5. **Min Liquidity** — default $500



**Drawdown Manager — 4-Level Heat System:**  - Domain authority scoring (primary > secondary > unknown)6. **Max Spread** — default 12%



| Heat Level | Trigger | Kelly Multiplier | Action |  - Full HTML content extraction via BeautifulSoup (not just snippets)7. **Evidence Quality** — default 0.3

|:----------:|---------|:----------------:|--------|

| 0 (Normal) | Drawdown < 10% | 1.0× | Full sizing |  - Deduplication and blocked domain filtering8. **Market Type Restrictions** — configurable blocked types

| 1 (Warning) | Drawdown ≥ 10% | 0.50× | Half position sizes |

| 2 (Critical) | Drawdown ≥ 15% | 0.25× | Quarter position sizes |  - Built-in caching with configurable TTL9. **Clear Resolution** — market must have unambiguous resolution criteria

| 3 (Max) | Drawdown ≥ 20% | 0× (killed) | All trading halted, kill switch auto-engages |



Recovery from drawdown requires demonstrating profitable trades (`recovery_trades_required`: 5) before resuming full sizing.

- **Evidence Extractor** — LLM-powered structured extraction:---

**Portfolio Risk Manager:**

  - Extracts: metric name, value, unit, date, source, URL for every fact

- Maximum exposure per market category (e.g., 40% MACRO, 35% ELECTION, 30% CORPORATE, 15% WEATHER)

- Maximum exposure per single event (25%)  - Identifies contradictions between sources## Position Sizing

- Correlated position limits (max 4 correlated positions)

- Per-category stake multipliers (e.g., MACRO: 1.0×, CORPORATE: 0.75×, ELECTION: 0.50×)  - Computes independent quality score (recency, authority, agreement, numeric density)

- Rebalance monitoring every 30 minutes

  - Strict extraction rules — only numbers, official statements, dates, and direct quotesUses **fractional Kelly criterion**:

**Arbitrage Detector:**



Scans for pricing inconsistencies in:

- Complementary markets (YES + NO should equal ~$1.00)### 3. Multi-Model AI Forecasting$$f^* = \frac{p \cdot b - q}{b}$$

- Multi-outcome markets (all outcomes should sum to ~$1.00 minus vig)

- Calculates overround (bookmaker margin) for opportunity detection



---The forecasting system produces calibrated probability estimates using an ensemble of frontier LLMs:Where $p$ = calibrated probability, $q = 1-p$, $b$ = odds.



### 6. Intelligent Execution Engine



Smart order execution designed to minimize market impact and improve fill quality.| Model | Role | Default Weight |The raw Kelly fraction is then scaled by:



**Position Sizing — Fractional Kelly Criterion:**|-------|------|---------------|- `kelly_fraction` (default 0.25 = quarter-Kelly)



The Kelly formula for binary outcomes:| **GPT-4o** (OpenAI) | Primary forecaster | 40% |- `confidence` from forecaster



```| **Claude 3.5 Sonnet** (Anthropic) | Second opinion | 35% |- Capped by `max_stake_per_trade_usd` and `max_bankroll_fraction`

f* = (p × b − q) / b

```| **Gemini 1.5 Pro** (Google) | Third opinion | 25% |



Where *p* = calibrated model probability, *q* = 1−*p*, *b* = decimal odds = (1 / implied_prob) − 1---



The raw Kelly fraction is then adjusted by **7 independent multipliers:****Ensemble Aggregation Methods:**



| Multiplier | Default | Purpose |- **Trimmed Mean** (default) — Removes highest/lowest, averages remaining## Execution Safety

|------------|:-------:|---------|

| `kelly_fraction` | 0.25 (quarter-Kelly) | Base aggressiveness control |- **Median** — Robust to outlier models

| Confidence | LOW=0.5×, MED=0.75×, HIGH=1.0× | Scale by forecast confidence |

| Drawdown heat | 0.25× – 1.0× | Reduce sizing during drawdowns |- **Weighted** — Configurable per-model weightsThree independent dry-run gates prevent accidental live trading:

| Timeline proximity | 0.5× – 1.3× | Adjust for resolution timing |

| Volatility | Dynamic | Reduce for volatile markets |

| Regime | Dynamic | Reduce in HIGH_VOLATILITY regime |

| Category | 0.50× – 1.0× | Per-category risk budget |**Key Design Principles:**1. `order.dry_run` flag on the order itself



Final stake is capped by `max_stake_per_market` ($50), `max_bankroll_fraction` (5%), and available liquidity.- Models forecast **independently** from evidence — they do not anchor to market price2. `config.execution.dry_run` in config.yaml



**Order Builder — Automatic Strategy Selection:**- Confidence levels (LOW / MEDIUM / HIGH) are calibrated to evidence quality3. `ENABLE_LIVE_TRADING` environment variable



| Strategy | Trigger | Behavior |- Graceful degradation — if some models fail, the system continues with remaining ones

|----------|---------|----------|

| **Simple** | Small orders (< 30% of visible depth) | Single limit order with slippage tolerance |- `min_models_required` ensures minimum quorum for a valid forecast**All three** must allow live trading for an order to be submitted.

| **TWAP** | Large orders (> 30% of visible depth) | Splits into 5 time-weighted slices with progressive pricing |

| **Iceberg** | Medium-large orders (> $500) | Shows only 20% of true order size, replenishes automatically |

| **Adaptive Pricing** | All orders (when enabled) | Adjusts limit price based on orderbook depth and queue position |

### 4. Calibration & Self-Improvement---

**Order Router — Triple Dry-Run Safety Gate:**



Three independent gates must ALL permit live trading before any real order is submitted:

The bot continuously improves through multiple feedback loops:## Project Structure

1. **Order-level:** `dry_run` flag on each `OrderSpec` object

2. **Config-level:** `execution.dry_run: true` in `config.yaml`

3. **Environment-level:** `ENABLE_LIVE_TRADING=true` environment variable

- **Platt Scaling** — Logistic compression that shrinks extreme probabilities toward 0.50```

If any gate is closed, the order is simulated and logged but never submitted to the CLOB.

- **Historical Calibration** — Learns from own forecast vs. outcome history using logistic regressionpolymarket-bot/

**Fill Tracker — Execution Quality Analytics:**

- **Evidence Quality Penalty** — Penalizes forecasts with low evidence quality├── src/

- Tracks fill rate, slippage (bps), and time-to-fill for every order

- Per-strategy performance statistics (simple vs. TWAP vs. iceberg)- **Contradiction Penalty** — Applies uncertainty discount when sources disagree│   ├── __init__.py

- Feeds execution quality data back into strategy selection

- **Calibration Feedback Loop** — Records every (forecast, outcome) pair; retrains calibrator every N resolutions│   ├── cli.py                    # Click CLI entry point

**Position Manager — Exit Strategies:**

- **Adaptive Model Weighting** — Tracks per-model, per-category Brier scores; dynamically reweights ensemble based on historical accuracy│   ├── config.py                 # Pydantic config models

| Exit Strategy | Default | Description |

|---------------|:-------:|-------------|- **Brier Score Tracking** — Monitors forecast calibration quality over time│   ├── connectors/

| Dynamic stop-loss | 20% | Scaled by confidence and edge magnitude — tighter stops for weaker signals |

| Trailing stop | Auto | Locks in gains by moving stop-loss up as position becomes profitable |│   │   ├── polymarket_gamma.py   # Gamma REST API client

| Take-profit / Resolution | $1.00 / $0.00 | Hold through resolution — exit at full payout |

| Time-based exit | 240 hours | Auto-exit positions held beyond max holding period |### 5. Risk Management Framework│   │   ├── polymarket_clob.py    # CLOB orderbook + signing

| Edge reversal | Auto | Exit when model probability flips direction (edge turns negative) |

| Kill switch exit | Immediate | Force-close all positions when kill switch activates |│   │   └── web_search.py         # SerpAPI / Bing / Tavily



---Institutional-grade risk controls with **15+ independent checks** — any single violation blocks the trade:│   ├── research/



### 7. Whale & Smart Money Intelligence│   │   ├── query_builder.py      # Site-restricted query generation



Tracks top Polymarket traders and generates conviction signals that can boost or penalize the bot's own edge calculations.| # | Risk Check | Description |│   │   ├── source_fetcher.py     # Concurrent source gathering



**Wallet Scanner:**|---|-----------|-------------|│   │   └── evidence_extractor.py # LLM evidence extraction



- Monitors tracked wallets (seeded from the Polymarket leaderboard — top traders by PnL) for position changes| 1 | Kill Switch | Manual emergency halt of all trading |│   ├── forecast/

- **Delta detection:** identifies new entries, exits, size increases, and size decreases by comparing against previous scan snapshots

- **Conviction scoring** per market: combines whale count × dollar size × entry recency into a composite signal| 2 | Drawdown Kill | Auto-engages when drawdown exceeds max threshold |│   │   ├── feature_builder.py    # 30+ market features

- **Signal strength classification:** STRONG (high conviction, multiple whales) / MODERATE / WEAK

| 3 | Drawdown Heat | Reduces position size at warning/critical drawdown levels |│   │   ├── llm_forecaster.py     # GPT-4 probability estimation

**Edge Integration:**

| 4 | Max Stake | Per-market maximum bet size |│   │   └── calibrator.py         # Platt-like calibration

- When whales agree with the model's directional edge → conviction edge boost (+8% default)

- When whales disagree with the model → edge penalty (−2% default)| 5 | Daily Loss Limit | Cumulative loss cap per day |│   ├── policy/

- Whale convergence can lower the minimum edge threshold (default: from 4% → 2%) to enable trades the bot would otherwise skip

| 6 | Max Open Positions | Limits number of concurrent positions |│   │   ├── edge_calc.py          # Edge & EV calculation

**Leaderboard Integration:**

| 7 | Minimum Edge | Net edge after fees must exceed threshold |│   │   ├── risk_limits.py        # 9 independent risk checks

- Auto-discovers top wallets from the Polymarket Leaderboard API

- Seeds top 50 wallets by profit + top 50 by volume| 8 | Minimum Liquidity | Skips illiquid markets |│   │   └── position_sizer.py     # Fractional Kelly sizing

- Deduplicates and scores wallets by PnL, win rate, and recent activity

- Custom wallets can be added via `config.yaml`| 9 | Maximum Spread | Rejects wide-spread markets |│   ├── execution/



---| 10 | Evidence Quality | Minimum evidence quality threshold |│   │   ├── order_builder.py      # Order construction



### 8. Multi-Source Liquid Scanner| 11 | Confidence Filter | Rejects LOW confidence forecasts |│   │   ├── order_router.py       # Dry/live routing



A 7-phase whale discovery engine (v4) with API-level rate limit bypass for high-throughput scanning.| 12 | Implied Probability Floor | Blocks micro-probability markets |│   │   └── cancels.py            # Order cancellation



**Discovery Pipeline:**| 13 | Positive Edge Direction | Net edge must be positive after costs |│   ├── storage/



| Phase | Name | Description || 14 | Market Type Allowed | Enforces category whitelist/blacklist |│   │   ├── models.py             # Pydantic DB models

|:-----:|------|-------------|

| 0 | **Leaderboard Seeding** | Seeds top wallets from Polymarket Leaderboard API (top 50 by PnL + top 50 by volume) || 15 | Portfolio Exposure | Category and event concentration limits |│   │   ├── migrations.py         # SQLite schema migrations

| 1 | **Market Discovery** | Fetches active markets via Gamma API with configurable filters |

| 2 | **Global Trade Scanning** | Scans recent trades from the Data API with rotating offsets to discover new whale addresses |│   │   └── database.py           # CRUD operations

| 2b | **Per-Market Trade Scanning** | Targets top liquid markets individually for concentrated whale activity detection |

| 3 | **Address Ranking** | Ranks all discovered addresses by total volume, trade count, and average trade size |**Additional Risk Modules:**│   └── observability/

| 4 | **Deep Wallet Analysis** | Fetches full position data for top-ranked candidate wallets |

| 5 | **Score & Save** | Computes composite whale scores and persists results to database |│       ├── logger.py             # structlog with redaction



**API Pool — Multi-Endpoint Rate Limit Bypass:**- **Drawdown Manager** — Heat-based system (4 levels) that progressively reduces Kelly fraction as drawdown deepens; auto-engages kill switch at max drawdown│       ├── metrics.py            # In-process metrics



The API Pool multiplies effective API throughput by rotating requests across multiple endpoints, each with its own independent rate limiter:- **Portfolio Risk Manager** — Monitors category exposure, event concentration, and correlated position limits│       └── reports.py            # JSON run reports



| Feature | Description |- **Position Sizer** — Fractional Kelly criterion with confidence, drawdown, timeline, volatility, regime, and category multipliers; capped by max stake and max bankroll fraction├── tests/

|---------|-------------|

| **Independent rate limiters** | Token-bucket rate limiter per endpoint (default 60 RPM each) |- **Arbitrage Detector** — Scans for pricing inconsistencies in complementary and multi-outcome markets│   ├── conftest.py

| **3 selection strategies** | `round-robin` (sequential), `least-loaded` (most available quota), `weighted-random` (probabilistic by quota) |

| **Auto-health management** | Endpoints auto-disable after 5 consecutive failures, auto-recover after 120-second cooldown |- **Timeline Intelligence** — Adjusts sizing and entry strategy based on resolution proximity│   ├── test_market_parsing.py

| **Path-based routing** | Directs requests to compatible endpoints based on URL path prefixes |

| **Custom endpoints** | Add proxy mirrors via `config.yaml` to further multiply throughput |│   ├── test_orderbook.py

| **Built-in endpoints** | `data-api.polymarket.com` (60 RPM) + `gamma-api.polymarket.com` (60 RPM) |

### 6. Intelligent Execution│   ├── test_evidence_extraction.py

**Smart Deduplication:**

│   └── test_policy.py

- Tracks recently-scanned wallet addresses with configurable cooldown windows

- Skips addresses that were analyzed within the cooldown periodSmart order execution to minimize market impact and improve fill quality:├── config.yaml

- Prioritizes newly-discovered addresses over previously-scanned ones

├── pyproject.toml

---

- **Order Builder** — Constructs orders from position sizing with automatic strategy selection:├── Dockerfile

### 9. Market Microstructure Analysis

  - **Simple** — Single limit or market order for small positions├── docker-compose.yml

Extracts alpha signals from raw orderbook and trade data for smarter entry timing.

  - **TWAP** (Time-Weighted Average Price) — Splits large orders across time intervals├── .env.example

| Signal | Description |

|--------|-------------|  - **Iceberg** — Hides true order size, showing only a fraction at a time├── .gitignore

| **Order Flow Imbalance** | Buy vs. sell volume ratio across multiple time windows (60min, 4hr, 24hr) — detects directional pressure |

| **VWAP Divergence** | Tracks volume-weighted average price vs. current price — enter when price is below VWAP for buys (discount) |  - **Adaptive Pricing** — Adjusts limit price based on orderbook depth and queue position├── example_output.json

| **Whale Order Detection** | Identifies individual trades exceeding $2,000 threshold — signals institutional activity |

| **Trade Arrival Rate** | Measures acceleration in trading frequency — detects unusual activity surges (>2× baseline triggers alert) |└── README.md

| **Book Depth Ratio** | Bid depth vs. ask depth ratio — >1.0 indicates buy-side pressure, <1.0 indicates sell-side |

| **Smart Money Flow** | Estimates institutional vs. retail flow based on trade size distribution |- **Order Router** — Triple dry-run safety gate:```



**Smart Entry Calculator:**  1. Order-level `dry_run` flag on each `OrderSpec`



Combines microstructure signals with orderbook analysis to optimize entry prices:  2. Config-level `execution.dry_run` setting---

- Identifies support/resistance levels from orderbook depth

- Calculates optimal limit price based on VWAP divergence  3. Environment variable `ENABLE_LIVE_TRADING` check

- Adjusts entry aggressiveness based on flow imbalance direction

- Confirms momentum direction before entry## Testing



---- **Fill Tracker** — Monitors execution quality:



### 10. Real-Time Monitoring Dashboard  - Fill rate, slippage (bps), time-to-fill```bash



Full-featured Flask web dashboard with glassmorphism UI design, dark theme, and 9 interactive tabs.  - Per-strategy performance stats# Run all tests



| Tab | Features |  - Feeds back into strategy selectionpytest

|-----|----------|

| **Overview** | Engine status, cycle count, markets scanned, live P&L, equity curve chart, system health indicators |

| **Trading Engine** | Start/stop engine controls, cycle history timeline, current pipeline phase, processing visualization |

| **Positions** | Open positions table with live P&L (color-coded), closed trade history, resolution tracking |- **Position Manager** — Monitors all open positions with multiple exit strategies:# Run with coverage

| **Forecasts** | Recent forecasts with full evidence breakdown, probability comparison (model vs. market), confidence levels, reasoning |

| **Risk & Drawdown** | Drawdown gauge visualization, heat level indicator, current Kelly multiplier, portfolio exposure breakdown by category |  - Dynamic stop-loss (scaled by confidence/edge)pytest --cov=src --cov-report=term-missing

| **Smart Money** | Tracked wallets table with PnL/scores, conviction signals per market, whale activity feed with timestamps |

| **Liquid Scanner** | 7-phase pipeline status with progress bars, discovered whale candidates, API pool endpoint health stats |  - Trailing stop-loss (locks in gains)

| **Performance** | Win rate, ROI, Sharpe ratio, profit factor, category breakdown chart, model accuracy comparison, rolling windows (7d/30d/all-time) |

| **Settings** | Environment status checklist, config viewer, kill switch toggle, API key status (configured/missing) |  - Take-profit at resolution ($1.00 YES / $0.00 NO)# Run specific test file



**Dashboard Features:**  - Time-based exit (configurable max holding period)pytest tests/test_policy.py -v



- **API-key authentication** — protected via `DASHBOARD_API_KEY` environment variable (header or query parameter)  - Edge reversal exit (model probability flips)

- **Hot-reload configuration** — config changes via `config.yaml` take effect on next cycle without restart

- **Real-time polling** — auto-refreshing data with live status indicators and color-coded health signals  - Kill switch forced exit# Type checking

- **Responsive design** — works on desktop and tablet, dark theme with glassmorphism styling

- **Health endpoints** — `GET /health` (liveness), `GET /ready` (readiness with DB/engine checks)mypy src/



---- **Smart Entry Calculator** — Optimizes entry prices using:



### 11. Observability & Alerting  - Orderbook depth analysis (support/resistance levels)# Linting



**Structured Logging (structlog):**  - VWAP divergence (enter when price is below VWAP for buys)ruff check src/ tests/



- JSON-formatted structured logs with automatic sensitive data scrubbing  - Microstructure signals (flow imbalance, whale activity)```

- Redaction processor strips private keys, API secrets, passwords, and tokens from all log output

- Configurable log level (DEBUG / INFO / WARNING / ERROR) and output format (JSON / console)  - Price momentum confirmation

- Log rotation with file output to `logs/bot.log`

---

**In-Process Metrics:**

### 7. Whale & Smart Money Intelligence

- Counters: forecasts generated, trades executed, risk violations, API calls

- Gauges: open positions, current drawdown, bankroll value## Configuration Reference

- Histograms: execution latency, edge distribution, evidence quality

- API cost tracking: per-call cost estimation for all LLM and search API usageTracks top Polymarket traders and generates conviction signals:



**Multi-Channel Alerts:**See `config.yaml` for the full configuration. Key sections:



| Channel | Configuration | Use Case |- **Wallet Scanner** — Monitors tracked wallets for position changes:

|---------|---------------|----------|

| **Console** | Always on | Local development monitoring |  - Delta detection (new entries, exits, size changes)| Section | Purpose |

| **Telegram** | Bot token + chat ID | Mobile notifications |

| **Discord** | Webhook URL | Team channel alerts |  - Conviction scoring per market (whale count × dollar size)|---|---|

| **Slack** | Webhook URL | Workspace integration |

  - Signal strength classification (STRONG / MODERATE / WEAK)| `scanning` | Market discovery filters (preferred/restricted types) |

**Alert Triggers:**

  - Edge boost/penalty based on whale-model agreement| `research` | Primary domains per market type, blocked domains |

- Trade executions (with market, edge, stake details)

- Drawdown warnings at each heat level| `forecasting` | Model name, min evidence quality, calibration params |

- Kill switch activation/deactivation

- System errors and exceptions- **Leaderboard Integration** — Auto-discovers top wallets from the Polymarket leaderboard API:| `risk` | All risk limit thresholds |

- Daily performance summaries (configurable hour)

- Configurable cooldowns to prevent alert spam (default: 60 seconds per unique alert)  - Seeds top 50 by profit + top 50 by volume| `execution` | Dry run toggle, slippage tolerance |



**Sentry Integration:**  - Deduplicates and scores wallets by PnL, win rate, and activity| `storage` | SQLite path |



- Optional error tracking with automatic sensitive data scrubbing via `before_send` hook| `observability` | Log level, file paths, metrics |

- Set `SENTRY_DSN` environment variable to enable

- **Market Microstructure Analysis**:

**JSON Run Reports:**

  - Order flow imbalance across multiple time windows---

- Exportable reports with full forecast data, trade details, and performance metrics

- Saved to `reports/` directory  - VWAP divergence from current price



---  - Whale order detection (large trade alerts)## Security Notes



### 12. Storage & Audit Trail  - Trade arrival rate acceleration



**SQLite Database with WAL Mode:**  - Book depth ratio changes- **Private keys** are never logged (structlog redaction processor)



- Write-Ahead Logging (WAL) for concurrent read/write without locking  - Smart money vs. retail flow estimation- **API keys** loaded from environment only, never committed

- Foreign keys enabled for referential integrity

- 10 schema migrations (automatic upgrade on startup)- **Triple dry-run gate** prevents accidental live trading

- Tables: `markets`, `forecasts`, `trades`, `positions`, `closed_positions`, `alerts`, `engine_state`, `wallet_scans`, `regime_history`, `performance_log`, `calibration_history`

### 8. Liquid Market Scanner- **Kill switch** immediately halts all trading

**Immutable Audit Trail:**

- Run as non-root user in Docker

Every trading decision is recorded with full context and SHA-256 integrity verification:

- Market data at decision timeMulti-source whale discovery engine (v4) with API-level rate limit bypass:

- Research evidence used

- Model probability and confidence---

- Edge calculation details

- Risk check results (all 15+ checks with pass/fail)- **7-Phase Discovery Pipeline:**

- Position sizing details

- Order specification and fill data  1. **Phase 0 — Leaderboard Seeding:** Seeds top wallets from Polymarket Leaderboard API## License

- Final P&L

  2. **Phase 1 — Market Discovery:** Fetches active markets via Gamma API

Each audit entry includes a `checksum` field computed from the entry contents. The `verify_integrity()` method detects any tampering.

  3. **Phase 2 — Global Trade Scanning:** Scans recent trades from Data API with rotating offsetsMIT

**TTL Cache:**

  4. **Phase 2b — Per-Market Trade Scanning:** Targets top liquid markets for concentrated whale activity

- In-memory LRU cache with per-category TTL settings:  5. **Phase 3 — Address Ranking:** Ranks discovered addresses by volume, trade count, and size

  - Search results: 3,600 seconds (1 hour)  6. **Phase 4 — Deep Wallet Analysis:** Fetches full position data for top candidates

  - Orderbook data: 30 seconds  7. **Phase 5 — Score & Save:** Computes composite whale scores and persists to database

  - LLM responses: 1,800 seconds (30 minutes)

  - Market lists: 300 seconds (5 minutes)- **API Pool (Multi-Endpoint Rate Limit Bypass):**

- Maximum cache size: 100 MB  - Rotates requests across multiple API endpoints with independent per-endpoint rate limiters

- Reduces redundant API calls by approximately 60%  - 3 selection strategies: round-robin, least-loaded, weighted-random

  - Auto-health management: endpoints auto-disable after consecutive failures, auto-recover after cooldown

**Automated Backup:**  - Path-based routing: directs requests to compatible endpoints

  - Custom endpoint support via `config.yaml` for proxy servers

- SQLite database backup with rotation (max 10 backups)

- Stored in `data/backups/`- **Smart Deduplication:** Skips recently-scanned addresses with configurable cooldown windows

- Triggered via `make backup` or programmatically

### 9. Real-Time Monitoring Dashboard

---

Full-featured Flask web dashboard with glassmorphism UI and 9 interactive tabs:

## Tech Stack

| Tab | Features |

| Layer | Technologies ||-----|----------|

|-------|-------------|| **Overview** | Engine status, cycle count, markets scanned, live P&L, equity curve |

| **Language** | Python 3.9+ (type-annotated, async/await throughout) || **Trading Engine** | Start/stop engine, cycle history, current phase, pipeline visualization |

| **AI/LLM** | OpenAI GPT-4o, Anthropic Claude 3.5 Sonnet, Google Gemini 1.5 Pro || **Positions** | Open positions with live P&L, closed trade history, resolution tracking |

| **Web Framework** | Flask (dashboard + REST API) || **Forecasts** | Recent forecasts with evidence, probability comparison, confidence levels |

| **Database** | SQLite with WAL mode, 10 schema migrations, auto-backup || **Risk & Drawdown** | Drawdown gauge, heat level, Kelly multiplier, portfolio exposure |

| **Async HTTP** | httpx (primary), aiohttp (WebSocket), tenacity (retry with backoff) || **Smart Money** | Tracked wallets, conviction signals, whale activity feed |

| **WebSocket** | websockets (real-time price streaming from Polymarket) || **Liquid Scanner** | 7-phase pipeline status, discovered candidates, API pool stats |

| **ML / Statistics** | scikit-learn (logistic regression calibration), NumPy || **Performance** | Win rate, ROI, Sharpe ratio, category breakdown, model accuracy |

| **Web Scraping** | BeautifulSoup4, lxml (full HTML content extraction) || **Settings** | Environment status, config viewer, kill switch toggle |

| **CLI** | Click (command framework), Rich (formatted terminal tables) |

| **Logging** | structlog (JSON structured logging with redaction) |- **API-key authentication** for dashboard access

| **Configuration** | Pydantic v2 (16 config models with validation), YAML (hot-reloadable) |- **Hot-reload** — config changes apply without restart

| **Search** | SerpAPI, Bing Search API, Tavily (pluggable with automatic fallback) |- **Real-time updates** via polling with live status indicators

| **Deployment** | Docker (multi-stage build), Docker Compose, systemd, Gunicorn |- **Responsive design** with dark theme and glassmorphism styling

| **Error Tracking** | Sentry (optional, with sensitive data scrubbing) |

| **Testing** | pytest, pytest-asyncio, pytest-cov, respx (HTTP mocking) |### 10. Observability & Alerting

| **Linting** | ruff (formatting + linting), mypy (strict type checking) |

- **Structured Logging** (structlog) — JSON-formatted logs with automatic sensitive data scrubbing

---- **In-Process Metrics** — Counters, gauges, and histograms for all operations

- **API Cost Tracking** — Per-call cost estimation for all LLM and search API usage

## Installation & Setup- **Multi-Channel Alerts:**

  - Console (always on)

### Prerequisites  - Telegram bot notifications

  - Discord webhooks

| Requirement | Minimum | Notes |  - Slack webhooks

|-------------|---------|-------|  - Configurable cooldowns and minimum alert levels

| Python | 3.9+ | 3.11 recommended for best performance |- **Alert Triggers:** Trade executions, drawdown warnings, kill switch activation, system errors, daily summaries

| pip | Latest | `pip install --upgrade pip` |- **Sentry Integration** — Optional error tracking with automatic sensitive data scrubbing

| API Keys | At least 1 LLM + 1 search provider | See environment variables below |- **JSON Run Reports** — Exportable reports with full forecast and trade data

| Disk Space | ~100 MB | Plus database growth over time |

| Memory | 512 MB | 1 GB recommended for full ensemble |---



### Option 1: Local Installation (Recommended for Development)## Tech Stack



```bash| Layer | Technologies |

# 1. Clone the repository|-------|-------------|

git clone https://github.com/dylanpersonguy/polymarket-ai-trading-bot.git| **Language** | Python 3.9+ |

cd polymarket-ai-trading-bot| **AI/LLM** | OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet), Google (Gemini 1.5 Pro) |

| **Web Framework** | Flask (dashboard) |

# 2. Create and activate virtual environment| **Database** | SQLite with WAL mode, schema migrations, auto-backup |

python3 -m venv .venv| **HTTP** | httpx (async), aiohttp, tenacity (retry logic) |

source .venv/bin/activate        # macOS/Linux| **WebSocket** | websockets (real-time price streaming) |

# .venv\Scripts\activate         # Windows| **ML** | scikit-learn (calibration), NumPy |

| **Web Scraping** | BeautifulSoup4, lxml |

# 3. Install dependencies| **CLI** | Click, Rich (formatted tables) |

pip install -e ".[dev]"          # Development (includes pytest, ruff, mypy)| **Logging** | structlog (JSON structured logging) |

# pip install -e "."             # Production only| **Config** | Pydantic (validation), YAML (hot-reloadable) |

# pip install -e ".[prod]"      # Production + Gunicorn| **Search** | SerpAPI, Bing, Tavily (pluggable backends) |

| **Deployment** | Docker, Docker Compose, systemd, Gunicorn |

# 4. Configure environment variables| **Error Tracking** | Sentry (optional) |

cp .env.example .env

# Edit .env with your API keys (see Configuration Reference below)---



# 5. Review and customize runtime config## Quick Start

# Edit config.yaml — all settings have sensible defaults

### Prerequisites

# 6. Launch the dashboard

make dashboard- Python 3.9 or higher

# Or directly: .venv/bin/python -m src.cli dashboard- API keys for at least one LLM provider (OpenAI recommended)

- API key for at least one search provider (SerpAPI recommended)

# 7. Open in browser

# http://localhost:2345### 1. Clone & Install

```

```bash

### Option 2: Docker (Recommended for Production)git clone https://github.com/dylanpersonguy/polymarket-bot.git

cd polymarket-bot

```bashpython3 -m venv .venv

# 1. Clone the repositorysource .venv/bin/activate

git clone https://github.com/dylanpersonguy/polymarket-ai-trading-bot.gitpip install -e ".[dev]"

cd polymarket-ai-trading-bot```



# 2. Configure environment### 2. Configure Environment

cp .env.example .env

# Edit .env with your API keys```bash

cp .env.example .env

# 3. Build and start```

docker compose up -d

Edit `.env` with your API keys:

# 4. View logs

docker compose logs -f bot```bash

# Required for forecasting

# 5. Run CLI commands inside the containerOPENAI_API_KEY=your-openai-key

docker compose run bot scan --limit 20

docker compose run bot forecast <CONDITION_ID># Required for research

SERPAPI_KEY=your-serpapi-key

# 6. Stop

docker compose down# Optional: ensemble models

```ANTHROPIC_API_KEY=your-anthropic-key

GOOGLE_API_KEY=your-google-key

The Docker image uses a multi-stage build (builder + runtime), runs as a non-root `botuser`, includes health checks, and exposes port 2345.

# Optional: dashboard authentication

### Option 3: Makefile ShortcutsDASHBOARD_API_KEY=your-dashboard-secret

```

```bash

make install     # Create venv and install production dependencies### 3. Launch Dashboard

make dev         # Install with dev + prod dependencies (pytest, ruff, mypy, gunicorn)

make dashboard   # Start Flask dashboard on port 2345```bash

make engine      # Start trading engine (headless, no dashboard)make dashboard

make scan        # Run a single market scan (20 markets)# Or directly:

make test        # Run full test suite.venv/bin/python -m src.cli dashboard

make test-cov    # Run tests with coverage report```

make lint        # Run ruff linter

make format      # Auto-format code with ruffVisit `http://localhost:2345` to access the monitoring dashboard.

make typecheck   # Run mypy type checker (strict mode)

make gunicorn    # Start production WSGI server (Gunicorn)### 4. CLI Commands

make docker      # Build Docker image

make docker-up   # Start with docker compose```bash

make docker-down # Stop docker compose# Scan for active markets

make backup      # Backup SQLite databasebot scan --limit 20

make clean       # Remove build artifacts and caches

```# Research a specific market

bot research --market <CONDITION_ID>

### Post-Installation Verification

# Full forecast pipeline

```bashbot forecast --market <CONDITION_ID>

# Verify installation

bot --help# Paper trading simulation

bot paper-trade --days 30

# Run test suite

make test# Start continuous trading engine

bot engine start

# Scan for markets (no API keys needed for Gamma API)

bot scan --limit 5# View portfolio risk

bot portfolio

# Check environment status in the dashboard

make dashboard# Scan for arbitrage

# → Navigate to Settings tab to verify API key statusbot arbitrage

``````



------



## Configuration Reference## Configuration



All runtime configuration is managed via `config.yaml` with **hot-reload support** — changes take effect on the next trading cycle without restarting the bot.All runtime configuration is managed via `config.yaml` with hot-reload support — changes take effect on the next cycle without restarting.



### Environment Variables### Key Configuration Sections



| Variable | Required | Description || Section | Purpose |

|----------|:--------:|-------------||---------|---------|

| `OPENAI_API_KEY` | **Yes** | GPT-4o for forecasting and evidence extraction || `scanning` | Market discovery filters (volume, liquidity, spread, categories) |

| `SERPAPI_KEY` | **Yes** | Web search for research pipeline (primary provider) || `research` | Search settings (max sources, timeouts, domain whitelist/blacklist) |

| `ANTHROPIC_API_KEY` | Optional | Claude 3.5 Sonnet for ensemble forecasting || `forecasting` | LLM model selection, temperature, confidence thresholds |

| `GOOGLE_API_KEY` | Optional | Gemini 1.5 Pro for ensemble forecasting || `ensemble` | Multi-model config, aggregation method, per-model weights |

| `BING_API_KEY` | Optional | Alternative search provider (fallback) || `risk` | Bankroll, max stake, daily loss limit, Kelly fraction, stop-loss/take-profit |

| `TAVILY_API_KEY` | Optional | Alternative search provider (fallback) || `drawdown` | Heat system thresholds, auto-kill, recovery requirements |

| `DASHBOARD_API_KEY` | Recommended | Protects dashboard with API key authentication || `portfolio` | Category exposure limits, event concentration, correlation limits |

| `POLYMARKET_API_KEY` | Live only | Polymarket CLOB API credentials || `execution` | Dry run toggle, order type, TWAP/iceberg settings, slippage tolerance |

| `POLYMARKET_API_SECRET` | Live only | CLOB API secret || `storage` | Database path and type |

| `POLYMARKET_API_PASSPHRASE` | Live only | CLOB API passphrase || `cache` | TTL settings for search, orderbook, LLM, and market list caches |

| `POLYMARKET_PRIVATE_KEY` | Live only | Polygon wallet private key for order signing || `observability` | Log level/format, metrics, report output directory |

| `POLYMARKET_CHAIN_ID` | Live only | `137` (Polygon mainnet) or `80001` (Mumbai testnet) || `alerts` | Notification channels (Telegram, Discord, Slack), alert triggers |

| `ENABLE_LIVE_TRADING` | Live only | Must be explicitly set to `true` to enable real order placement || `wallet_scanner` | Whale tracking settings, conviction thresholds |

| `SENTRY_DSN` | Optional | Sentry error tracking DSN || `scanner.apiPool` | API endpoint pool strategy, custom proxy endpoints |

| `engine` | Cycle interval, max markets per cycle, paper mode toggle |

### Config YAML Sections

### Environment Variables

| Section | Key Settings | Description |

|---------|-------------|-------------|| Variable | Required | Description |

| `scanning` | `min_volume_usd`, `min_liquidity_usd`, `max_spread`, `preferred_types`, `restricted_types`, `filter_min_score`, `research_cooldown_minutes` | Market discovery and pre-research filtering ||----------|----------|-------------|

| `research` | `max_sources`, `primary_domains`, `blocked_domains`, `search_provider`, `fetch_full_content`, `min_corroborating_sources` | Web search and content extraction || `OPENAI_API_KEY` | Yes | GPT-4o for forecasting and evidence extraction |

| `forecasting` | `llm_model`, `llm_temperature`, `calibration_method`, `low_evidence_penalty`, `min_evidence_quality`, `min_confidence_level` | LLM forecasting parameters || `SERPAPI_KEY` | Yes | Web search for research pipeline |

| `ensemble` | `enabled`, `models`, `aggregation`, `weights`, `timeout_per_model_secs`, `min_models_required` | Multi-model ensemble configuration || `ANTHROPIC_API_KEY` | Optional | Claude 3.5 Sonnet for ensemble |

| `risk` | `bankroll`, `max_stake_per_market`, `max_daily_loss`, `min_edge`, `kelly_fraction`, `max_bankroll_fraction`, `stop_loss_pct`, `take_profit_pct`, `category_stake_multipliers` | Risk thresholds and position limits || `GOOGLE_API_KEY` | Optional | Gemini 1.5 Pro for ensemble |

| `drawdown` | `max_drawdown_pct`, `warning_drawdown_pct`, `critical_drawdown_pct`, `auto_kill_at_max`, `heat_loss_streak_threshold`, `recovery_trades_required` | Drawdown heat system || `BING_API_KEY` | Optional | Alternative search provider |

| `portfolio` | `max_category_exposure_pct`, `max_single_event_exposure_pct`, `max_correlated_positions`, `category_limits` | Portfolio-level risk controls || `TAVILY_API_KEY` | Optional | Alternative search provider |

| `timeline` | `near_resolution_hours`, `near_resolution_confidence_boost`, `early_market_uncertainty_penalty` | Resolution timing adjustments || `DASHBOARD_API_KEY` | Recommended | Protects dashboard with API key authentication |

| `microstructure` | `whale_size_threshold_usd`, `flow_imbalance_windows`, `vwap_lookback_trades` | Order flow analysis settings || `POLYMARKET_API_KEY` | Live only | Polymarket CLOB API credentials |

| `execution` | `dry_run`, `default_order_type`, `slippage_tolerance`, `twap_num_slices`, `iceberg_show_pct`, `adaptive_pricing` | Order execution parameters || `POLYMARKET_API_SECRET` | Live only | CLOB API secret |

| `storage` | `db_type`, `sqlite_path` | Database configuration || `POLYMARKET_API_PASSPHRASE` | Live only | CLOB API passphrase |

| `cache` | `search_ttl_secs`, `orderbook_ttl_secs`, `llm_response_ttl_secs`, `max_cache_size_mb` | Cache TTL settings || `POLYMARKET_PRIVATE_KEY` | Live only | Polygon wallet private key for signing |

| `observability` | `log_level`, `log_format`, `log_file`, `enable_metrics`, `reports_dir` | Logging and metrics || `ENABLE_LIVE_TRADING` | Live only | Must be `true` to enable real order placement |

| `alerts` | `telegram_bot_token`, `discord_webhook_url`, `slack_webhook_url`, `alert_on_trade`, `daily_summary_enabled` | Notification channels and triggers || `SENTRY_DSN` | Optional | Sentry error tracking |

| `wallet_scanner` | `enabled`, `scan_interval_minutes`, `min_conviction_score`, `conviction_edge_boost`, `track_leaderboard` | Whale tracking settings |

| `engine` | `cycle_interval_secs`, `max_markets_per_cycle`, `paper_mode`, `max_concurrent_research` | Trading loop configuration |---



---## CLI Reference



## CLI Reference```

Usage: bot [OPTIONS] COMMAND [ARGS]...

```

Usage: bot [OPTIONS] COMMAND [ARGS]...Commands:

  scan          Scan and list candidate markets

  Polymarket Research & Trading Bot  research      Research a specific market (evidence gathering)

  forecast      Full forecast pipeline (research → forecast → risk → sizing)

Options:  paper-trade   Run paper trading simulation

  --config PATH  Path to config.yaml (default: ./config.yaml)  trade         Execute live trades (requires ENABLE_LIVE_TRADING=true)

  --help         Show this message and exit.  dashboard     Launch the monitoring dashboard web UI

  engine start  Start the continuous trading engine

Commands:  engine status Show engine status

  scan          Scan and list candidate markets  portfolio     Show portfolio risk report

  research      Research a specific market (evidence gathering + extraction)  drawdown      Show current drawdown state

  forecast      Full pipeline: research → forecast → calibrate → edge → risk → size  arbitrage     Scan for arbitrage opportunities

  paper-trade   Forecast + build order in dry-run mode (always simulated)  alerts        Show recent alerts

  trade         Forecast + execute order (requires ENABLE_LIVE_TRADING=true)```

  engine start  Start the continuous autonomous trading engine

  engine status Show current engine status, cycle count, and health---

  dashboard     Launch the monitoring dashboard web UI (port 2345)

  portfolio     Show portfolio risk report with category exposure## Deployment

  drawdown      Show current drawdown state and heat level

  arbitrage     Scan for arbitrage opportunities across markets### Docker

  alerts        Show recent alert history

``````bash

# Build and start

### Usage Examplesdocker compose up -d



```bash# View logs

# Discover active marketsdocker compose logs -f bot

bot scan --limit 20

# Run CLI commands

# Deep research on a specific marketdocker compose run bot scan --limit 20

bot research --market <CONDITION_ID>docker compose run bot forecast --market <ID>



# Full forecast pipeline (research → forecast → risk check → sizing)# Stop

bot forecast --market <CONDITION_ID>docker compose down

```

# Paper trade (simulated order, logged to database)

bot paper-trade --market <CONDITION_ID>### Makefile Shortcuts



# Start continuous trading engine```bash

bot engine startmake install     # Install production dependencies

make dev         # Install with dev dependencies

# Launch monitoring dashboardmake dashboard   # Start Flask dashboard

bot dashboardmake engine      # Start trading engine (headless)

make test        # Run test suite

# View portfolio riskmake lint        # Run ruff linter

bot portfoliomake format      # Auto-format code

make typecheck   # Run mypy type checker

# Check drawdown statemake test-cov    # Run tests with coverage

bot drawdown```



# Scan for arbitrage### Production (Gunicorn + systemd)

bot arbitrage

```See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment instructions including systemd service configuration and Gunicorn setup.



------



## Deployment## Project Structure



### Development```

polymarket-bot/

```bash├── config.yaml                 # Runtime configuration (hot-reloadable)

make dashboard        # Flask dev server on port 2345├── pyproject.toml              # Project metadata and dependencies

```├── Dockerfile                  # Multi-stage Docker build

├── docker-compose.yml          # Container orchestration

### Production (Docker)├── Makefile                    # Development shortcuts

├── .env.example                # Environment variable template

```bash│

docker compose up -d                    # Start├── src/

docker compose logs -f bot              # Monitor│   ├── cli.py                  # Click CLI entry point

docker compose down                     # Stop│   ├── config.py               # Pydantic config loader with hot-reload

docker compose run bot scan --limit 20  # Run CLI commands│   │

```│   ├── connectors/             # External API integrations

│   │   ├── polymarket_gamma.py # Market discovery & metadata (Gamma API)

### Production (Gunicorn + systemd)│   │   ├── polymarket_clob.py  # Orderbook & order placement (CLOB API)

│   │   ├── polymarket_data.py  # Wallet positions & trades (Data API)

Create `/etc/systemd/system/polymarket-bot.service`:│   │   ├── web_search.py       # Pluggable search (SerpAPI/Bing/Tavily)

│   │   ├── ws_feed.py          # WebSocket real-time price streaming

```ini│   │   ├── microstructure.py   # Order flow, VWAP, whale detection

[Unit]│   │   ├── api_pool.py         # Multi-endpoint rate limit bypass

Description=Polymarket AI Trading Bot│   │   └── rate_limiter.py     # Token-bucket rate limiting

After=network.target│   │

│   ├── research/               # Evidence gathering pipeline

[Service]│   │   ├── query_builder.py    # Site-restricted search query generation

Type=simple│   │   ├── source_fetcher.py   # Source ranking & full-content extraction

User=botuser│   │   └── evidence_extractor.py # LLM-powered structured evidence extraction

WorkingDirectory=/opt/polymarket-ai-trading-bot│   │

EnvironmentFile=/opt/polymarket-ai-trading-bot/.env│   ├── forecast/               # Probability estimation

ExecStart=/opt/polymarket-ai-trading-bot/.venv/bin/gunicorn \│   │   ├── feature_builder.py  # Market feature vector construction

    --bind 0.0.0.0:2345 \│   │   ├── llm_forecaster.py   # Single-model LLM forecasting

    --workers 2 --threads 4 --timeout 120 \│   │   ├── ensemble.py         # Multi-model ensemble (GPT-4o/Claude/Gemini)

    --access-logfile - \│   │   └── calibrator.py       # Platt scaling & historical calibration

    src.dashboard.app:app│   │

Restart=always│   ├── policy/                 # Trading rules & risk management

RestartSec=10│   │   ├── edge_calc.py        # Edge calculation with cost awareness

│   │   ├── risk_limits.py      # 15+ independent risk checks

[Install]│   │   ├── position_sizer.py   # Fractional Kelly criterion

WantedBy=multi-user.target│   │   ├── drawdown.py         # Heat-based drawdown management

```│   │   ├── portfolio_risk.py   # Category/event exposure limits

│   │   ├── arbitrage.py        # Cross-market arbitrage detection

```bash│   │   └── timeline.py         # Resolution timeline intelligence

sudo systemctl enable polymarket-bot│   │

sudo systemctl start polymarket-bot│   ├── engine/                 # Core trading loop

sudo systemctl status polymarket-bot│   │   ├── loop.py             # Main trading engine (coordinator)

```│   │   ├── market_classifier.py# 11-category classifier (100+ rules)

│   │   ├── market_filter.py    # Pre-research quality filter

### Going Live — Testnet First│   │   ├── position_manager.py # Position monitoring & exit strategies

│   │   └── event_monitor.py    # Price/volume spike re-research triggers

1. **Configure for Mumbai testnet:**│   │

   ```bash│   ├── execution/              # Order management

   # .env│   │   ├── order_builder.py    # TWAP, iceberg, adaptive order construction

   POLYMARKET_CHAIN_ID=80001│   │   ├── order_router.py     # Dry-run / live routing with triple safety

   ENABLE_LIVE_TRADING=true│   │   ├── fill_tracker.py     # Execution quality analytics

   ```│   │   └── cancels.py          # Order cancellation (individual + kill switch)

   ```yaml│   │

   # config.yaml│   ├── analytics/              # Intelligence & self-improvement

   execution:│   │   ├── wallet_scanner.py   # Whale/smart-money position tracking

     dry_run: false│   │   ├── regime_detector.py  # Market regime detection

   risk:│   │   ├── calibration_feedback.py # Forecast vs. outcome learning loop

     bankroll: 100.0│   │   ├── adaptive_weights.py # Dynamic per-model weighting

     max_stake_per_market: 5.0│   │   ├── smart_entry.py      # Optimal entry price calculation

   ```│   │   └── performance_tracker.py # Win rate, Sharpe, category breakdown

│   │

2. **Install CLOB client:** `pip install py-clob-client`│   ├── storage/                # Persistence

│   │   ├── database.py         # SQLite with WAL mode

3. **Validate on testnet** — monitor dashboard, verify order placement and fills│   │   ├── models.py           # Pydantic data models

│   │   ├── migrations.py       # Schema versioning (10 migrations)

4. **Switch to mainnet:**│   │   ├── audit.py            # Immutable decision audit trail (SHA-256)

   ```bash│   │   ├── cache.py            # TTL cache with LRU eviction

   # .env│   │   └── backup.py           # Automated SQLite backup with rotation

   POLYMARKET_CHAIN_ID=137│   │

   # Fund wallet with USDC on Polygon│   ├── observability/          # Monitoring & alerting

   ```│   │   ├── logger.py           # structlog with sensitive data scrubbing

   ```yaml│   │   ├── metrics.py          # In-process counters, gauges, histograms

   # config.yaml — start conservative│   │   ├── alerts.py           # Multi-channel (Telegram/Discord/Slack)

   risk:│   │   ├── reports.py          # JSON run report generation

     bankroll: 500.0│   │   └── sentry_integration.py # Optional Sentry error tracking

     max_stake_per_market: 25.0│   │

     kelly_fraction: 0.15  # Conservative start│   └── dashboard/              # Web monitoring UI

   drawdown:│       ├── app.py              # Flask application + scanner + engine

     max_drawdown_pct: 0.10  # Tight 10% limit│       ├── templates/

   ```│       │   └── index.html      # 9-tab dashboard (glassmorphism UI)

│       └── static/

### Health Checks & Monitoring│           ├── dashboard.js    # Frontend logic (live updates, charts)

│           └── style.css       # Dark theme styling

| Endpoint | Purpose |│

|----------|---------|├── tests/                      # Test suite (pytest)

| `GET /health` | Liveness check (always returns 200) |├── scripts/                    # Utility scripts

| `GET /ready` | Readiness check (verifies DB + engine) |└── data/                       # Runtime data (gitignored)

| Dashboard | Full monitoring at `http://localhost:2345` |```



------



## Testing## Safety & Risk Controls



```bashThis bot is designed with multiple layers of safety to prevent accidental or runaway trading:

# Run all tests

make test### Triple Dry-Run Gate

# Or: pytest tests/ -qEvery order must pass three independent checks before reaching the Polymarket CLOB:

1. **Order-level** `dry_run` flag on each `OrderSpec`

# Run with coverage report2. **Config-level** `execution.dry_run: true` in `config.yaml`

make test-cov3. **Environment-level** `ENABLE_LIVE_TRADING=true` must be explicitly set

# Or: pytest tests/ --cov=src --cov-report=term-missing

### Drawdown Protection

# Run specific test file- **4-level heat system** progressively reduces position sizes as drawdown deepens

pytest tests/test_policy.py -v- **Auto kill-switch** halts all trading when maximum drawdown is reached

- **Recovery requirements** — must demonstrate profitable trades before resuming full sizing

# Type checking (strict mode)

make typecheck### Portfolio Guardrails

# Or: mypy src/- Maximum exposure per market category (e.g., 40% MACRO, 35% ELECTION)

- Maximum exposure per single event

# Linting- Correlated position limits

make lint- Per-category stake multipliers

# Or: ruff check src/ tests/

### Sensitive Data Protection

# Auto-format- All credentials loaded exclusively from environment variables

make format- Structured logger automatically scrubs sensitive fields (private keys, API secrets, passwords)

# Or: ruff format src/ tests/- Sentry integration includes before-send scrubber

```- `.env` files excluded from version control



------



## Project Structure## License



```This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

polymarket-ai-trading-bot/

├── config.yaml                  # Runtime configuration (hot-reloadable)---

├── pyproject.toml               # Project metadata, dependencies, tool configs

├── Dockerfile                   # Multi-stage Docker build (builder + runtime)<p align="center">

├── docker-compose.yml           # Container orchestration with health checks  <sub>Built for the prediction market community</sub>

├── Makefile                     # 20+ development shortcuts</p>

├── .env.example                 # Environment variable template (never commit .env)
├── DEPLOYMENT.md                # Detailed deployment & live trading guide
│
├── src/
│   ├── cli.py                   # Click CLI — 12 commands with Rich table output
│   ├── config.py                # 16 Pydantic config models with hot-reload watcher
│   │
│   ├── connectors/              # External API integrations
│   │   ├── polymarket_gamma.py  # Market discovery & metadata (Gamma REST API)
│   │   ├── polymarket_clob.py   # Orderbook, order placement, signing (CLOB API)
│   │   ├── polymarket_data.py   # Wallet positions, trade history (Data API)
│   │   ├── web_search.py        # Pluggable search (SerpAPI / Bing / Tavily + fallback)
│   │   ├── ws_feed.py           # WebSocket real-time price streaming
│   │   ├── microstructure.py    # Order flow, VWAP, whale detection, depth analysis
│   │   ├── api_pool.py          # Multi-endpoint pool with independent rate limiters
│   │   └── rate_limiter.py      # Token-bucket rate limiting per service
│   │
│   ├── research/                # Autonomous evidence gathering pipeline
│   │   ├── query_builder.py     # Site-restricted query generation per category
│   │   ├── source_fetcher.py    # Concurrent source ranking + full HTML extraction
│   │   └── evidence_extractor.py # LLM-powered structured evidence extraction
│   │
│   ├── forecast/                # Probability estimation engine
│   │   ├── feature_builder.py   # 30+ market feature vector construction
│   │   ├── llm_forecaster.py    # Single-model LLM forecasting with strict prompting
│   │   ├── ensemble.py          # Multi-model ensemble (GPT-4o / Claude / Gemini)
│   │   └── calibrator.py        # Platt scaling, historical calibration, penalties
│   │
│   ├── policy/                  # Trading rules & risk management
│   │   ├── edge_calc.py         # Edge calculation with cost awareness + multi-outcome
│   │   ├── risk_limits.py       # 15+ independent risk checks (all must pass)
│   │   ├── position_sizer.py    # Fractional Kelly criterion with 7 multipliers
│   │   ├── drawdown.py          # 4-level heat-based drawdown management
│   │   ├── portfolio_risk.py    # Category/event exposure limits + rebalancing
│   │   ├── arbitrage.py         # Cross-market arbitrage detection
│   │   └── timeline.py          # Resolution timeline intelligence
│   │
│   ├── engine/                  # Core trading loop
│   │   ├── loop.py              # TradingEngine — main coordinator (1,500+ lines)
│   │   ├── market_classifier.py # 11-category classifier with 100+ regex rules
│   │   ├── market_filter.py     # Pre-research quality filter with cooldowns
│   │   ├── position_manager.py  # Position monitoring + 6 exit strategies
│   │   └── event_monitor.py     # Price/volume spike re-research triggers
│   │
│   ├── execution/               # Order management
│   │   ├── order_builder.py     # TWAP, iceberg, adaptive order construction
│   │   ├── order_router.py      # Triple dry-run safety gate (order/config/env)
│   │   ├── fill_tracker.py      # Execution quality analytics (fill rate, slippage)
│   │   └── cancels.py           # Order cancellation (individual + bulk kill switch)
│   │
│   ├── analytics/               # Intelligence & self-improvement
│   │   ├── wallet_scanner.py    # Whale/smart-money position tracking & conviction
│   │   ├── regime_detector.py   # Market regime detection (5 regimes)
│   │   ├── calibration_feedback.py # Forecast vs. outcome learning loop
│   │   ├── adaptive_weights.py  # Dynamic per-model, per-category weighting
│   │   ├── smart_entry.py       # Optimal entry price (orderbook + VWAP + flow)
│   │   └── performance_tracker.py # Win rate, Sharpe, Sortino, Calmar, equity curve
│   │
│   ├── storage/                 # Persistence layer
│   │   ├── database.py          # SQLite with WAL mode + CRUD operations
│   │   ├── models.py            # Pydantic data models for all DB entities
│   │   ├── migrations.py        # 10 schema migrations (auto-upgrade on startup)
│   │   ├── audit.py             # Immutable decision audit trail (SHA-256 checksums)
│   │   ├── cache.py             # TTL cache with LRU eviction (per-category TTL)
│   │   └── backup.py            # Automated SQLite backup with rotation (max 10)
│   │
│   ├── observability/           # Monitoring & alerting
│   │   ├── logger.py            # structlog with automatic sensitive data scrubbing
│   │   ├── metrics.py           # In-process counters, gauges, histograms, cost tracker
│   │   ├── alerts.py            # Multi-channel alerts (Telegram / Discord / Slack)
│   │   ├── reports.py           # JSON run report generation
│   │   └── sentry_integration.py # Optional Sentry error tracking with scrubbing
│   │
│   └── dashboard/               # Web monitoring UI
│       ├── app.py               # Flask app + scanner/engine integration
│       ├── templates/
│       │   └── index.html       # 9-tab glassmorphism dashboard
│       └── static/
│           ├── dashboard.js     # Frontend logic (live polling, charts, controls)
│           └── style.css        # Dark theme styling
│
├── tests/                       # Test suite (pytest + pytest-asyncio)
│   ├── conftest.py              # Shared fixtures
│   ├── test_policy.py           # Risk limits, edge calc, position sizing
│   ├── test_market_classifier.py # Classification rules
│   ├── test_market_filter.py    # Pre-research filter
│   ├── test_evidence_extraction.py # Evidence extractor
│   ├── test_market_parsing.py   # Market data parsing
│   ├── test_orderbook.py        # Orderbook operations
│   ├── test_paper_trading.py    # Paper trade simulation
│   ├── test_wallet_scanner.py   # Whale scanner
│   ├── test_analytics.py        # Analytics modules
│   └── ...
│
├── scripts/                     # Utility scripts
│   ├── seed_demo_data.py        # Seed database with demo data
│   └── wipe_db.py               # Reset database
│
├── data/                        # Runtime data (gitignored)
├── logs/                        # Log files (gitignored)
└── reports/                     # Generated reports (gitignored)
```

---

## Safety & Risk Controls

This bot is designed with multiple defense-in-depth layers to prevent accidental or runaway trading.

### Triple Dry-Run Gate

Every order must pass **three independent checks** before reaching the Polymarket CLOB:

```
OrderSpec.dry_run ──▶ config.yaml execution.dry_run ──▶ ENV ENABLE_LIVE_TRADING
    (per-order)           (global config)                  (environment variable)
        │                       │                                │
   Must be False          Must be False                   Must be "true"
        │                       │                                │
        └───────── ALL THREE must permit ────────────────────────┘
                            │
                     Order submitted
```

### Drawdown Protection

- **4-level heat system** progressively reduces position sizes (100% → 50% → 25% → 0%)
- **Auto kill-switch** halts all trading when maximum drawdown is reached
- **Recovery requirements** — must demonstrate 5 profitable trades before resuming full sizing
- **Snapshot interval** — drawdown state persisted every 15 minutes

### Portfolio Guardrails

- Maximum exposure per market category (MACRO: 40%, ELECTION: 35%, CORPORATE: 30%, WEATHER: 15%)
- Maximum exposure per single event (25%)
- Correlated position limit (4 positions with similarity > 70%)
- Per-category stake multipliers for granular risk budgeting

### Sensitive Data Protection

- All credentials loaded exclusively from environment variables — never hardcoded
- Structured logger (structlog) includes automatic redaction processor that strips private keys, API secrets, passwords, and tokens from all log output
- Sentry integration includes `before_send` scrubber
- `.env` files excluded from version control via `.gitignore`
- Docker container runs as non-root `botuser`

---

## API Cost Estimates

| Component | Cost per Cycle | Notes |
|-----------|:--------------:|-------|
| SerpAPI | ~$0.05–0.15 | 5–15 queries × ~$0.01/query |
| GPT-4o | ~$0.05–0.10 | Per market forecast |
| Claude 3.5 Sonnet | ~$0.03–0.05 | If ensemble enabled |
| Gemini 1.5 Pro | ~$0.01–0.03 | If ensemble enabled |
| **Total per cycle** | **~$0.15–0.35** | With 5-minute cycle interval |
| **Daily (24h)** | **~$45–100** | ~288 cycles/day |

**Cost reduction strategies built in:**
- Pre-research filter blocks ~90% of markets before any API calls
- Search cache with 1-hour TTL reduces redundant queries by ~60%
- Research cooldown prevents re-researching the same market within 60 minutes
- Configurable `max_markets_per_cycle` limits research per cycle (default: 5)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built for the prediction market research community · Not financial advice</sub>
</div>
