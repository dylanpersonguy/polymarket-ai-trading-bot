"""Position sizer — determines optimal trade size.

Uses fractional Kelly criterion with guardrails:
  - Full Kelly would be: f* = edge / odds
  - We use kelly_fraction (default 0.25) of full Kelly
  - Capped by max_stake_per_market and max_bankroll_fraction
"""

from __future__ import annotations

from dataclasses import dataclass

from src.config import RiskConfig
from src.policy.edge_calc import EdgeResult
from src.observability.logger import get_logger

log = get_logger(__name__)


@dataclass
class PositionSize:
    """Computed position size."""
    stake_usd: float
    kelly_fraction_used: float
    full_kelly_stake: float
    capped_by: str  # "kelly" | "max_stake" | "max_bankroll"
    direction: str  # "BUY_YES" | "BUY_NO"
    token_quantity: float  # approximate tokens at implied price


def calculate_position_size(
    edge: EdgeResult,
    risk_config: RiskConfig,
    confidence_level: str = "LOW",
) -> PositionSize:
    """Calculate position size using fractional Kelly criterion.

    Kelly formula for binary outcome:
      f* = (p * b - q) / b
    where:
      p = model probability of winning
      b = odds (payout / cost - 1)
      q = 1 - p
    """
    if edge.direction == "BUY_YES":
        p = edge.model_probability
        cost = edge.implied_probability
    else:
        p = 1 - edge.model_probability
        cost = 1 - edge.implied_probability

    cost = max(cost, 0.01)
    b = (1.0 / cost) - 1.0  # odds
    q = 1 - p

    # Full Kelly
    if b > 0:
        full_kelly_frac = (p * b - q) / b
    else:
        full_kelly_frac = 0.0

    full_kelly_frac = max(0.0, full_kelly_frac)

    # Fractional Kelly
    kelly_mult = risk_config.kelly_fraction
    # Scale down further for LOW confidence
    if confidence_level == "LOW":
        kelly_mult *= 0.5
    elif confidence_level == "MEDIUM":
        kelly_mult *= 0.75

    adj_kelly = full_kelly_frac * kelly_mult
    full_kelly_stake = adj_kelly * risk_config.bankroll

    # Apply caps
    max_stake = risk_config.max_stake_per_market
    max_bankroll = risk_config.max_bankroll_fraction * risk_config.bankroll

    stake = min(full_kelly_stake, max_stake, max_bankroll)
    stake = max(0.0, stake)

    # Determine what capped it
    if stake == full_kelly_stake:
        capped_by = "kelly"
    elif stake == max_stake:
        capped_by = "max_stake"
    else:
        capped_by = "max_bankroll"

    # Approximate token quantity
    token_qty = stake / cost if cost > 0 else 0.0

    result = PositionSize(
        stake_usd=round(stake, 2),
        kelly_fraction_used=round(adj_kelly, 4),
        full_kelly_stake=round(full_kelly_stake, 2),
        capped_by=capped_by,
        direction=edge.direction,
        token_quantity=round(token_qty, 2),
    )

    log.info(
        "position_sizer.sized",
        stake=result.stake_usd,
        kelly_frac=result.kelly_fraction_used,
        full_kelly=result.full_kelly_stake,
        capped_by=result.capped_by,
        direction=result.direction,
    )
    return result
