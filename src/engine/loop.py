"""Continuous trading loop — the brain of the bot.

Runs on a configurable cycle (default 5 minutes):
  1. Discover & filter markets
  2. Build features for each market
  3. Research top candidates (evidence gathering)
  4. Forecast probabilities
  5. Calculate edges
  6. Check risk limits
  7. Size positions
  8. Route orders (paper or live)
  9. Monitor existing positions for exits

Between cycles:
  - Check drawdown state
  - Monitor position exits (stop-loss, resolution/100%, time-based)
  - Persist engine state to DB for dashboard
"""

from __future__ import annotations

import asyncio
import json
import signal
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from src.config import BotConfig, load_config, is_live_trading_enabled
from src.policy.drawdown import DrawdownManager
from src.policy.portfolio_risk import PortfolioRiskManager, PositionSnapshot
from src.engine.market_filter import ResearchCache, filter_markets, FilterStats
from src.analytics.regime_detector import RegimeDetector, RegimeState
from src.analytics.calibration_feedback import CalibrationFeedbackLoop
from src.analytics.adaptive_weights import AdaptiveModelWeighter
from src.analytics.smart_entry import SmartEntryCalculator
from src.analytics.wallet_scanner import WalletScanner, save_scan_result
from src.observability.logger import get_logger

log = get_logger(__name__)


@dataclass
class CycleResult:
    """Summary of one trading cycle."""
    cycle_id: int
    started_at: float
    ended_at: float = 0.0
    duration_secs: float = 0.0
    markets_scanned: int = 0
    markets_researched: int = 0
    edges_found: int = 0
    trades_attempted: int = 0
    trades_executed: int = 0
    errors: list[str] = field(default_factory=list)
    status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


