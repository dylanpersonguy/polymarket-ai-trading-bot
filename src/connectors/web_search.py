"""Web search connector with pluggable backends.

Supported providers:
  - serpapi  (default, requires SERPAPI_KEY)
  - bing     (requires BING_API_KEY)
  - tavily   (requires TAVILY_API_KEY)

Includes domain whitelisting/blocking per the research agent spec.
"""

from __future__ import annotations

import abc
import os
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from src.observability.logger import get_logger

log = get_logger(__name__)


# ── Data Models ──────────────────────────────────────────────────────

@dataclass
class SearchResult:
    """A single web search result."""
    title: str
    url: str
    snippet: str
    source: str = ""         # publisher / domain
    date: str = ""            # publication date if available
    position: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


# ── Domain filtering ────────────────────────────────────────────────

def is_domain_blocked(url: str, blocked: list[str]) -> bool:
    """Check if a URL's domain is on the blocked list."""
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return False
    return any(b.lower() in domain for b in blocked)


def score_domain_authority(url: str, primary: list[str], secondary: list[str]) -> float:
    """Score a URL's domain authority (0-1)."""
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return 0.3
    for p in primary:
        if p.lower() in domain:
            return 1.0
    for s in secondary:
        if s.lower() in domain:
            return 0.7
    if domain.endswith(".gov"):
        return 0.95
    if domain.endswith(".edu"):
        return 0.8
    return 0.4


# ── Abstract Provider ────────────────────────────────────────────────

class SearchProvider(abc.ABC):
    """Base class for web search providers."""

    @abc.abstractmethod
    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        ...

    async def close(self) -> None:
        pass


# ── SerpAPI Provider ─────────────────────────────────────────────────

class SerpAPIProvider(SearchProvider):
    """Google search via SerpAPI."""

    def __init__(self, api_key: str | None = None):
        self._key = api_key or os.environ.get("SERPAPI_KEY", "")
        if not self._key:
            log.warning("serpapi.no_key", msg="SERPAPI_KEY not set; searches will fail")
        self._client = httpx.AsyncClient(timeout=20.0)

    async def close(self) -> None:
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        resp = await self._client.get(
            "https://serpapi.com/search.json",
            params={
                "q": query,
                "api_key": self._key,
                "num": num_results,
                "engine": "google",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        results: list[SearchResult] = []
        for i, item in enumerate(data.get("organic_results", [])):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=item.get("source", item.get("displayed_link", "")),
                    date=item.get("date", ""),
                    position=i + 1,
                    raw=item,
                )
            )
        log.info("serpapi.search", query=query[:80], results=len(results))
        return results


# ── Bing Provider ────────────────────────────────────────────────────

class BingProvider(SearchProvider):
    """Bing Web Search API v7."""

    def __init__(self, api_key: str | None = None):
        self._key = api_key or os.environ.get("BING_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=20.0)

    async def close(self) -> None:
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        resp = await self._client.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers={"Ocp-Apim-Subscription-Key": self._key},
            params={"q": query, "count": num_results, "mkt": "en-US"},
        )
        resp.raise_for_status()
        data = resp.json()
        results: list[SearchResult] = []
        for i, item in enumerate(data.get("webPages", {}).get("value", [])):
            results.append(
                SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source=item.get("displayUrl", ""),
                    date=item.get("dateLastCrawled", ""),
                    position=i + 1,
                    raw=item,
                )
            )
        log.info("bing.search", query=query[:80], results=len(results))
        return results


# ── Tavily Provider ──────────────────────────────────────────────────

class TavilyProvider(SearchProvider):
    """Tavily AI search API."""

    def __init__(self, api_key: str | None = None):
        self._key = api_key or os.environ.get("TAVILY_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=20.0)

    async def close(self) -> None:
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        resp = await self._client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self._key,
                "query": query,
                "max_results": num_results,
                "search_depth": "advanced",
                "include_answer": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        results: list[SearchResult] = []
        for i, item in enumerate(data.get("results", [])):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=(
                        item.get("url", "").split("/")[2]
                        if "/" in item.get("url", "") else ""
                    ),
                    date="",
                    position=i + 1,
                    raw=item,
                )
            )
        log.info("tavily.search", query=query[:80], results=len(results))
        return results


# ── Factory ──────────────────────────────────────────────────────────

_PROVIDERS: dict[str, type[SearchProvider]] = {
    "serpapi": SerpAPIProvider,
    "bing": BingProvider,
    "tavily": TavilyProvider,
}


def create_search_provider(name: str = "serpapi") -> SearchProvider:
    """Create a search provider by name."""
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        raise ValueError(
            f"Unknown search provider: {name!r}. Choose from: {list(_PROVIDERS)}"
        )
    return cls()
