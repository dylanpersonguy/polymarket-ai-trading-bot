"""Pre-research market filter — reduces SerpAPI usage by ~90%.

Scores markets 0-100 based on structural quality signals BEFORE any web
searches.  Markets below the threshold are skipped entirely, saving
expensive API calls on low-value or un-researchable markets.

Stages:
  1. Hard rejection   – instant skip (no token IDs, blocked types, etc.)
  2. Soft scoring      – 0–100 composite score
  3. Research cooldown – skip markets researched within the last N minutes
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.engine.market_classifier import (
    MarketClassification,
    classify_market,
)
from src.observability.logger import get_logger

log = get_logger(__name__)


# ── Blocked keywords — markets matching these are almost never tradeable ──

BLOCKED_KEYWORDS: list[str] = [
    "meme", "tiktok", "viral", "streamer", "youtuber", "twitch",
    "follower count", "subscriber", "like count", "retweet",
    "instagram", "snapchat", "onlyfans", "celebrity dating",
    "baby name", "pet", "hot dog", "eating contest",
]


# ── Preferred keywords — boost score for high-signal markets ──

PREFERRED_KEYWORDS: list[str] = [
    "federal reserve", "fomc", "cpi", "inflation", "gdp",
    "unemployment", "interest rate", "rate cut", "rate hike",
    "nonfarm payroll", "pce", "treasury", "yield curve",
    "sec filing", "ipo", "merger", "acquisition", "fda",
    "election", "primary", "senate", "congress", "president",
    "governor", "ballot", "supreme court", "indictment",
    "antitrust", "earnings",
]


# ── Data structures ─────────────────────────────────────────────────


@dataclass
class FilterResult:
    """Result of filtering a single market."""
    market_id: str
    question: str
    score: int  # 0-100
    passed: bool
    rejection_reason: str = ""
    breakdown: Dict[str, int] = field(default_factory=dict)
    classification: Optional[MarketClassification] = None


@dataclass
class FilterStats:
    """Aggregate stats from filtering a batch of markets."""
    total_input: int = 0
    hard_rejected: int = 0
    soft_rejected: int = 0
    cooldown_skipped: int = 0
    passed: int = 0
    avg_score: float = 0.0
    rejection_reasons: Dict[str, int] = field(default_factory=dict)
    top_passed: List[Dict[str, Any]] = field(default_factory=list)


# ── Research cooldown cache ──────────────────────────────────────────


class ResearchCache:
    """In-memory cache tracking when each market was last researched."""

    def __init__(self, cooldown_minutes: int = 30):
        self._cooldown_secs = cooldown_minutes * 60
        self._cache: Dict[str, float] = {}  # market_id → timestamp

    @property
    def cooldown_minutes(self) -> int:
        return self._cooldown_secs // 60

    @cooldown_minutes.setter
    def cooldown_minutes(self, value: int) -> None:
        self._cooldown_secs = value * 60

    def was_recently_researched(self, market_id: str) -> bool:
        ts = self._cache.get(market_id)
        if ts is None:
            return False
        return (time.time() - ts) < self._cooldown_secs

    def mark_researched(self, market_id: str) -> None:
        self._cache[market_id] = time.time()

    def clear_stale(self) -> int:
        """Remove entries older than 2× cooldown.  Returns count removed."""
        cutoff = time.time() - (self._cooldown_secs * 2)
        stale = [k for k, v in self._cache.items() if v < cutoff]
        for k in stale:
            del self._cache[k]
        return len(stale)

    def size(self) -> int:
        return len(self._cache)


# ── Hard rejection ───────────────────────────────────────────────────

_BLOCKED_TYPES: set[str] = {"UNKNOWN"}


def _hard_reject(market: Any, blocked_types: set[str] | None = None,
                 classification: MarketClassification | None = None) -> Optional[str]:
    """Return rejection reason string, or None if the market passes."""
    # No token IDs → can't trade
    if not getattr(market, "tokens", None):
        return "no_tokens"

    # Market already closed
    if getattr(market, "closed", False):
        return "market_closed"

    # Market not active
    if not getattr(market, "active", True):
        return "market_inactive"

    # Blocked market type (legacy)
    types = blocked_types if blocked_types is not None else _BLOCKED_TYPES
    if getattr(market, "market_type", "") in types:
        return f"blocked_type:{market.market_type}"

    # Classifier-based rejection: not worth researching
    if classification and not classification.worth_researching:
        return f"not_researchable:{classification.category}/{classification.subcategory}"

    # Blocked keywords in question
    q = getattr(market, "question", "").lower()
    for kw in BLOCKED_KEYWORDS:
        if kw in q:
            return f"blocked_keyword:{kw}"

    return None


# ── Soft scoring ─────────────────────────────────────────────────────

def _score_market(market: Any, preferred_types: list[str] | None = None,
                  classification: MarketClassification | None = None) -> tuple[int, Dict[str, int]]:
    """Score a market 0–100.  Returns (total, breakdown)."""
    breakdown: Dict[str, int] = {}
    base = 50  # start at 50

    # ── Liquidity ────────────────────────────────────────────────────
    liq = getattr(market, "liquidity", 0.0)
    if liq >= 50_000:
        breakdown["liquidity"] = 15
    elif liq >= 10_000:
        breakdown["liquidity"] = 8
    elif liq >= 1_000:
        breakdown["liquidity"] = 0
    else:
        breakdown["liquidity"] = -30

    # ── Volume ───────────────────────────────────────────────────────
    vol = getattr(market, "volume", 0.0)
    if vol >= 100_000:
        breakdown["volume"] = 10
    elif vol >= 20_000:
        breakdown["volume"] = 5
    elif vol >= 5_000:
        breakdown["volume"] = 0
    else:
        breakdown["volume"] = -15

    # ── Implied probability sweet spot ───────────────────────────────
    prob = getattr(market, "best_bid", 0.5)
    if prob < 0.03 or prob > 0.97:
        breakdown["probability"] = -25
    elif 0.15 <= prob <= 0.85:
        breakdown["probability"] = 10
    elif 0.05 <= prob <= 0.95:
        breakdown["probability"] = 3
    else:
        breakdown["probability"] = -10

    # ── Time to expiry ───────────────────────────────────────────────
    import datetime as dt
    end_date = getattr(market, "end_date", None)
    if end_date:
        try:
            now = dt.datetime.now(dt.timezone.utc)
            if isinstance(end_date, str):
                end_date = dt.datetime.fromisoformat(end_date)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=dt.timezone.utc)
            days = (end_date - now).total_seconds() / 86400
        except Exception:
            days = 30.0
    else:
        days = 30.0

    if days < 2:
        breakdown["expiry"] = -20
    elif 7 <= days <= 60:
        breakdown["expiry"] = 10
    elif days > 180:
        breakdown["expiry"] = -10
    else:
        breakdown["expiry"] = 0

    # ── Market type ──────────────────────────────────────────────────
    mtype = getattr(market, "market_type", "")
    prefs = preferred_types or ["MACRO", "ELECTION", "CORPORATE"]
    if mtype in prefs:
        breakdown["market_type"] = 15
    elif mtype == "SPORTS":
        breakdown["market_type"] = -5
    else:
        breakdown["market_type"] = 0

    # ── Resolution source ────────────────────────────────────────────
    has_res = getattr(market, "has_clear_resolution", False)
    breakdown["resolution"] = 8 if has_res else 0

    # ── Spread ───────────────────────────────────────────────────────
    spread = getattr(market, "spread", 1.0)
    if spread < 0.03:
        breakdown["spread"] = 8
    elif spread < 0.06:
        breakdown["spread"] = 4
    elif spread > 0.15:
        breakdown["spread"] = -8
    else:
        breakdown["spread"] = 0

    # ── Preferred keywords ───────────────────────────────────────────
    q = getattr(market, "question", "").lower()
    desc = getattr(market, "description", "").lower()
    text = f"{q} {desc}"
    kw_hits = sum(1 for kw in PREFERRED_KEYWORDS if kw in text)
    kw_bonus = min(kw_hits * 5, 20)  # cap at +20
    breakdown["keywords"] = kw_bonus

    # ── Classifier researchability bonus ─────────────────────────────
    if classification:
        # Map researchability 0-100 → bonus -15 to +15
        r = classification.researchability
        if r >= 80:
            breakdown["researchability"] = 15
        elif r >= 60:
            breakdown["researchability"] = 8
        elif r >= 40:
            breakdown["researchability"] = 0
        elif r >= 25:
            breakdown["researchability"] = -8
        else:
            breakdown["researchability"] = -15

        # Bonus for scheduled events (more predictable)
        if "scheduled_event" in classification.tags:
            breakdown["scheduled_event"] = 8

    total = max(0, min(100, base + sum(breakdown.values())))
    return total, breakdown


# ── Public API ───────────────────────────────────────────────────────

def score_market(
    market: Any,
    blocked_types: set[str] | None = None,
    preferred_types: list[str] | None = None,
) -> FilterResult:
    """Score a single market.  Hard rejections get score=0."""
    market_id = getattr(market, "id", "?")
    question = getattr(market, "question", "?")

    # Run classifier first
    description = getattr(market, "description", "")
    classification = classify_market(question, description)

    rejection = _hard_reject(market, blocked_types=blocked_types,
                             classification=classification)
    if rejection:
        return FilterResult(
            market_id=market_id, question=question,
            score=0, passed=False, rejection_reason=rejection,
            classification=classification,
        )

    score, breakdown = _score_market(market, preferred_types=preferred_types,
                                     classification=classification)
    return FilterResult(
        market_id=market_id, question=question,
        score=score, passed=True, breakdown=breakdown,
        classification=classification,
    )


def filter_markets(
    markets: list[Any],
    min_score: int = 45,
    max_pass: int = 5,
    research_cache: ResearchCache | None = None,
    blocked_types: set[str] | None = None,
    preferred_types: list[str] | None = None,
) -> tuple[list[Any], FilterStats]:
    """Filter and rank markets, returning only the best candidates.

    Returns:
        (passed_markets, stats)
    """
    stats = FilterStats(total_input=len(markets))
    scored: list[tuple[int, Any, FilterResult]] = []

    for m in markets:
        fr = score_market(m, blocked_types=blocked_types, preferred_types=preferred_types)

        if not fr.passed:
            stats.hard_rejected += 1
            stats.rejection_reasons[fr.rejection_reason] = (
                stats.rejection_reasons.get(fr.rejection_reason, 0) + 1
            )
            continue

        # Research cooldown check
        if research_cache and research_cache.was_recently_researched(fr.market_id):
            stats.cooldown_skipped += 1
            stats.rejection_reasons["cooldown"] = (
                stats.rejection_reasons.get("cooldown", 0) + 1
            )
            continue

        if fr.score < min_score:
            stats.soft_rejected += 1
            stats.rejection_reasons["low_score"] = (
                stats.rejection_reasons.get("low_score", 0) + 1
            )
            continue

        scored.append((fr.score, m, fr))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_pass]

    stats.passed = len(top)
    if scored:
        stats.avg_score = sum(s for s, _, _ in scored) / len(scored)
    stats.top_passed = [
        {"market_id": fr.market_id, "question": fr.question[:80],
         "score": fr.score, "breakdown": fr.breakdown}
        for _, _, fr in top
    ]

    log.info(
        "market_filter.result",
        total=stats.total_input,
        hard_rejected=stats.hard_rejected,
        soft_rejected=stats.soft_rejected,
        cooldown=stats.cooldown_skipped,
        passed=stats.passed,
        avg_score=round(stats.avg_score, 1),
    )

    return [m for _, m, _ in top], stats
