"""Query builder — constructs targeted web search queries from market data.

Implements the SOURCE-FIRST, WHITELISTED SEARCH PIPELINE:
  1. Site-restricted queries to primary authoritative sources
  2. Metric-specific and date-scoped queries
  3. Confirmation queries to secondary outlets
  4. Contrarian queries to surface opposing evidence
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.connectors.polymarket_gamma import GammaMarket
from src.observability.logger import get_logger

log = get_logger(__name__)

# ── Primary source sites by market type ──────────────────────────────
_SITE_RESTRICTED: dict[str, list[str]] = {
    "MACRO": [
        "site:bls.gov",
        "site:bea.gov",
        "site:federalreserve.gov",
        "site:fred.stlouisfed.org",
        "site:treasury.gov",
    ],
    "ELECTION": [
        "site:fec.gov",
        "site:ballotpedia.org",
    ],
    "CORPORATE": [
        "site:sec.gov",
    ],
    "WEATHER": [
        "site:noaa.gov",
        "site:nhc.noaa.gov",
        "site:weather.gov",
    ],
    "SPORTS": [],
}


@dataclass
class SearchQuery:
    """A search query with intent metadata."""
    text: str
    intent: str  # "primary" | "news" | "statistics" | "contrarian" | "confirmation"
    priority: int = 1  # 1 = highest


def build_queries(
    market: GammaMarket,
    max_queries: int = 8,
) -> list[SearchQuery]:
    """Generate search queries for a market.

    Strategy (in order):
      1. Site-restricted queries to official sources
      2. Exact metric / event name search
      3. Date-scoped news queries
      4. Contrarian queries
    """
    question = market.question.strip().rstrip("?")
    # Strip common leading words for a cleaner core query
    core = re.sub(r"^(Will|Is|Does|Has|Are|Do|Can|Should)\s+", "", question, flags=re.I)

    queries: list[SearchQuery] = []

    # ── 1. Site-restricted primary source queries ────────────────────
    site_restrictions = _SITE_RESTRICTED.get(market.market_type, [])
    for site in site_restrictions[:3]:  # Max 3 site-restricted queries
        queries.append(SearchQuery(
            text=f"{site} {core}",
            intent="primary",
            priority=1,
        ))

    # ── 2. Exact metric search ──────────────────────────────────────
    queries.append(SearchQuery(
        text=f'"{core}" official data release 2026',
        intent="statistics",
        priority=1,
    ))

    # ── 3. Recent news from major outlets ────────────────────────────
    queries.append(SearchQuery(
        text=f"{core} latest news 2026",
        intent="news",
        priority=2,
    ))

    # ── 4. Probability / forecast context ────────────────────────────
    queries.append(SearchQuery(
        text=f"{core} probability forecast prediction analysis",
        intent="confirmation",
        priority=2,
    ))

    # ── 5. Contrarian / opposing view ────────────────────────────────
    queries.append(SearchQuery(
        text=f"{core} unlikely reasons against criticism",
        intent="contrarian",
        priority=3,
    ))

    # ── 6. Category-specific refinement ──────────────────────────────
    if market.category and market.category.lower() not in core.lower():
        queries.append(SearchQuery(
            text=f"{market.category} {core}",
            intent="confirmation",
            priority=3,
        ))

    # Sort by priority and trim
    queries.sort(key=lambda q: q.priority)
    result = queries[:max_queries]

    log.info(
        "query_builder.built",
        market_id=market.id,
        market_type=market.market_type,
        num_queries=len(result),
        intents=[q.intent for q in result],
    )
    return result
