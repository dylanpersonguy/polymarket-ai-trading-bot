"""Position manager — monitor positions, trigger exits.

Exit strategies:
  1. Stop-loss: Exit if unrealised loss exceeds threshold
  2. Take-profit: Exit if unrealised profit hits target
  3. Time-based: Exit before market resolution
  4. Edge reversal: Exit if model probability flips direction
  5. Drawdown: Force exit all positions when kill-switch triggers
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from src.policy.portfolio_risk import PositionSnapshot
from src.observability.logger import get_logger

log = get_logger(__name__)


@dataclass
class ExitSignal:
    """Signal to exit a position."""
    market_id: str
    reason: str  # "stop_loss" | "take_profit" | "time_exit" | "edge_reversal" | "kill_switch"
    urgency: str  # "immediate" | "soon" | "optional"
    current_pnl_pct: float
    details: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


@dataclass
class PositionRecord:
    """Full position record with tracking data."""
    market_id: str
    question: str
    category: str
    event_slug: str
    side: str  # "YES" | "NO"
    size_usd: float
    entry_price: float
    entry_time: float
    current_price: float = 0.0
    unrealised_pnl: float = 0.0
    realised_pnl: float = 0.0
    status: str = "open"  # "open" | "closing" | "closed"
    exit_time: float = 0.0
    exit_price: float = 0.0
    exit_reason: str = ""

    # Model tracking
    entry_model_prob: float = 0.0
    entry_edge: float = 0.0
    entry_confidence: str = "LOW"

    # Risk tracking
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    max_unrealised_pnl: float = 0.0
    min_unrealised_pnl: float = 0.0

    @property
    def pnl_pct(self) -> float:
        if self.size_usd > 0:
            return self.unrealised_pnl / self.size_usd
        return 0.0

    @property
    def holding_hours(self) -> float:
        end = self.exit_time if self.exit_time > 0 else time.time()
        return (end - self.entry_time) / 3600

    def to_snapshot(self) -> PositionSnapshot:
        return PositionSnapshot(
            market_id=self.market_id,
            question=self.question,
            category=self.category,
            event_slug=self.event_slug,
            side=self.side,
            size_usd=self.size_usd,
            entry_price=self.entry_price,
            current_price=self.current_price,
            unrealised_pnl=self.unrealised_pnl,
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


class PositionManager:
    """Track and manage all open positions."""

    def __init__(
        self,
        stop_loss_pct: float = 0.20,
        take_profit_pct: float = 0.50,
        exit_before_hours: float = 12.0,
    ):
        self.positions: dict[str, PositionRecord] = {}
        self.closed_positions: list[PositionRecord] = []
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.exit_before_hours = exit_before_hours

    def open_position(
        self,
        market_id: str,
        question: str,
        category: str,
        event_slug: str,
        side: str,
        size_usd: float,
        entry_price: float,
        model_prob: float = 0.0,
        edge: float = 0.0,
        confidence: str = "LOW",
    ) -> PositionRecord:
        """Record a new position."""
        # Calculate stop-loss and take-profit prices
        if side == "YES":
            stop_price = max(0.01, entry_price * (1 - self.stop_loss_pct))
            tp_price = min(0.99, entry_price * (1 + self.take_profit_pct))
        else:
            # For NO positions, direction is inverted
            stop_price = min(0.99, entry_price * (1 + self.stop_loss_pct))
            tp_price = max(0.01, entry_price * (1 - self.take_profit_pct))

        pos = PositionRecord(
            market_id=market_id,
            question=question,
            category=category,
            event_slug=event_slug,
            side=side,
            size_usd=size_usd,
            entry_price=entry_price,
            entry_time=time.time(),
            current_price=entry_price,
            entry_model_prob=model_prob,
            entry_edge=edge,
            entry_confidence=confidence,
            stop_loss_price=stop_price,
            take_profit_price=tp_price,
        )

        self.positions[market_id] = pos
        log.info(
            "position.opened",
            market_id=market_id,
            side=side,
            size=size_usd,
            entry=entry_price,
            stop=round(stop_price, 3),
            tp=round(tp_price, 3),
        )
        return pos

    def update_price(self, market_id: str, current_price: float) -> None:
        """Update current price and unrealised P&L for a position."""
        pos = self.positions.get(market_id)
        if not pos:
            return

        pos.current_price = current_price

        # Calculate unrealised P&L
        if pos.side == "YES":
            # Bought YES tokens at entry_price
            # They pay 1.0 if correct, current value is current_price
            pos.unrealised_pnl = (current_price - pos.entry_price) * (
                pos.size_usd / pos.entry_price
            )
        else:
            # Bought NO tokens (1 - entry_price)
            pos.unrealised_pnl = (pos.entry_price - current_price) * (
                pos.size_usd / (1 - pos.entry_price)
            )

        # Track high water mark and maximum loss
        pos.max_unrealised_pnl = max(pos.max_unrealised_pnl, pos.unrealised_pnl)
        pos.min_unrealised_pnl = min(pos.min_unrealised_pnl, pos.unrealised_pnl)

    def check_exits(
        self,
        hours_to_resolution: dict[str, float] | None = None,
        model_probs: dict[str, float] | None = None,
        force_exit_all: bool = False,
    ) -> list[ExitSignal]:
        """Check all positions for exit conditions.

        Args:
            hours_to_resolution: market_id -> hours until resolution
            model_probs: market_id -> current model probability
            force_exit_all: if True (kill switch), exit everything
        """
        signals: list[ExitSignal] = []

        for market_id, pos in list(self.positions.items()):
            if pos.status != "open":
                continue

            # Kill switch — exit all
            if force_exit_all:
                signals.append(ExitSignal(
                    market_id=market_id,
                    reason="kill_switch",
                    urgency="immediate",
                    current_pnl_pct=pos.pnl_pct,
                    details="Drawdown kill switch engaged — liquidating all positions",
                ))
                continue

            # Stop-loss
            if pos.side == "YES" and pos.current_price <= pos.stop_loss_price:
                signals.append(ExitSignal(
                    market_id=market_id,
                    reason="stop_loss",
                    urgency="immediate",
                    current_pnl_pct=pos.pnl_pct,
                    details=(
                        f"Price {pos.current_price:.3f} <= "
                        f"stop {pos.stop_loss_price:.3f}"
                    ),
                ))
            elif pos.side == "NO" and pos.current_price >= pos.stop_loss_price:
                signals.append(ExitSignal(
                    market_id=market_id,
                    reason="stop_loss",
                    urgency="immediate",
                    current_pnl_pct=pos.pnl_pct,
                    details=(
                        f"Price {pos.current_price:.3f} >= "
                        f"stop {pos.stop_loss_price:.3f}"
                    ),
                ))

            # Take-profit
            if pos.side == "YES" and pos.current_price >= pos.take_profit_price:
                signals.append(ExitSignal(
                    market_id=market_id,
                    reason="take_profit",
                    urgency="soon",
                    current_pnl_pct=pos.pnl_pct,
                    details=(
                        f"Price {pos.current_price:.3f} >= "
                        f"TP {pos.take_profit_price:.3f}"
                    ),
                ))
            elif pos.side == "NO" and pos.current_price <= pos.take_profit_price:
                signals.append(ExitSignal(
                    market_id=market_id,
                    reason="take_profit",
                    urgency="soon",
                    current_pnl_pct=pos.pnl_pct,
                    details=(
                        f"Price {pos.current_price:.3f} <= "
                        f"TP {pos.take_profit_price:.3f}"
                    ),
                ))

            # Time-based exit
            if hours_to_resolution and market_id in hours_to_resolution:
                hrs = hours_to_resolution[market_id]
                if hrs <= self.exit_before_hours:
                    signals.append(ExitSignal(
                        market_id=market_id,
                        reason="time_exit",
                        urgency="soon" if hrs > 2 else "immediate",
                        current_pnl_pct=pos.pnl_pct,
                        details=f"Only {hrs:.1f}h to resolution",
                    ))

            # Edge reversal
            if model_probs and market_id in model_probs:
                new_prob = model_probs[market_id]
                if pos.side == "YES" and new_prob < pos.entry_price * 0.9:
                    signals.append(ExitSignal(
                        market_id=market_id,
                        reason="edge_reversal",
                        urgency="soon",
                        current_pnl_pct=pos.pnl_pct,
                        details=(
                            f"Model prob {new_prob:.3f} dropped below "
                            f"entry {pos.entry_price:.3f}"
                        ),
                    ))
                elif pos.side == "NO" and new_prob > (1 - pos.entry_price) * 1.1:
                    signals.append(ExitSignal(
                        market_id=market_id,
                        reason="edge_reversal",
                        urgency="soon",
                        current_pnl_pct=pos.pnl_pct,
                        details=(
                            f"Model prob {new_prob:.3f} reversed against NO position"
                        ),
                    ))

        if signals:
            log.info(
                "position_manager.exit_signals",
                count=len(signals),
                immediate=sum(1 for s in signals if s.urgency == "immediate"),
            )
        return signals

    def close_position(
        self,
        market_id: str,
        exit_price: float,
        reason: str,
    ) -> PositionRecord | None:
        """Close a position and move to closed list."""
        pos = self.positions.get(market_id)
        if not pos:
            return None

        pos.status = "closed"
        pos.exit_time = time.time()
        pos.exit_price = exit_price
        pos.exit_reason = reason

        # Final P&L
        if pos.side == "YES":
            pos.realised_pnl = (exit_price - pos.entry_price) * (
                pos.size_usd / pos.entry_price
            )
        else:
            pos.realised_pnl = (pos.entry_price - exit_price) * (
                pos.size_usd / (1 - pos.entry_price)
            )

        del self.positions[market_id]
        self.closed_positions.append(pos)

        log.info(
            "position.closed",
            market_id=market_id,
            reason=reason,
            realised_pnl=round(pos.realised_pnl, 2),
            holding_hours=round(pos.holding_hours, 1),
        )
        return pos

    def get_snapshots(self) -> list[PositionSnapshot]:
        """Get current position snapshots for portfolio risk."""
        return [pos.to_snapshot() for pos in self.positions.values()]

    def total_unrealised_pnl(self) -> float:
        return sum(p.unrealised_pnl for p in self.positions.values())

    def total_realised_pnl(self) -> float:
        return sum(p.realised_pnl for p in self.closed_positions)

    def get_summary(self) -> dict[str, Any]:
        """Dashboard-friendly summary."""
        open_pos = list(self.positions.values())
        return {
            "open_count": len(open_pos),
            "closed_count": len(self.closed_positions),
            "total_unrealised_pnl": round(self.total_unrealised_pnl(), 2),
            "total_realised_pnl": round(self.total_realised_pnl(), 2),
            "positions": [p.to_dict() for p in open_pos],
            "recent_closed": [
                p.to_dict() for p in self.closed_positions[-10:]
            ],
        }
