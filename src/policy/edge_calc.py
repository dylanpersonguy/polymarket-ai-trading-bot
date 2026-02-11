"""Edge calculator — computes trading edge from forecast vs market price.

Edge = model_probability - implied_probability

Features:
  - Directional edge (buy YES or buy NO)
  - Transaction cost deduction (fees + gas)
  - Multi-outcome market support
  - Expected value per dollar (net of costs)
  - Confidence-weighted edge
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

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
    # Cost-adjusted fields
    transaction_cost_pct: float = 0.0
    net_edge: float = 0.0        # raw_edge - transaction_cost
    net_ev_per_dollar: float = 0.0
    break_even_probability: float = 0.0

    @property
    def abs_edge(self) -> float:
        return abs(self.raw_edge)

    @property
    def abs_net_edge(self) -> float:
        return abs(self.net_edge)


@dataclass
class MultiOutcomeEdge:
    """Edge calculation for multi-outcome markets."""
    market_id: str
    outcomes: List[str] = field(default_factory=list)
    implied_probs: List[float] = field(default_factory=list)
    model_probs: List[float] = field(default_factory=list)
    edges: List[float] = field(default_factory=list)
    best_outcome_index: int = -1
    best_edge: float = 0.0
    best_direction: str = ""
    overround: float = 0.0  # sum of implied probs - 1.0 (vig)


def calculate_edge(
    implied_prob: float,
    model_prob: float,
    transaction_fee_pct: float = 0.0,
    gas_cost_usd: float = 0.0,
    stake_usd: float = 100.0,
) -> EdgeResult:
    """Calculate trading edge with transaction cost awareness.

    If model_prob > implied_prob → edge on YES (buy YES token).
    If model_prob < implied_prob → edge on NO (buy NO token).

    Transaction costs are deducted from the edge to get net_edge.
    """
    raw_edge = model_prob - implied_prob

    # Single-leg cost — we hold to resolution, no exit trade
    total_cost_pct = transaction_fee_pct  # entry fee only (hold-to-resolution)
    if stake_usd > 0:
        total_cost_pct += gas_cost_usd / stake_usd  # gas as % of stake

    if raw_edge >= 0:
        direction = "BUY_YES"
        cost = implied_prob if implied_prob > 0 else 0.001
        ev = (model_prob * 1.0 - cost) / cost
        # Break-even: what model_prob needs to be to overcome costs
        break_even = cost * (1 + total_cost_pct)
    else:
        direction = "BUY_NO"
        cost = (1 - implied_prob) if (1 - implied_prob) > 0 else 0.001
        no_model = 1 - model_prob
        ev = (no_model * 1.0 - cost) / cost
        break_even = 1.0 - cost * (1 + total_cost_pct)

    # Net edge after costs
    net_edge = abs(raw_edge) - total_cost_pct
    net_ev = ev - total_cost_pct

    edge_pct = raw_edge / implied_prob if implied_prob > 0 else 0.0

    result = EdgeResult(
        implied_probability=implied_prob,
        model_probability=model_prob,
        raw_edge=raw_edge,
        edge_pct=edge_pct,
        direction=direction,
        expected_value_per_dollar=ev,
        is_positive=net_edge > 0,
        transaction_cost_pct=total_cost_pct,
        net_edge=net_edge if raw_edge >= 0 else -net_edge,
        net_ev_per_dollar=net_ev,
        break_even_probability=break_even,
    )

    log.info(
        "edge_calc.result",
        implied=round(implied_prob, 3),
        model=round(model_prob, 3),
        raw_edge=round(raw_edge, 3),
        net_edge=round(net_edge, 3),
        cost_pct=round(total_cost_pct, 4),
        direction=direction,
        ev_per_dollar=round(ev, 3),
    )
    return result


def calculate_multi_outcome_edge(
    market_id: str,
    outcomes: list[str],
    implied_probs: list[float],
    model_probs: list[float],
    transaction_fee_pct: float = 0.0,
) -> MultiOutcomeEdge:
    """Calculate edge across all outcomes in a multi-outcome market.

    Identifies the best outcome to bet on and detects overround (vig).
    """
    if len(outcomes) != len(implied_probs) or len(outcomes) != len(model_probs):
        raise ValueError("outcomes, implied_probs, and model_probs must have same length")

    overround = sum(implied_probs) - 1.0

    # Adjust implied probs for overround to get true implied
    adj_implied = implied_probs
    if overround > 0.01:
        total = sum(implied_probs)
        adj_implied = [p / total for p in implied_probs]

    edges = [m - i for m, i in zip(model_probs, adj_implied)]

    # Find best edge (considering costs)
    best_idx = -1
    best_net_edge = -float("inf")
    for i, edge in enumerate(edges):
        net = abs(edge) - transaction_fee_pct * 2
        if net > best_net_edge:
            best_net_edge = net
            best_idx = i

    best_direction = ""
    if best_idx >= 0:
        if edges[best_idx] > 0:
            best_direction = f"BUY_{outcomes[best_idx].upper()}"
        else:
            best_direction = f"SELL_{outcomes[best_idx].upper()}"

    result = MultiOutcomeEdge(
        market_id=market_id,
        outcomes=outcomes,
        implied_probs=implied_probs,
        model_probs=model_probs,
        edges=edges,
        best_outcome_index=best_idx,
        best_edge=edges[best_idx] if best_idx >= 0 else 0.0,
        best_direction=best_direction,
        overround=overround,
    )

    log.info(
        "edge_calc.multi_outcome",
        market_id=market_id,
        num_outcomes=len(outcomes),
        best_outcome=outcomes[best_idx] if best_idx >= 0 else "none",
        best_edge=round(result.best_edge, 3),
        overround=round(overround, 3),
    )
    return result
