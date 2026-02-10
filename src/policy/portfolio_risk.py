"""Portfolio risk management — category exposure, correlation, concentration limits.

Prevents over-concentration in correlated markets, single categories,
or single events. Works alongside per-trade risk_limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.config import load_config
from src.observability.logger import get_logger

log = get_logger(__name__)


@dataclass
class PositionSnapshot:
    """Current position in a market."""
    market_id: str
    question: str
    category: str
    event_slug: str  # groups related markets
    side: str  # YES / NO
    size_usd: float
    entry_price: float
    current_price: float
    unrealised_pnl: float = 0.0

    @property
    def exposure_usd(self) -> float:
        return abs(self.size_usd)


@dataclass
class PortfolioRiskReport:
    """Summary of portfolio risk state."""
    total_exposure_usd: float = 0.0
    total_unrealised_pnl: float = 0.0
    num_positions: int = 0
    category_exposures: dict[str, float] = field(default_factory=dict)
    event_exposures: dict[str, float] = field(default_factory=dict)
    largest_position_pct: float = 0.0

    # Limit violations
    category_violations: list[str] = field(default_factory=list)
    event_violations: list[str] = field(default_factory=list)
    concentration_violation: bool = False
    correlated_position_count: int = 0
    is_healthy: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


class PortfolioRiskManager:
    """Evaluate portfolio-level risk constraints."""

    def __init__(self, bankroll: float, config: Any | None = None):
        self.bankroll = max(bankroll, 1.0)
        cfg = config or load_config()
        p = cfg.portfolio
        self.max_exposure_per_category = p.max_category_exposure_pct
        self.max_exposure_per_event = p.max_single_event_exposure_pct
        self.max_correlated_positions = p.max_correlated_positions
        self.correlation_threshold = p.correlation_similarity_threshold

    def assess(self, positions: list[PositionSnapshot]) -> PortfolioRiskReport:
        """Build a risk report from current positions."""
        report = PortfolioRiskReport()
        report.num_positions = len(positions)

        if not positions:
            return report

        report.total_exposure_usd = sum(p.exposure_usd for p in positions)
        report.total_unrealised_pnl = sum(p.unrealised_pnl for p in positions)

        # Category exposure
        for pos in positions:
            cat = pos.category or "uncategorised"
            report.category_exposures[cat] = (
                report.category_exposures.get(cat, 0.0) + pos.exposure_usd
            )

        # Event exposure (grouped markets)
        for pos in positions:
            evt = pos.event_slug or pos.market_id
            report.event_exposures[evt] = (
                report.event_exposures.get(evt, 0.0) + pos.exposure_usd
            )

        # Check category limits
        for cat, exp in report.category_exposures.items():
            pct = exp / self.bankroll
            if pct > self.max_exposure_per_category:
                report.category_violations.append(
                    f"{cat}: {pct:.1%} > {self.max_exposure_per_category:.0%} limit"
                )
                report.is_healthy = False

        # Check event limits
        for evt, exp in report.event_exposures.items():
            pct = exp / self.bankroll
            if pct > self.max_exposure_per_event:
                report.event_violations.append(
                    f"{evt}: {pct:.1%} > {self.max_exposure_per_event:.0%} limit"
                )
                report.is_healthy = False

        # Concentration check: largest position
        max_pos = max(p.exposure_usd for p in positions)
        report.largest_position_pct = max_pos / self.bankroll
        if report.largest_position_pct > 0.25:
            report.concentration_violation = True
            report.is_healthy = False

        # Simple correlation proxy: positions in same category count as correlated
        cat_counts = {}
        for pos in positions:
            cat = pos.category or "uncategorised"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        max_in_cat = max(cat_counts.values()) if cat_counts else 0
        report.correlated_position_count = max_in_cat
        if max_in_cat > self.max_correlated_positions:
            report.is_healthy = False

        log.info(
            "portfolio_risk.assessed",
            total_exposure=round(report.total_exposure_usd, 2),
            num_positions=report.num_positions,
            healthy=report.is_healthy,
            category_violations=len(report.category_violations),
        )
        return report

    def can_add_position(
        self,
        positions: list[PositionSnapshot],
        new_category: str,
        new_event: str,
        new_size_usd: float,
    ) -> tuple[bool, str]:
        """Check if adding a new position would violate portfolio limits."""
        # Category exposure check
        cat_exposure = sum(
            p.exposure_usd for p in positions if p.category == new_category
        )
        new_cat_pct = (cat_exposure + new_size_usd) / self.bankroll
        if new_cat_pct > self.max_exposure_per_category:
            return False, (
                f"Category '{new_category}' would reach {new_cat_pct:.1%} "
                f"(limit {self.max_exposure_per_category:.0%})"
            )

        # Event exposure check
        evt_exposure = sum(
            p.exposure_usd for p in positions if p.event_slug == new_event
        )
        new_evt_pct = (evt_exposure + new_size_usd) / self.bankroll
        if new_evt_pct > self.max_exposure_per_event:
            return False, (
                f"Event '{new_event}' would reach {new_evt_pct:.1%} "
                f"(limit {self.max_exposure_per_event:.0%})"
            )

        # Concentration check
        new_total = sum(p.exposure_usd for p in positions) + new_size_usd
        if new_size_usd / self.bankroll > 0.25:
            return False, f"Single position {new_size_usd:.0f} > 25% of bankroll"

        # Correlated positions
        same_cat = sum(1 for p in positions if p.category == new_category) + 1
        if same_cat > self.max_correlated_positions:
            return False, (
                f"Would create {same_cat} positions in '{new_category}' "
                f"(limit {self.max_correlated_positions})"
            )

        return True, "ok"
