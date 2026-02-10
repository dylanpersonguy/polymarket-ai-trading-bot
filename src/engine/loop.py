"""Continuous trading loop — the brain of the bot.

Runs on a configurable cycle (default 5 minutes):
  1. Discover & filter markets
  2. Build features for each market
  3. Research top candidates (evidence gathering)
  4. Forecast probabilities
  5. Calculate edges
  6. Check risk limits
  7. Size positions
  8. Route orders
  9. Monitor existing positions for exits

Between cycles:
  - Check drawdown state
  - Monitor position exits (stop-loss, take-profit, time-based)
  - Process websocket updates
"""

from __future__ import annotations

import asyncio
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

from src.config import load_config, is_live_trading_enabled
from src.policy.drawdown import DrawdownManager
from src.policy.portfolio_risk import PortfolioRiskManager, PositionSnapshot
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
    status: str = "pending"  # "pending" | "completed" | "error" | "skipped"

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


class TradingEngine:
    """Continuous trading engine that coordinates all bot components.

    Usage:
        engine = TradingEngine()
        await engine.start()  # runs until stopped
        engine.stop()
    """

    def __init__(self, config: Any | None = None):
        self.config = config or load_config()
        self._running = False
        self._cycle_count = 0
        self._cycle_history: list[CycleResult] = []

        # Managers
        bankroll = self.config.risk.bankroll
        self.drawdown = DrawdownManager(bankroll, self.config)
        self.portfolio = PortfolioRiskManager(bankroll, self.config)

        # Callbacks for custom hooks
        self._pre_cycle_hooks: list[Callable] = []
        self._post_cycle_hooks: list[Callable] = []

        # Positions tracked in-memory (loaded from DB on start)
        self._positions: list[PositionSnapshot] = []

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

    async def start(self) -> None:
        """Start the continuous trading loop."""
        self._running = True
        interval = self.config.engine.cycle_interval_secs
        log.info(
            "engine.starting",
            interval_secs=interval,
            live_trading=is_live_trading_enabled(),
            bankroll=self.config.risk.bankroll,
        )

        while self._running:
            try:
                await self._run_cycle()
            except Exception as e:
                log.error("engine.cycle_error", error=str(e))
                traceback.print_exc()

            if self._running:
                log.info("engine.sleeping", seconds=interval)
                await asyncio.sleep(interval)

        log.info("engine.stopped", total_cycles=self._cycle_count)

    def stop(self) -> None:
        """Signal the engine to stop after current cycle."""
        log.info("engine.stop_requested")
        self._running = False

    async def _run_cycle(self) -> CycleResult:
        """Execute one full trading cycle."""
        self._cycle_count += 1
        cycle = CycleResult(
            cycle_id=self._cycle_count,
            started_at=time.time(),
        )

        log.info("engine.cycle_start", cycle_id=cycle.cycle_id)

        try:
            # Pre-cycle hooks
            for hook in self._pre_cycle_hooks:
                try:
                    if asyncio.iscoroutinefunction(hook):
                        await hook()
                    else:
                        hook()
                except Exception as e:
                    log.warning("engine.hook_error", hook=str(hook), error=str(e))

            # Check drawdown state
            can_trade, dd_reason = self.drawdown.can_trade()
            if not can_trade:
                log.warning("engine.drawdown_halt", reason=dd_reason)
                cycle.status = "skipped"
                cycle.errors.append(f"Drawdown halt: {dd_reason}")
                self._finish_cycle(cycle)
                return cycle

            # Step 1: Discover markets
            markets = await self._discover_markets()
            cycle.markets_scanned = len(markets)

            if not markets:
                log.info("engine.no_markets")
                cycle.status = "completed"
                self._finish_cycle(cycle)
                return cycle

            # Step 2: Score and rank markets
            candidates = await self._rank_markets(markets)

            # Step 3: Research top candidates
            max_per_cycle = self.config.engine.max_markets_per_cycle
            top = candidates[:max_per_cycle]
            cycle.markets_researched = len(top)

            # Step 4-7: Process each candidate
            for candidate in top:
                try:
                    result = await self._process_candidate(candidate)
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

            # Step 8: Check existing positions for exits
            await self._check_positions()

            cycle.status = "completed"

        except Exception as e:
            cycle.status = "error"
            cycle.errors.append(str(e))
            log.error("engine.cycle_failed", error=str(e))

        # Post-cycle hooks
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
        """Finalize a cycle result."""
        cycle.ended_at = time.time()
        cycle.duration_secs = round(cycle.ended_at - cycle.started_at, 2)
        self._cycle_history.append(cycle)

        # Keep last 100 cycles
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

    async def _discover_markets(self) -> list[Any]:
        """Discover active markets from Polymarket.

        Override this or use hooks for custom market discovery.
        """
        from src.connectors.polymarket_gamma import fetch_active_markets

        try:
            markets = await fetch_active_markets(
                min_volume=self.config.risk.min_liquidity,
                limit=200,
            )
            return markets
        except Exception as e:
            log.error("engine.discovery_error", error=str(e))
            return []

    async def _rank_markets(self, markets: list[Any]) -> list[Any]:
        """Rank markets by potential (volume, liquidity, type)."""
        # Simple ranking: prefer higher volume and liquidity
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

    async def _process_candidate(self, market: Any) -> dict[str, Any]:
        """Process a single market candidate through the full pipeline.

        Returns dict with keys: has_edge, trade_attempted, trade_executed
        """
        result = {"has_edge": False, "trade_attempted": False, "trade_executed": False}

        # This is a framework — actual implementation wires in
        # all the pipeline stages (research, forecast, edge, risk, sizing, execution)
        log.debug("engine.process_candidate", market_id=market.id)

        return result

    async def _check_positions(self) -> None:
        """Check existing positions for exit conditions."""
        # Framework for position monitoring
        # Actual exit logic lives in position_manager.py
        pass

    def get_status(self) -> dict[str, Any]:
        """Get current engine status for dashboard."""
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
                if self._cycle_history
                else None
            ),
            "positions": len(self._positions),
        }