class TradingEngine:
    """Continuous trading engine that coordinates all bot components."""

    def __init__(self, config: Any | None = None):
        self.config: BotConfig = config or load_config()
        self._running = False
        self._cycle_count = 0
        self._cycle_history: list[CycleResult] = []

        bankroll = self.config.risk.bankroll
        self.drawdown = DrawdownManager(bankroll, self.config)
        self.portfolio = PortfolioRiskManager(bankroll, self.config)

        self._pre_cycle_hooks: list[Callable] = []
        self._post_cycle_hooks: list[Callable] = []
        self._positions: list[PositionSnapshot] = []

        # Pre-research filter
        self._research_cache = ResearchCache(
            cooldown_minutes=self.config.scanning.research_cooldown_minutes,
        )
        self._last_filter_stats: FilterStats | None = None

        # ── Analytics & Intelligence Layer ──
        self._regime_detector = RegimeDetector()
        self._calibration_loop = CalibrationFeedbackLoop()
        self._adaptive_weighter = AdaptiveModelWeighter(self.config.ensemble)
        self._smart_entry = SmartEntryCalculator()
        self._current_regime: RegimeState | None = None

        # ── Wallet / Whale Scanner ──
        self._wallet_scanner = WalletScanner(
            min_whale_count=self.config.wallet_scanner.min_whale_count,
            min_conviction_score=self.config.wallet_scanner.min_conviction_score,
        )
        self._last_wallet_scan: float = 0.0
        self._latest_scan_result: Any = None

        # Database (initialised in start())
        self._db: Any = None
        self._audit: Any = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def cycle_history(self) -> list[CycleResult]:
        return list(self._cycle_history)

    def add_pre_cycle_hook(self, fn: Callable) -> None:
        self._pre_cycle_hooks.append(fn)

    def add_post_cycle_hook(self, fn: Callable) -> None:
        self._post_cycle_hooks.append(fn)

    # ── Lifecycle ────────────────────────────────────────────────────

    def _init_db(self) -> None:
        from src.storage.database import Database
        from src.storage.audit import AuditTrail
        self._db = Database(self.config.storage)
        self._db.connect()
        self._audit = AuditTrail()
        log.info("engine.db_connected", path=self.config.storage.sqlite_path)

    def _persist_engine_state(self, extra: dict[str, Any] | None = None) -> None:
        if not self._db:
            return
        try:
            state = {
                "running": self._running,
                "cycle_count": self._cycle_count,
                "live_trading": is_live_trading_enabled(),
                "paper_mode": self.config.engine.paper_mode,
                "last_cycle": (
                    self._cycle_history[-1].to_dict()
                    if self._cycle_history else None
                ),
                "positions": len(self._positions),
                "scan_interval_minutes": self.config.engine.scan_interval_minutes,
                "max_markets_per_cycle": self.config.engine.max_markets_per_cycle,
                "auto_start": self.config.engine.auto_start,
                "filter_stats": (
                    self._last_filter_stats.__dict__
                    if self._last_filter_stats else None
                ),
                "research_cache_size": self._research_cache.size(),
            }
            if extra:
                state.update(extra)
            self._db.set_engine_state("engine_status", json.dumps(state))
            dd = self.drawdown.state
            self._db.set_engine_state("drawdown", json.dumps(dd.to_dict()))
        except Exception as e:
            log.warning("engine.persist_state_error", error=str(e))

    async def start(self) -> None:
        self._running = True
        interval = self.config.engine.cycle_interval_secs
        self._init_db()
        self._db.insert_alert("info", "\U0001f916 Trading engine started", "system")
        log.info(
            "engine.starting",
            interval_secs=interval,
            live_trading=is_live_trading_enabled(),
            bankroll=self.config.risk.bankroll,
        )
        self._persist_engine_state()

        # Graceful shutdown on SIGTERM / SIGINT
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, self._handle_signal, sig)
            except NotImplementedError:
                pass  # Windows doesn't support add_signal_handler

        while self._running:
            try:
                await self._run_cycle()
            except Exception as e:
                log.error("engine.cycle_error", error=str(e))
                traceback.print_exc()
                if self._db:
                    self._db.insert_alert("error", f"Cycle error: {e}", "system")
            self._persist_engine_state()
            if self._running:
                log.info("engine.sleeping", seconds=interval)
                await asyncio.sleep(interval)

        log.info("engine.stopped", total_cycles=self._cycle_count)
        if self._db:
            self._db.insert_alert("info", "\U0001f6d1 Trading engine stopped", "system")
            self._persist_engine_state({"running": False})

    def stop(self) -> None:
        log.info("engine.stop_requested")
        self._running = False

    def _handle_signal(self, sig: signal.Signals) -> None:
        """Handle SIGTERM/SIGINT for graceful shutdown."""
        log.info("engine.signal_received", signal=sig.name)
        self.stop()

    # ── Cycle ────────────────────────────────────────────────────────

    async def _run_cycle(self) -> CycleResult:
        self._cycle_count += 1
        cycle = CycleResult(cycle_id=self._cycle_count, started_at=time.time())
        log.info("engine.cycle_start", cycle_id=cycle.cycle_id)

        try:
            for hook in self._pre_cycle_hooks:
                try:
                    if asyncio.iscoroutinefunction(hook):
                        await hook()
                    else:
                        hook()
                except Exception as e:
                    log.warning("engine.hook_error", hook=str(hook), error=str(e))

            can_trade, dd_reason = self.drawdown.can_trade()
            if not can_trade:
                log.warning("engine.drawdown_halt", reason=dd_reason)
                cycle.status = "skipped"
                cycle.errors.append(f"Drawdown halt: {dd_reason}")
                if self._db:
                    self._db.insert_alert("warning", f"Cycle skipped: {dd_reason}", "risk")
                self._finish_cycle(cycle)
                return cycle

            # ── Regime Detection ─────────────────────────────────────
            try:
                if self._db:
                    self._current_regime = self._regime_detector.detect(
                        self._db.conn,
                    )
                    # Persist regime state for dashboard
                    import datetime as _dt
                    self._db.conn.execute("""
                        INSERT INTO regime_history
                            (regime, confidence, kelly_multiplier,
                             size_multiplier, explanation, detected_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        self._current_regime.regime,
                        self._current_regime.confidence,
                        self._current_regime.kelly_multiplier,
                        self._current_regime.size_multiplier,
                        self._current_regime.explanation,
                        _dt.datetime.now(_dt.timezone.utc).isoformat(),
                    ))
                    self._db.conn.commit()
            except Exception as e:
                log.warning("engine.regime_detection_error", error=str(e))

            # ── Calibration check ────────────────────────────────────
            try:
                if self._db and self._cycle_count % 10 == 0:
                    self._calibration_loop.retrain_calibrator(self._db.conn)
            except Exception as e:
                log.warning("engine.calibration_retrain_error", error=str(e))
                return cycle

            markets = await self._discover_markets()
            cycle.markets_scanned = len(markets)

            if not markets:
                log.info("engine.no_markets")
                cycle.status = "completed"
                self._finish_cycle(cycle)
                return cycle

            # Pre-research filter — skip low-quality markets before SerpAPI
            blocked_types = set(self.config.scanning.filter_blocked_types)
            preferred_types = self.config.scanning.preferred_types or None
            min_score = self.config.scanning.filter_min_score
            max_per_cycle = self.config.engine.max_markets_per_cycle

            self._research_cache.clear_stale()

            filtered, fstats = filter_markets(
                markets,
                min_score=min_score,
                max_pass=max_per_cycle,
                research_cache=self._research_cache,
                blocked_types=blocked_types,
                preferred_types=preferred_types,
            )
            self._last_filter_stats = fstats
            cycle.markets_researched = len(filtered)

            if not filtered:
                log.info("engine.all_filtered", stats=fstats.__dict__)
                cycle.status = "completed"
                self._finish_cycle(cycle)
                return cycle

            for candidate in filtered:
                try:
                    result = await self._process_candidate(candidate, cycle.cycle_id)
                    # Mark as researched so it's skipped for cooldown period
                    self._research_cache.mark_researched(
                        getattr(candidate, "id", ""),
                    )
                    if result.get("has_edge"):
                        cycle.edges_found += 1
                    if result.get("trade_attempted"):
                        cycle.trades_attempted += 1
                    if result.get("trade_executed"):
                        cycle.trades_executed += 1
                except Exception as e:
                    log.error(
                        "engine.candidate_error",
                        market_id=getattr(candidate, "id", "?"),
                        error=str(e),
                    )
                    cycle.errors.append(str(e))
                    traceback.print_exc()

            await self._check_positions()
            await self._maybe_scan_wallets()
            cycle.status = "completed"

        except Exception as e:
            cycle.status = "error"
            cycle.errors.append(str(e))
            log.error("engine.cycle_failed", error=str(e))

        for hook in self._post_cycle_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
            except Exception as e:
                log.warning("engine.hook_error", hook=str(hook), error=str(e))

        self._finish_cycle(cycle)
        return cycle

    def _finish_cycle(self, cycle: CycleResult) -> None:
        cycle.ended_at = time.time()
        cycle.duration_secs = round(cycle.ended_at - cycle.started_at, 2)
        self._cycle_history.append(cycle)
        if len(self._cycle_history) > 100:
            self._cycle_history = self._cycle_history[-50:]

        log.info(
            "engine.cycle_complete",
            cycle_id=cycle.cycle_id,
            duration=cycle.duration_secs,
            scanned=cycle.markets_scanned,
            researched=cycle.markets_researched,
            edges=cycle.edges_found,
            trades=cycle.trades_executed,
            status=cycle.status,
        )
        if self._db:
            self._db.insert_alert(
                "info",
                f"Cycle {cycle.cycle_id}: scanned={cycle.markets_scanned} "
                f"researched={cycle.markets_researched} edges={cycle.edges_found} "
                f"trades={cycle.trades_executed} ({cycle.duration_secs:.1f}s)",
                "engine",
            )

    # ── Market Discovery ─────────────────────────────────────────────

    async def _discover_markets(self) -> list[Any]:
        from src.connectors.polymarket_gamma import fetch_active_markets
        try:
            markets = await fetch_active_markets(
                min_volume=self.config.risk.min_liquidity, limit=200,
            )
            return markets
        except Exception as e:
            log.error("engine.discovery_error", error=str(e))
            return []

    async def _rank_markets(self, markets: list[Any]) -> list[Any]:
        scored = []
        for m in markets:
            score = (
                m.volume * 0.3
                + m.liquidity * 0.5
                + (1.0 if m.has_clear_resolution else 0.0) * 0.2
            )
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    # ── Full Pipeline ────────────────────────────────────────────────

    async def _process_candidate(self, market: Any, cycle_id: int) -> dict[str, Any]:
        """Process a single market through the full research-to-trade pipeline."""
        result = {"has_edge": False, "trade_attempted": False, "trade_executed": False}
        market_id = market.id
        question = market.question

        # ── Stage 0: Classification ──────────────────────────────────
        from src.engine.market_classifier import classify_and_log
        classification = classify_and_log(market)

        log.info(
            "engine.pipeline_start",
            market_id=market_id,
            question=question[:80],
            market_type=market.market_type,
            category=classification.category,
            subcategory=classification.subcategory,
            researchability=classification.researchability,
        )

        # ── Stage 1: Research ────────────────────────────────────────
        from src.research.query_builder import build_queries
        from src.research.source_fetcher import SourceFetcher
        from src.research.evidence_extractor import EvidenceExtractor
        from src.connectors.web_search import create_search_provider

        search_provider = create_search_provider(self.config.research.search_provider)
        source_fetcher = SourceFetcher(search_provider, self.config.research)

        try:
            # Adaptive query budget from classifier — pass category + researchability
            max_q = classification.recommended_queries
            queries = build_queries(
                market, max_queries=max_q,
                category=classification.category,
                researchability=classification.researchability,
            )
            sources = await source_fetcher.fetch_sources(
                queries, market_type=classification.category or market.market_type,
                max_sources=self.config.research.max_sources,
            )
            extractor = EvidenceExtractor(self.config.forecasting)
            evidence = await extractor.extract(
                market_id=market_id, question=question,
                sources=sources, market_type=market.market_type,
            )
        except Exception as e:
            log.error("engine.research_failed", market_id=market_id, error=str(e))
            self._log_candidate(cycle_id, market, decision="SKIP",
                                reason=f"Research failed: {e}")
            return result
        finally:
            await source_fetcher.close()
            await search_provider.close()

        log.info(
            "engine.research_done", market_id=market_id,
            sources=len(sources), bullets=len(evidence.bullets),
            quality=round(evidence.quality_score, 3),
        )

        # ── Stage 2: Build Features ──────────────────────────────────
        from src.forecast.feature_builder import build_features
        features = build_features(market=market, evidence=evidence)

        # ── Stage 3: Forecast ────────────────────────────────────────
        # Use ensemble forecaster when enabled, otherwise single-model
        if self.config.ensemble.enabled:
            from src.forecast.ensemble import EnsembleForecaster
            ens_forecaster = EnsembleForecaster(
                self.config.ensemble, self.config.forecasting,
            )
            ens_result = await ens_forecaster.forecast(
                features=features, evidence=evidence,
            )
            # Adapt EnsembleResult into ForecastResult-like interface
            from src.forecast.llm_forecaster import ForecastResult
            forecast = ForecastResult(
                market_id=market_id,
                question=question,
                market_type=market.market_type,
                resolution_source=market.resolution_source,
                implied_probability=features.implied_probability,
                model_probability=ens_result.model_probability,
                edge=ens_result.model_probability - features.implied_probability,
                confidence_level=ens_result.confidence_level,
                evidence=ens_result.key_evidence,
                invalidation_triggers=ens_result.invalidation_triggers,
                reasoning=ens_result.reasoning,
                evidence_quality=evidence.quality_score,
                num_sources=evidence.num_sources,
                raw_llm_response={
                    "ensemble": True,
                    "models_succeeded": ens_result.models_succeeded,
                    "models_failed": ens_result.models_failed,
                    "spread": ens_result.spread,
                    "agreement": ens_result.agreement_score,
                    "aggregation": ens_result.aggregation_method,
                },
            )
            # Apply low-evidence penalty (same logic as LLMForecaster)
            if evidence.quality_score < self.config.forecasting.min_evidence_quality:
                penalty = self.config.forecasting.low_evidence_penalty
                old_prob = forecast.model_probability
                forecast.model_probability = old_prob * (1 - penalty) + 0.5 * penalty
                forecast.edge = forecast.model_probability - features.implied_probability
                log.info("engine.ensemble_low_evidence_penalty",
                         original=round(old_prob, 3),
                         adjusted=round(forecast.model_probability, 3))
        else:
            from src.forecast.llm_forecaster import LLMForecaster
            forecaster = LLMForecaster(self.config.forecasting)
            forecast = await forecaster.forecast(
                features=features, evidence=evidence,
                resolution_source=market.resolution_source,
            )

        # ── Adaptive model weights (learn per-category accuracy) ─────
        adaptive_result = None
        try:
            if self._db:
                cat = classification.category if classification else "UNKNOWN"
                adaptive_result = self._adaptive_weighter.get_weights(
                    self._db.conn, cat,
                )
                if adaptive_result.data_available:
                    log.info(
                        "engine.adaptive_weights",
                        category=cat,
                        blend=round(adaptive_result.blend_factor, 3),
                        weights={k: round(v, 3)
                                 for k, v in adaptive_result.weights.items()},
                    )
        except Exception as e:
            log.warning("engine.adaptive_weights_error", error=str(e))

        log.info(
            "engine.forecast_done", market_id=market_id,
            implied=round(forecast.implied_probability, 3),
            model=round(forecast.model_probability, 3),
            edge=round(forecast.edge, 3),
            confidence=forecast.confidence_level,
        )

        # ── Stage 4: Edge Calculation ────────────────────────────────
        from src.policy.edge_calc import calculate_edge
        edge_result = calculate_edge(
            implied_prob=forecast.implied_probability,
            model_prob=forecast.model_probability,
            transaction_fee_pct=self.config.risk.transaction_fee_pct,
            gas_cost_usd=self.config.risk.gas_cost_usd,
        )

        # ── Stage 4b: Whale / Smart-Money Edge Adjustment ───────────
        if (self.config.wallet_scanner.enabled
                and self._latest_scan_result
                and hasattr(self._latest_scan_result, "conviction_signals")):
            whale_cfg = self.config.wallet_scanner
            for sig in self._latest_scan_result.conviction_signals:
                if getattr(sig, "market_id", None) != market_id:
                    continue
                whale_agrees = (
                    (sig.direction == "BUY" and edge_result.direction == "BUY_YES")
                    or (sig.direction == "SELL" and edge_result.direction == "BUY_NO")
                )
                if whale_agrees:
                    boost = whale_cfg.conviction_edge_boost
                    edge_result = calculate_edge(
                        implied_prob=forecast.implied_probability,
                        model_prob=min(0.99, forecast.model_probability + boost)
                        if edge_result.direction == "BUY_YES"
                        else forecast.model_probability,
                        transaction_fee_pct=self.config.risk.transaction_fee_pct,
                        gas_cost_usd=self.config.risk.gas_cost_usd,
                    )
                    log.info("engine.whale_edge_boost", market_id=market_id,
                             boost=boost, new_edge=round(edge_result.abs_net_edge, 4))
                else:
                    penalty = whale_cfg.conviction_edge_penalty
                    edge_result = calculate_edge(
                        implied_prob=forecast.implied_probability,
                        model_prob=max(0.01, forecast.model_probability - penalty)
                        if edge_result.direction == "BUY_YES"
                        else min(0.99, forecast.model_probability + penalty),
                        transaction_fee_pct=self.config.risk.transaction_fee_pct,
                        gas_cost_usd=self.config.risk.gas_cost_usd,
                    )
                    log.info("engine.whale_edge_penalty", market_id=market_id,
                             penalty=penalty, new_edge=round(edge_result.abs_net_edge, 4))
                break  # only apply first matching signal

        has_edge = edge_result.is_positive and edge_result.abs_net_edge >= self.config.risk.min_edge
        result["has_edge"] = has_edge

        # ── Stage 5: Risk Checks ─────────────────────────────────────
        from src.policy.risk_limits import check_risk_limits
        daily_pnl = self._db.get_daily_pnl() if self._db else 0.0
        open_positions = self._db.get_open_positions_count() if self._db else 0
        risk_result = check_risk_limits(
            edge=edge_result, features=features,
            risk_config=self.config.risk,
            forecast_config=self.config.forecasting,
            current_open_positions=open_positions,
            daily_pnl=daily_pnl,
            market_type=market.market_type,
            allowed_types=self.config.scanning.preferred_types or None,
            restricted_types=self.config.scanning.restricted_types or None,
            drawdown_state=self.drawdown.state,
        )

        # ── Persist forecast to DB ───────────────────────────────────
        if self._db:
            from src.storage.models import ForecastRecord, MarketRecord
            self._db.upsert_market(MarketRecord(
                id=market_id, condition_id=market.condition_id,
                question=question, market_type=market.market_type,
                category=market.category, volume=market.volume,
                liquidity=market.liquidity,
                end_date=market.end_date.isoformat() if market.end_date else "",
                resolution_source=market.resolution_source,
            ))
            self._db.insert_forecast(ForecastRecord(
                id=str(uuid.uuid4()), market_id=market_id,
                question=question, market_type=market.market_type,
                implied_probability=forecast.implied_probability,
                model_probability=forecast.model_probability,
                edge=forecast.edge,
                confidence_level=forecast.confidence_level,
                evidence_quality=evidence.quality_score,
                num_sources=evidence.num_sources,
                decision=risk_result.decision,
                reasoning=forecast.reasoning[:500],
                evidence_json=json.dumps(forecast.evidence[:5]),
                invalidation_triggers_json=json.dumps(forecast.invalidation_triggers),
                research_evidence_json=json.dumps({
                    **evidence.to_dict(),
                    "classification": classification.to_dict(),
                }),
            ))

        # ── Decision Gate ────────────────────────────────────────────
        if not risk_result.allowed:
            log.info("engine.no_trade", market_id=market_id, violations=risk_result.violations)
            self._log_candidate(
                cycle_id, market, forecast=forecast, evidence=evidence,
                edge_result=edge_result, decision="NO TRADE",
                reason="; ".join(risk_result.violations),
            )
            if self._audit:
                self._audit.record_trade_decision(
                    market_id=market_id, question=question,
                    model_prob=forecast.model_probability,
                    implied_prob=forecast.implied_probability,
                    edge=forecast.edge, confidence=forecast.confidence_level,
                    risk_result=risk_result.to_dict(), position_size=0.0,
                    evidence_summary=evidence.summary[:200],
                )
            return result

        # ── Stage 6: Position Sizing ─────────────────────────────────
        from src.policy.position_sizer import calculate_position_size
        regime_kelly = (
            self._current_regime.kelly_multiplier
            if self._current_regime else 1.0
        )
        regime_size = (
            self._current_regime.size_multiplier
            if self._current_regime else 1.0
        )
        position = calculate_position_size(
            edge=edge_result, risk_config=self.config.risk,
            confidence_level=forecast.confidence_level,
            drawdown_multiplier=self.drawdown.state.kelly_multiplier,
            timeline_multiplier=features.time_decay_multiplier,
            price_volatility=features.price_volatility,
            regime_multiplier=regime_kelly * regime_size,
        )
        if position.stake_usd < 1.0:
            log.info("engine.stake_too_small", market_id=market_id, stake=position.stake_usd)
            self._log_candidate(
                cycle_id, market, forecast=forecast, evidence=evidence,
                edge_result=edge_result, decision="NO TRADE",
                reason="Stake too small", stake=position.stake_usd,
            )
            return result

        result["trade_attempted"] = True

        # ── Stage 7: Build & Route Order ─────────────────────────────
        from src.execution.order_builder import build_order
        from src.execution.order_router import OrderRouter
        from src.connectors.polymarket_clob import CLOBClient

        yes_tokens = [t for t in market.tokens if t.outcome.lower() == "yes"]
        no_tokens = [t for t in market.tokens if t.outcome.lower() == "no"]
        # For non-Yes/No markets, treat first token as "yes", second as "no"
        if not yes_tokens and not no_tokens and len(market.tokens) >= 2:
            yes_tokens = [market.tokens[0]]
            no_tokens = [market.tokens[1]]
        elif not yes_tokens and market.tokens:
            yes_tokens = [market.tokens[0]]
        if edge_result.direction == "BUY_YES" and yes_tokens:
            token_id = yes_tokens[0].token_id
            implied_price = yes_tokens[0].price or forecast.implied_probability
        elif edge_result.direction == "BUY_NO" and no_tokens:
            token_id = no_tokens[0].token_id
            implied_price = no_tokens[0].price or (1 - forecast.implied_probability)
        else:
            token_id = (yes_tokens[0].token_id if yes_tokens
                        else (no_tokens[0].token_id if no_tokens else ""))
            implied_price = forecast.implied_probability
        if not token_id:
            log.warning("engine.no_token_id", market_id=market_id)
            self._log_candidate(
                cycle_id, market, forecast=forecast, evidence=evidence,
                edge_result=edge_result, decision="NO TRADE",
                reason="No token ID available",
            )
            return result

        # ── Smart Entry: Calculate optimal entry price ───────────────
        entry_plan = None
        execution_strategy = "simple"
        try:
            regime_patience = (
                self._current_regime.entry_patience
                if self._current_regime else 1.0
            )
            entry_plan = self._smart_entry.calculate_entry(
                market_id=market_id,
                side=edge_result.direction,
                current_price=implied_price,
                fair_value=forecast.model_probability,
                edge=edge_result.abs_net_edge,
                spread=getattr(features, "spread", 0.0),
                hours_to_resolution=getattr(features, "hours_to_resolution", 720.0),
                regime_patience=regime_patience,
            )
            if entry_plan and entry_plan.recommended_price > 0:
                old_price = implied_price
                implied_price = entry_plan.recommended_price
                if entry_plan.recommended_strategy == "twap":
                    execution_strategy = "twap"
                log.info(
                    "engine.smart_entry",
                    market_id=market_id,
                    old_price=round(old_price, 4),
                    new_price=round(implied_price, 4),
                    strategy=entry_plan.recommended_strategy,
                    improvement_bps=round(entry_plan.expected_improvement_bps, 1),
                )
        except Exception as e:
            log.warning("engine.smart_entry_error", error=str(e))

        orders = build_order(
            market_id=market_id, token_id=token_id,
            position=position, implied_price=implied_price,
            config=self.config.execution, execution_strategy=execution_strategy,
        )

        clob = CLOBClient()
        router = OrderRouter(clob, self.config.execution)
        order_statuses: list[str] = []
        try:
            for order in orders:
                order_result = await router.submit_order(order)
                order_statuses.append(order_result.status)
                log.info(
                    "engine.order_result", market_id=market_id,
                    order_id=order_result.order_id[:8],
                    status=order_result.status,
                    fill_price=order_result.fill_price,
                    fill_size=order_result.fill_size,
                )
                if self._db:
                    from src.storage.models import TradeRecord, PositionRecord
                    self._db.insert_trade(TradeRecord(
                        id=str(uuid.uuid4()),
                        order_id=order_result.order_id,
                        market_id=market_id, token_id=token_id,
                        side=edge_result.direction,
                        price=order_result.fill_price,
                        size=order_result.fill_size,
                        stake_usd=position.stake_usd,
                        status=order_result.status.upper(),
                        dry_run=order_result.status == "simulated",
                    ))
                    self._db.upsert_position(PositionRecord(
                        market_id=market_id, token_id=token_id,
                        direction=edge_result.direction,
                        entry_price=order_result.fill_price,
                        size=order_result.fill_size,
                        stake_usd=position.stake_usd,
                        current_price=order_result.fill_price, pnl=0.0,
                    ))
                result["trade_executed"] = True
        finally:
            await clob.close()

        # ── Stage 8: Audit ───────────────────────────────────────────
        if self._audit:
            self._audit.record_trade_decision(
                market_id=market_id, question=question,
                model_prob=forecast.model_probability,
                implied_prob=forecast.implied_probability,
                edge=forecast.edge, confidence=forecast.confidence_level,
                risk_result=risk_result.to_dict(),
                position_size=position.stake_usd,
                order_id=orders[0].order_id if orders else "",
                evidence_summary=evidence.summary[:200],
            )

        self._log_candidate(
            cycle_id, market, forecast=forecast, evidence=evidence,
            edge_result=edge_result, decision="TRADE",
            reason="All checks passed", stake=position.stake_usd,
            order_status=order_statuses[0] if order_statuses else "",
        )
        if self._db:
            mode = "\U0001f9ea Paper" if order_statuses and order_statuses[0] == "simulated" else "\U0001f4b0 Live"
            self._db.insert_alert(
                "info",
                f'{mode} trade: {edge_result.direction} on "{question[:60]}" '
                f"\u2014 stake ${position.stake_usd:.2f}, edge {forecast.edge:+.3f}, "
                f"confidence {forecast.confidence_level}",
                "trade", market_id,
            )
        log.info(
            "engine.trade_executed", market_id=market_id,
            direction=edge_result.direction, stake=position.stake_usd,
            edge=round(forecast.edge, 3), status=order_statuses,
        )

        # ── Record for adaptive weighting (model accuracy log) ───────
        try:
            if self._db and hasattr(forecast, 'model_forecasts'):
                for model_name, prob in (forecast.model_forecasts or {}).items():
                    self._db.conn.execute("""
                        INSERT INTO model_forecast_log
                            (model_name, market_id, category, forecast_prob,
                             actual_outcome, recorded_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        model_name, market_id,
                        classification.category if classification else "UNKNOWN",
                        prob, -1.0,  # actual_outcome set to -1 = unresolved
                        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    ))
                    self._db.conn.commit()
        except Exception as e:
            log.warning("engine.model_forecast_log_error", error=str(e))

        return result

    def _log_candidate(
        self, cycle_id: int, market: Any,
        forecast: Any = None, evidence: Any = None,
        edge_result: Any = None,
        decision: str = "SKIP", reason: str = "",
        stake: float = 0.0, order_status: str = "",
    ) -> None:
        if not self._db:
            return
        try:
            self._db.insert_candidate(
                cycle_id=cycle_id, market_id=market.id,
                question=market.question[:200],
                market_type=market.market_type,
                implied_prob=(getattr(forecast, "implied_probability", market.best_bid)
                              if forecast else market.best_bid),
                model_prob=(getattr(forecast, "model_probability", 0.0)
                            if forecast else 0.0),
                edge=getattr(forecast, "edge", 0.0) if forecast else 0.0,
                evidence_quality=(getattr(evidence, "quality_score", 0.0)
                                  if evidence else 0.0),
                num_sources=(getattr(evidence, "num_sources", 0)
                             if evidence else 0),
                confidence=(getattr(forecast, "confidence_level", "")
                            if forecast else ""),
                decision=decision, decision_reasons=reason[:300],
                stake_usd=stake, order_status=order_status,
            )
        except Exception as e:
            log.warning("engine.log_candidate_error", error=str(e))

    async def _check_positions(self) -> None:
        """Fetch live prices for all open positions and update PNL."""
        if not self._db:
            return

        positions = self._db.get_open_positions()
        if not positions:
            self._positions = []
            return

        from src.connectors.polymarket_gamma import GammaClient

        client = GammaClient()
        snapshots: list[PositionSnapshot] = []
        try:
            for pos in positions:
                try:
                    market = await client.get_market(pos.market_id)

                    # Find the matching token price
                    current_price = pos.current_price  # fallback
                    for tok in market.tokens:
                        if tok.token_id == pos.token_id:
                            current_price = tok.price
                            break

                    # Calculate PNL based on direction
                    if pos.direction in ("BUY_YES", "BUY"):
                        pnl = (current_price - pos.entry_price) * pos.size
                    elif pos.direction in ("BUY_NO", "SELL"):
                        pnl = (pos.entry_price - current_price) * pos.size
                    else:
                        pnl = (current_price - pos.entry_price) * pos.size

                    self._db.update_position_price(
                        pos.market_id, current_price, round(pnl, 4),
                    )

                    # Build snapshot for portfolio risk
                    mkt_record = self._db.get_market(pos.market_id)
                    snapshots.append(PositionSnapshot(
                        market_id=pos.market_id,
                        question=mkt_record.question if mkt_record else "",
                        category=mkt_record.category if mkt_record else "",
                        event_slug=market.slug or "",
                        side="YES" if pos.direction in ("BUY_YES", "BUY") else "NO",
                        size_usd=pos.stake_usd,
                        entry_price=pos.entry_price,
                        current_price=current_price,
                        unrealised_pnl=round(pnl, 4),
                    ))

                    log.info(
                        "engine.position_update",
                        market_id=pos.market_id[:8],
                        entry=pos.entry_price,
                        current=current_price,
                        pnl=round(pnl, 4),
                    )

                except Exception as e:
                    log.warning(
                        "engine.position_price_error",
                        market_id=pos.market_id[:8],
                        error=str(e),
                    )
                    # Keep stale snapshot
                    snapshots.append(PositionSnapshot(
                        market_id=pos.market_id,
                        question="",
                        category="",
                        event_slug="",
                        side="YES" if pos.direction in ("BUY_YES", "BUY") else "NO",
                        size_usd=pos.stake_usd,
                        entry_price=pos.entry_price,
                        current_price=pos.current_price,
                        unrealised_pnl=pos.pnl,
                    ))

        finally:
            await client.close()

        self._positions = snapshots
        log.info(
            "engine.positions_checked",
            count=len(snapshots),
            total_pnl=round(sum(s.unrealised_pnl for s in snapshots), 4),
        )

    async def _maybe_scan_wallets(self) -> None:
        """Run wallet scanner if enabled and interval elapsed."""
        if not self.config.wallet_scanner.enabled:
            return

        interval = self.config.wallet_scanner.scan_interval_minutes * 60
        now = time.time()
        if now - self._last_wallet_scan < interval:
            return

        log.info("engine.wallet_scan_start")
        try:
            result = await self._wallet_scanner.scan()
            self._latest_scan_result = result
            self._last_wallet_scan = now

            # Persist to database
            if self._db:
                import sqlite3
                db_path = self.config.storage.sqlite_path
                conn = sqlite3.connect(db_path)
                try:
                    save_scan_result(conn, result)
                finally:
                    conn.close()

            log.info(
                "engine.wallet_scan_complete",
                wallets=result.wallets_scanned,
                signals=len(result.conviction_signals),
                deltas=len(result.deltas),
            )
        except Exception as e:
            log.warning("engine.wallet_scan_error", error=str(e))

    def get_status(self) -> dict[str, Any]:
        dd_state = self.drawdown.state
        pr_report = self.portfolio.assess(self._positions)
        return {
            "running": self._running,
            "cycle_count": self._cycle_count,
            "live_trading": is_live_trading_enabled(),
            "drawdown": dd_state.to_dict(),
            "portfolio": pr_report.to_dict(),
            "last_cycle": (
                self._cycle_history[-1].to_dict()
                if self._cycle_history else None
            ),
            "positions": len(self._positions),
            "filter_stats": (
                self._last_filter_stats.__dict__
                if self._last_filter_stats else None
            ),
            "research_cache_size": self._research_cache.size(),
        }
