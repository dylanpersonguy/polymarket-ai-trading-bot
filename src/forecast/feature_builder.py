"""Feature builder — construct features for the forecasting model.

Combines:
  - Market metadata (volume, liquidity, time to expiry, type)
  - Orderbook features (spread, depth, imbalance)
  - Evidence features (quality, num sources, contradictions)
  - Price history features (momentum, volatility)
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from src.connectors.polymarket_clob import OrderBook, TradeRecord
from src.connectors.polymarket_gamma import GammaMarket
from src.research.evidence_extractor import EvidencePackage
from src.observability.logger import get_logger

log = get_logger(__name__)


@dataclass
class MarketFeatures:
    """Feature vector for forecasting."""
    market_id: str = ""
    question: str = ""
    market_type: str = "UNKNOWN"

    # Market metadata
    volume_usd: float = 0.0
    liquidity_usd: float = 0.0
    days_to_expiry: float = 0.0
    category: str = ""
    has_clear_resolution: bool = False

    # Price / orderbook
    implied_probability: float = 0.5
    spread: float = 0.0
    spread_pct: float = 0.0
    bid_depth_5: float = 0.0
    ask_depth_5: float = 0.0
    book_imbalance: float = 0.0  # (bid - ask) / (bid + ask)

    # Price history
    price_24h_ago: float = 0.0
    price_momentum: float = 0.0
    price_volatility: float = 0.0
    num_recent_trades: int = 0

    # Evidence
    evidence_quality: float = 0.0
    num_sources: int = 0
    num_contradictions: int = 0
    has_numeric_evidence: bool = False
    num_evidence_bullets: int = 0

    # Derived
    evidence_summary: str = ""
    top_bullets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


def build_features(
    market: GammaMarket,
    orderbook: OrderBook | None = None,
    trades: list[TradeRecord] | None = None,
    evidence: EvidencePackage | None = None,
) -> MarketFeatures:
    """Construct a feature vector from all available data."""
    features = MarketFeatures(
        market_id=market.id,
        question=market.question,
        market_type=market.market_type,
        volume_usd=market.volume,
        liquidity_usd=market.liquidity,
        category=market.category,
        implied_probability=market.best_bid,
        has_clear_resolution=market.has_clear_resolution,
    )

    # Days to expiry
    if market.end_date:
        now = dt.datetime.now(dt.timezone.utc)
        delta = market.end_date - now
        features.days_to_expiry = max(delta.total_seconds() / 86400, 0)

    # Orderbook features
    if orderbook:
        features.spread = orderbook.spread
        features.spread_pct = orderbook.spread_pct
        features.implied_probability = orderbook.mid
        features.bid_depth_5 = orderbook.bid_depth(5)
        features.ask_depth_5 = orderbook.ask_depth(5)
        total = features.bid_depth_5 + features.ask_depth_5
        if total > 0:
            features.book_imbalance = (features.bid_depth_5 - features.ask_depth_5) / total

    # Trade history features
    if trades:
        features.num_recent_trades = len(trades)
        prices = [t.price for t in trades if t.price > 0]
        if prices:
            features.price_24h_ago = prices[-1] if len(prices) > 1 else prices[0]
            features.price_momentum = prices[0] - features.price_24h_ago
            if len(prices) >= 2:
                mean_p = sum(prices) / len(prices)
                variance = sum((p - mean_p) ** 2 for p in prices) / len(prices)
                features.price_volatility = variance ** 0.5

    # Evidence features
    if evidence:
        features.evidence_quality = evidence.quality_score
        features.num_sources = evidence.num_sources
        features.num_contradictions = len(evidence.contradictions)
        features.num_evidence_bullets = len(evidence.bullets)
        features.has_numeric_evidence = any(b.is_numeric for b in evidence.bullets)
        features.evidence_summary = evidence.summary
        features.top_bullets = [
            f"{b.text} [{b.citation.publisher}, {b.citation.date}]"
            for b in sorted(evidence.bullets, key=lambda x: x.relevance, reverse=True)[:5]
        ]

    log.info(
        "feature_builder.built",
        market_id=features.market_id,
        implied_prob=round(features.implied_probability, 3),
        evidence_quality=round(features.evidence_quality, 2),
    )
    return features
