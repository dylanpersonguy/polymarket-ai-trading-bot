"""Edge calculator — computes trading edge from forecast vs market price.

Edge = model_probability - implied_probability

Also computes:
  - Directional edge (buy YES or buy NO)
  - Edge as a percentage of implied probability
  - Expected value per dollar
"""

from __future__ import annotations

from dataclasses import dataclass

from src.observability.logger import get_logger

log = get_logger(__name__)


@dataclass
class EdgeResult:
    """Result of edge calculation."""
    implied_probability: float
    model_probability: float
    raw_edge: float              # model_prob - implied_prob
    edge_pct: float              # raw_edge / implied_prob
    direction: str               # "BUY_YES" | "BUY_NO"
    expected_value_per_dollar: float
    is_positive: bool

    @property
    def abs_edge(self) -> float:
        return abs(self.raw_edge)


def calculate_edge(
    implied_prob: float,
    model_prob: float,
) -> EdgeResult:
    """Calculate trading edge.

    If model_prob > implied_prob → edge on YES (buy YES token).
    If model_prob < implied_prob → edge on NO (buy NO token, i.e. sell YES).
    """
    raw_edge = model_prob - implied_prob

    if raw_edge >= 0:
        direction = "BUY_YES"
        # EV per dollar: (model_prob * payout - cost) / cost
        # For YES token: cost = implied_prob, payout = 1.0
        cost = implied_prob if implied_prob > 0 else 0.001
        ev = (model_prob * 1.0 - cost) / cost
    else:
        direction = "BUY_NO"
        # For NO token: cost = 1 - implied_prob, payout = 1.0
        cost = (1 - implied_prob) if (1 - implied_prob) > 0 else 0.001
        no_model = 1 - model_prob
        ev = (no_model * 1.0 - cost) / cost

    edge_pct = raw_edge / implied_prob if implied_prob > 0 else 0.0

    result = EdgeResult(
        implied_probability=implied_prob,
        model_probability=model_prob,
        raw_edge=raw_edge,
        edge_pct=edge_pct,
        direction=direction,
        expected_value_per_dollar=ev,
        is_positive=abs(raw_edge) > 0,
    )

    log.info(
        "edge_calc.result",
        implied=round(implied_prob, 3),
        model=round(model_prob, 3),
        edge=round(raw_edge, 3),
        direction=direction,
        ev_per_dollar=round(ev, 3),
    )
    return result
