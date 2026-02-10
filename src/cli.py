"""CLI entry point for the Polymarket Research & Trading Bot.

Commands:
  bot scan               — List candidate markets
  bot research --market   — Research a specific market
  bot forecast --market   — Produce a forecast for a market
  bot paper-trade --days  — Run paper trading simulation
  bot trade --live        — Live trading (requires ENABLE_LIVE_TRADING=true)
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from typing import Any

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from src.config import BotConfig, load_config, is_live_trading_enabled
from src.observability.logger import configure_logging, get_logger

load_dotenv()

console = Console()
log = get_logger(__name__)


def _run(coro: Any) -> Any:
    """Run an async coroutine from sync CLI."""
    return asyncio.run(coro)


@click.group()
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
@click.pass_context
def cli(ctx: click.Context, config_path: str | None) -> None:
    """Polymarket Research & Trading Bot."""
    ctx.ensure_object(dict)
    cfg = load_config(config_path)
    ctx.obj["config"] = cfg
    configure_logging(
        level=cfg.observability.log_level,
        fmt="console",  # CLI always uses console format
        log_file=cfg.observability.log_file,
    )


# ─── SCAN ────────────────────────────────────────────────────────────

@cli.command()
@click.option("--limit", default=20, help="Number of markets to list")
@click.pass_context
def scan(ctx: click.Context, limit: int) -> None:
    """Scan and list candidate markets."""
    cfg: BotConfig = ctx.obj["config"]

    async def _scan() -> list[dict[str, Any]]:
        from src.connectors.polymarket_gamma import GammaClient

        gamma = GammaClient()
        try:
            markets = await gamma.list_markets(
                limit=min(limit, cfg.scanning.batch_size),
                active=True,
            )
        finally:
            await gamma.close()

        # Filter by scanning config
        candidates = []
        for m in markets:
            if m.volume < cfg.scanning.min_volume_usd:
                continue
            if m.liquidity < cfg.scanning.min_liquidity_usd:
                continue
            if m.spread > cfg.scanning.max_spread:
                continue
            candidates.append(m)

        return candidates

    markets = _run(_scan())

    table = Table(title=f"📊 Candidate Markets ({len(markets)} found)")
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Type", style="cyan", max_width=10)
    table.add_column("Question", max_width=50)
    table.add_column("Volume", justify="right", style="green")
    table.add_column("Liquidity", justify="right")
    table.add_column("Implied P", justify="right", style="yellow")
    table.add_column("Spread", justify="right")

    for m in markets:
        table.add_row(
            m.id[:12],
            m.market_type,
            m.question[:50],
            f"${m.volume:,.0f}",
            f"${m.liquidity:,.0f}",
            f"{m.best_bid:.1%}",
            f"{m.spread:.2%}",
        )

    console.print(table)


# ─── RESEARCH ────────────────────────────────────────────────────────

@cli.command()
@click.option("--market", "market_id", required=True, help="Market ID to research")
@click.pass_context
def research(ctx: click.Context, market_id: str) -> None:
    """Research a specific market — fetch evidence and sources."""
    cfg: BotConfig = ctx.obj["config"]

    async def _research() -> dict[str, Any]:
        from src.connectors.polymarket_gamma import GammaClient
        from src.connectors.web_search import create_search_provider
        from src.research.query_builder import build_queries
        from src.research.source_fetcher import SourceFetcher
        from src.research.evidence_extractor import EvidenceExtractor

        gamma = GammaClient()
        search = create_search_provider(cfg.research.search_provider)
        fetcher = SourceFetcher(search, cfg.research)
        extractor = EvidenceExtractor(cfg.forecasting)

        try:
            market = await gamma.get_market(market_id)
            queries = build_queries(market)
            sources = await fetcher.fetch_sources(
                queries, market_type=market.market_type
            )
            evidence = await extractor.extract(
                market.id, market.question, sources,
                market_type=market.market_type,
            )
        finally:
            await gamma.close()
            await search.close()
            await fetcher.close()

        return evidence.to_dict()

    result = _run(_research())

    console.print("\n[bold cyan]📚 Research Results[/bold cyan]\n")
    console.print_json(json.dumps(result, indent=2, default=str))


# ─── FORECAST ────────────────────────────────────────────────────────

@cli.command()
@click.option("--market", "market_id", required=True, help="Market ID to forecast")
@click.pass_context
def forecast(ctx: click.Context, market_id: str) -> None:
    """Produce a full forecast for a market."""
    cfg: BotConfig = ctx.obj["config"]

    async def _forecast() -> dict[str, Any]:
        from src.connectors.polymarket_gamma import GammaClient
        from src.connectors.polymarket_clob import CLOBClient
        from src.connectors.web_search import create_search_provider
        from src.research.query_builder import build_queries
        from src.research.source_fetcher import SourceFetcher
        from src.research.evidence_extractor import EvidenceExtractor
        from src.forecast.feature_builder import build_features
        from src.forecast.llm_forecaster import LLMForecaster
        from src.forecast.calibrator import calibrate
        from src.policy.edge_calc import calculate_edge
        from src.policy.risk_limits import check_risk_limits
        from src.policy.position_sizer import calculate_position_size

        gamma = GammaClient()
        clob = CLOBClient()
        search = create_search_provider(cfg.research.search_provider)
        fetcher = SourceFetcher(search, cfg.research)
        extractor = EvidenceExtractor(cfg.forecasting)
        forecaster = LLMForecaster(cfg.forecasting)

        try:
            # 1. Fetch market data
            market = await gamma.get_market(market_id)
            console.print(f"\n[bold]Market:[/bold] {market.question}")
            console.print(f"[bold]Type:[/bold] {market.market_type}")
            console.print(f"[bold]Implied P:[/bold] {market.best_bid:.1%}")

            # 2. Fetch orderbook
            orderbook = None
            trades = None
            if market.tokens:
                try:
                    token_id = market.tokens[0].token_id
                    orderbook = await clob.get_orderbook(token_id)
                    trades = await clob.get_trade_history(token_id, limit=50)
                except Exception as e:
                    console.print(f"[yellow]⚠ CLOB data unavailable: {e}[/yellow]")

            # 3. Research
            console.print("\n[cyan]🔍 Researching...[/cyan]")
            queries = build_queries(market)
            sources = await fetcher.fetch_sources(
                queries, market_type=market.market_type
            )
            evidence = await extractor.extract(
                market.id, market.question, sources,
                market_type=market.market_type,
            )

            # 4. Build features
            features = build_features(market, orderbook, trades, evidence)

            # 5. LLM forecast
            console.print("[cyan]🧠 Forecasting...[/cyan]")
            raw_forecast = await forecaster.forecast(
                features, evidence,
                resolution_source=market.resolution_source,
            )

            # 6. Calibrate
            cal = calibrate(
                raw_forecast.model_probability,
                evidence.quality_score,
                num_contradictions=len(evidence.contradictions),
                method=cfg.forecasting.calibration_method,
                low_evidence_penalty=cfg.forecasting.low_evidence_penalty,
            )
            model_prob = cal.calibrated_probability

            # 7. Edge calculation
            edge = calculate_edge(features.implied_probability, model_prob)

            # 8. Risk check
            risk_result = check_risk_limits(
                edge=edge,
                features=features,
                risk_config=cfg.risk,
                forecast_config=cfg.forecasting,
                market_type=market.market_type,
                allowed_types=cfg.scanning.preferred_types,
                restricted_types=cfg.scanning.restricted_types,
            )

            # 9. Position sizing (only if TRADE)
            position = None
            if risk_result.allowed:
                position = calculate_position_size(
                    edge, cfg.risk,
                    confidence_level=raw_forecast.confidence_level,
                )

            # Build output
            output: dict[str, Any] = {
                "market_id": market.id,
                "question": market.question,
                "market_type": market.market_type,
                "resolution_source": market.resolution_source,
                "implied_probability": round(features.implied_probability, 4),
                "model_probability": round(model_prob, 4),
                "edge": round(edge.raw_edge, 4),
                "edge_direction": edge.direction,
                "confidence_level": raw_forecast.confidence_level,
                "evidence_quality": round(evidence.quality_score, 2),
                "evidence": [
                    {
                        "text": b.text,
                        "citation": {
                            "url": b.citation.url,
                            "publisher": b.citation.publisher,
                            "date": b.citation.date,
                        },
                    }
                    for b in evidence.bullets[:5]
                ],
                "contradictions": [
                    {"description": c.description}
                    for c in evidence.contradictions
                ],
                "invalidation_triggers": raw_forecast.invalidation_triggers,
                "reasoning": raw_forecast.reasoning,
                "calibration": {
                    "method": cal.method,
                    "adjustments": cal.adjustments,
                },
                "risk_check": {
                    "decision": risk_result.decision,
                    "violations": risk_result.violations,
                    "warnings": risk_result.warnings,
                },
                "decision": risk_result.decision,
            }

            if position:
                output["position"] = {
                    "stake_usd": position.stake_usd,
                    "direction": position.direction,
                    "token_quantity": position.token_quantity,
                    "kelly_fraction": position.kelly_fraction_used,
                    "capped_by": position.capped_by,
                }

            return output

        finally:
            await gamma.close()
            await clob.close()
            await search.close()
            await fetcher.close()

    result = _run(_forecast())

    console.print(f"\n[bold {'green' if result['decision'] == 'TRADE' else 'red'}]"
                  f"Decision: {result['decision']}[/bold {'green' if result['decision'] == 'TRADE' else 'red'}]\n")
    console.print_json(json.dumps(result, indent=2, default=str))


# ─── PAPER TRADE ─────────────────────────────────────────────────────

@cli.command("paper-trade")
@click.option("--days", default=30, help="Number of days to simulate")
@click.option("--markets", default=10, help="Number of markets per cycle")
@click.pass_context
def paper_trade(ctx: click.Context, days: int, markets: int) -> None:
    """Run paper trading simulation."""
    cfg: BotConfig = ctx.obj["config"]
    console.print(f"[bold]📈 Paper Trading Mode[/bold] — {days} days, {markets} markets/cycle")
    console.print("[yellow]⚠ This is a simulation. No real trades will be placed.[/yellow]\n")

    async def _paper_trade() -> None:
        from src.connectors.polymarket_gamma import GammaClient
        from src.storage.database import Database

        db = Database(cfg.storage)
        db.connect()
        gamma = GammaClient()

        try:
            all_markets = await gamma.list_markets(limit=markets, active=True)
            console.print(f"Fetched {len(all_markets)} markets")

            for m in all_markets:
                console.print(f"  [{m.market_type}] {m.question[:60]}  P={m.best_bid:.1%}")

            console.print(f"\n[green]✓ Paper trade scan complete.[/green]")
            console.print(
                "Full paper trading loop (with forecasting) requires API keys.\n"
                "Set OPENAI_API_KEY and SERPAPI_KEY, then use:\n"
                "  bot forecast --market <ID>"
            )
        finally:
            await gamma.close()
            db.close()

    _run(_paper_trade())


# ─── LIVE TRADE ──────────────────────────────────────────────────────

@cli.command()
@click.option("--live", is_flag=True, help="Confirm live trading")
@click.pass_context
def trade(ctx: click.Context, live: bool) -> None:
    """Execute live trades (requires ENABLE_LIVE_TRADING=true)."""
    if not live:
        console.print("[red]❌ Use --live flag to confirm.[/red]")
        sys.exit(1)

    if not is_live_trading_enabled():
        console.print(
            "[red]❌ Live trading is disabled.[/red]\n"
            "Set ENABLE_LIVE_TRADING=true in your environment to enable."
        )
        sys.exit(1)

    cfg: BotConfig = ctx.obj["config"]

    if cfg.risk.kill_switch:
        console.print("[red]❌ Kill switch is ON. Trading halted.[/red]")
        sys.exit(1)

    console.print("[bold red]🚨 LIVE TRADING MODE 🚨[/bold red]")
    console.print("This will place real orders with real money.\n")

    if not click.confirm("Are you sure you want to proceed?"):
        console.print("Aborted.")
        sys.exit(0)

    console.print(
        "[yellow]Live trading loop starting...[/yellow]\n"
        "Implement the full live loop by connecting the forecast pipeline "
        "to the order router. See README for architecture."
    )


if __name__ == "__main__":
    cli()
