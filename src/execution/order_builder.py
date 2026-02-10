"""Order builder — constructs orders from position sizing results.

Creates order specifications that can be routed to the CLOB.
Supports limit and market orders with slippage protection.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from src.config import ExecutionConfig
from src.policy.position_sizer import PositionSize
from src.observability.logger import get_logger

log = get_logger(__name__)


@dataclass
class OrderSpec:
    """Specification for an order to be placed."""
    order_id: str
    market_id: str
    token_id: str
    side: str           # "BUY" | "SELL"
    order_type: str     # "limit" | "market"
    price: float        # limit price (or 0 for market)
    size: float         # token quantity
    stake_usd: float    # USD value
    ttl_secs: int       # time-to-live for limit orders
    dry_run: bool       # if True, order is simulated only
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "market_id": self.market_id,
            "token_id": self.token_id,
            "side": self.side,
            "order_type": self.order_type,
            "price": self.price,
            "size": self.size,
            "stake_usd": self.stake_usd,
            "ttl_secs": self.ttl_secs,
            "dry_run": self.dry_run,
        }


def build_order(
    market_id: str,
    token_id: str,
    position: PositionSize,
    implied_price: float,
    config: ExecutionConfig,
) -> OrderSpec:
    """Build an order specification from a position sizing result."""
    # Determine side
    side = "BUY"  # We always buy tokens (YES or NO)

    # Limit price with slippage tolerance
    if config.default_order_type == "limit":
        # Add slippage tolerance to price for buys
        price = round(implied_price * (1 + config.slippage_tolerance), 4)
    else:
        price = 0.0  # Market order

    order = OrderSpec(
        order_id=str(uuid.uuid4()),
        market_id=market_id,
        token_id=token_id,
        side=side,
        order_type=config.default_order_type,
        price=price,
        size=position.token_quantity,
        stake_usd=position.stake_usd,
        ttl_secs=config.limit_order_ttl_secs,
        dry_run=config.dry_run,
        metadata={
            "direction": position.direction,
            "kelly_fraction": position.kelly_fraction_used,
            "capped_by": position.capped_by,
        },
    )

    log.info(
        "order_builder.built",
        order_id=order.order_id[:8],
        market_id=market_id,
        side=side,
        type=order.order_type,
        price=order.price,
        size=order.size,
        dry_run=order.dry_run,
    )
    return order
