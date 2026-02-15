# Polymarket AI Trading Bot

Autonomous trading agent for Polymarket prediction markets. Discovers markets, researches evidence, forecasts probabilities with a multi-model AI ensemble, and executes trades with strict risk controls.

Paper trading by default. Three safety gates must be unlocked for live orders.

---

## Features

- **Market Discovery** — scans Polymarket for active markets, classifies them into 11 categories, and filters out low-quality ones before spending API calls
- **Research Pipeline** — builds site-restricted search queries per category, fetches full articles, scores source authority, and extracts structured evidence with citations
- **AI Forecasting** — runs GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro in parallel, then combines their outputs with trimmed-mean aggregation
- **Calibration** — applies Platt scaling, historical accuracy correction, and penalizes weak evidence, contradictions, and model disagreement
- **Risk Management** — 15+ independent checks including drawdown limits, position caps, edge thresholds, portfolio exposure limits, and a manual kill switch
- **Execution** — fractional Kelly sizing with 7 multipliers, auto-selects between simple, TWAP, iceberg, and adaptive order strategies
- **Whale Intelligence** — tracks top traders from the Polymarket leaderboard, detects position changes, and integrates conviction signals into edge calculations
- **Dashboard** — 9-tab Flask UI on port 2345 with engine controls, live P&L, forecasts, risk gauges, whale activity, and performance metrics
- **Observability** — structured logging, Telegram/Discord/Slack alerts, Sentry integration, and exportable JSON reports
- **Storage** — SQLite with WAL mode, 10 auto-migrations, immutable SHA-256 audit trail, TTL caching, and automated backups

---

## Quick Start

```
git clone https://github.com/dylanpersonguy/polymarket-ai-trading-bot.git
cd polymarket-ai-trading-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Add your API keys to `.env` — at minimum `OPENAI_API_KEY` and `SERPAPI_KEY`.

```
make dashboard
```

Open **http://localhost:2345**.

---

## Docker

```
cp .env.example .env
docker compose up -d
```

---

## CLI

```
bot scan --limit 20            # discover markets
bot research --market <ID>     # research a market
bot forecast --market <ID>     # full pipeline: research, forecast, risk, size
bot paper-trade --market <ID>  # simulated trade
bot trade --market <ID>        # live trade (needs ENABLE_LIVE_TRADING=true)
bot engine start               # continuous trading loop
bot engine status              # engine health
bot dashboard                  # launch dashboard
bot portfolio                  # portfolio risk report
bot drawdown                   # drawdown status
bot arbitrage                  # scan for arbitrage
bot alerts                     # alert history
```

---

## Configuration

All config lives in `config.yaml` and `.env`.

**Required keys** — `OPENAI_API_KEY`, `SERPAPI_KEY`

**Optional keys** — `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `BING_API_KEY`, `TAVILY_API_KEY`, `DASHBOARD_API_KEY`

**Live trading** — set `ENABLE_LIVE_TRADING=true` and add `POLYMARKET_API_KEY`, `POLYMARKET_API_SECRET`, `POLYMARKET_API_PASSPHRASE`, `POLYMARKET_PRIVATE_KEY`

---

## Safety

- Dry run by default — three independent gates (order flag, config flag, env var) must all allow live trading
- 4-level drawdown heat system — progressively cuts position sizes, halts at 20% drawdown
- No secrets in the codebase — everything via `.env`
- Docker runs as non-root user

---

## Tests

```
make test
make lint
make format
```

---

## License

MIT

---

*Built for the prediction market community. Not financial advice.*
