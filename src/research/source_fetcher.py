"""Source fetcher — runs search queries and fetches page content.

Orchestrates:
  1. Executing search queries via the web_search connector
  2. Filtering out blocked domains
  3. De-duplicating results across queries
  4. Scoring sources by authority (primary > secondary > unknown)
  5. Optionally fetching full page content for top sources
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx

from src.config import ResearchConfig
from src.connectors.web_search import (
    SearchProvider,
    SearchResult,
    is_domain_blocked,
    score_domain_authority,
)
from src.observability.logger import get_logger
from src.research.query_builder import SearchQuery

log = get_logger(__name__)


@dataclass
class FetchedSource:
    """A source with full metadata and optionally fetched content."""
    title: str
    url: str
    snippet: str
    publisher: str = ""
    date: str = ""
    content: str = ""           # full page text (if fetched)
    authority_score: float = 0.0
    query_intent: str = ""
    extraction_method: str = "search"  # "search" | "api" | "html" | "rss"
    raw: dict[str, Any] = field(default_factory=dict)


class SourceFetcher:
    """Fetch and rank sources for a set of search queries."""

    def __init__(self, provider: SearchProvider, config: ResearchConfig):
        self._provider = provider
        self._config = config
        self._http = httpx.AsyncClient(
            timeout=config.source_timeout_secs,
            follow_redirects=True,
            headers={"User-Agent": "PolymarketBot/0.1 (research)"},
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def fetch_sources(
        self,
        queries: list[SearchQuery],
        market_type: str = "UNKNOWN",
        max_sources: int | None = None,
    ) -> list[FetchedSource]:
        """Run all queries, filter, de-dup, rank, and return top sources."""
        max_sources = max_sources or self._config.max_sources
        seen_urls: set[str] = set()
        all_sources: list[FetchedSource] = []

        # Resolve primary domains for this market type
        primary = self._config.primary_domains.get(market_type, [])
        secondary = self._config.secondary_domains
        blocked = self._config.blocked_domains

        # Run queries concurrently
        tasks = [self._run_query(q) for q in queries]
        results_per_query = await asyncio.gather(*tasks, return_exceptions=True)

        for query, results in zip(queries, results_per_query):
            if isinstance(results, BaseException):
                log.warning(
                    "source_fetcher.query_failed",
                    query=query.text[:80],
                    error=str(results),
                )
                continue
            for sr in results:
                # Block bad domains
                if is_domain_blocked(sr.url, blocked):
                    log.debug("source_fetcher.blocked", url=sr.url)
                    continue

                canonical = _canonical_url(sr.url)
                if canonical in seen_urls:
                    continue
                seen_urls.add(canonical)

                all_sources.append(
                    FetchedSource(
                        title=sr.title,
                        url=sr.url,
                        snippet=sr.snippet,
                        publisher=sr.source or _extract_domain(sr.url),
                        date=sr.date,
                        authority_score=score_domain_authority(
                            sr.url, primary, secondary
                        ),
                        query_intent=query.intent,
                        raw=sr.raw,
                    )
                )

        # Sort: authority desc, then intent priority (primary > news > contrarian)
        intent_order = {"primary": 0, "statistics": 1, "news": 2, "confirmation": 3, "contrarian": 4}
        all_sources.sort(
            key=lambda s: (-s.authority_score, intent_order.get(s.query_intent, 5)),
        )
        top = all_sources[:max_sources]

        log.info(
            "source_fetcher.fetched",
            total_raw=len(all_sources),
            returned=len(top),
            blocked_count=sum(
                1 for _ in []  # logged above individually
            ),
        )
        return top

    async def _run_query(self, query: SearchQuery) -> list[SearchResult]:
        return await self._provider.search(query.text, num_results=8)

    async def fetch_page_content(self, url: str) -> str:
        """Fetch and extract text content from a URL."""
        try:
            resp = await self._http.get(url)
            resp.raise_for_status()
            text = resp.text
            # Basic tag stripping (production would use readability)
            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:10000]
        except Exception as e:
            log.warning("source_fetcher.page_fetch_failed", url=url, error=str(e))
            return ""


def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def _canonical_url(url: str) -> str:
    """Normalize URL for de-duplication."""
    parsed = urlparse(url)
    return f"{parsed.netloc}{parsed.path}".rstrip("/").lower()
