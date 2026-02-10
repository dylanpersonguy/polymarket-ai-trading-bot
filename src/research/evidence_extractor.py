"""Evidence extractor — pulls structured evidence from fetched sources.

Uses an LLM to:
  1. Extract key numeric facts with dates, units, and sources
  2. Identify the most relevant evidence bullets with citations
  3. Detect contradictions between sources
  4. Assess overall evidence quality
  5. Determine confidence score

Implements strict extraction rules:
  - ONLY extract: numbers, official statements, dates, direct quotes
  - Every fact must have: metric name, value, unit, date, source, URL
  - If sources conflict: list both, reduce confidence
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI

from src.config import ForecastingConfig
from src.observability.logger import get_logger
from src.research.source_fetcher import FetchedSource

log = get_logger(__name__)


@dataclass
class Citation:
    """A source citation."""
    url: str
    publisher: str
    date: str
    title: str = ""


@dataclass
class EvidenceBullet:
    """A single piece of evidence with citation."""
    text: str
    citation: Citation
    relevance: float = 0.0   # 0-1 scale
    is_numeric: bool = False
    metric_name: str = ""
    metric_value: str = ""
    metric_unit: str = ""
    metric_date: str = ""
    confidence: float = 0.5


@dataclass
class Contradiction:
    """When two sources disagree."""
    claim_a: str
    source_a: Citation
    claim_b: str
    source_b: Citation
    description: str = ""


@dataclass
class EvidencePackage:
    """Complete evidence package for a market."""
    market_id: str
    question: str
    market_type: str = "UNKNOWN"
    bullets: list[EvidenceBullet] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    quality_score: float = 0.0   # 0-1 scale
    num_sources: int = 0
    summary: str = ""
    raw_llm_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "market_id": self.market_id,
            "question": self.question,
            "market_type": self.market_type,
            "evidence": [
                {
                    "text": b.text,
                    "citation": {
                        "url": b.citation.url,
                        "publisher": b.citation.publisher,
                        "date": b.citation.date,
                        "title": b.citation.title,
                    },
                    "relevance": b.relevance,
                    "is_numeric": b.is_numeric,
                    "metric_name": b.metric_name,
                    "metric_value": b.metric_value,
                    "metric_unit": b.metric_unit,
                    "metric_date": b.metric_date,
                    "confidence": b.confidence,
                }
                for b in self.bullets
            ],
            "contradictions": [
                {
                    "claim_a": c.claim_a,
                    "source_a_url": c.source_a.url,
                    "claim_b": c.claim_b,
                    "source_b_url": c.source_b.url,
                    "description": c.description,
                }
                for c in self.contradictions
            ],
            "quality_score": self.quality_score,
            "num_sources": self.num_sources,
            "summary": self.summary,
        }


_EXTRACTION_PROMPT = """\
You are a precise research analyst extracting evidence for a prediction market.

MARKET QUESTION: {question}
MARKET TYPE: {market_type}

SOURCES:
{sources_block}

TASK:
Analyze all sources and extract structured evidence. Return valid JSON:
{{
  "bullets": [
    {{
      "text": "key fact or statistic with specific numbers/dates",
      "source_index": <int>,
      "relevance": <0.0-1.0>,
      "is_numeric": <bool>,
      "metric_name": "e.g. CPI YoY, unemployment rate",
      "metric_value": "e.g. 3.2",
      "metric_unit": "e.g. percent, USD, basis points",
      "metric_date": "e.g. 2026-01-15",
      "confidence": <0.0-1.0>
    }}
  ],
  "contradictions": [
    {{
      "claim_a": "claim from source A",
      "source_a_index": <int>,
      "claim_b": "contradicting claim from source B",
      "source_b_index": <int>,
      "description": "brief explanation of disagreement"
    }}
  ],
  "quality_score": <0.0-1.0>,
  "summary": "2-3 sentence summary of the evidence landscape"
}}

EXTRACTION RULES:
- Extract ONLY: numbers, official statements, dates, direct quotes.
- Every numeric fact MUST have metric_name, metric_value, metric_unit, metric_date.
- Prefer recent data. Mark stale data (>30 days) with lower confidence.
- quality_score: 1.0 = overwhelming authoritative evidence, 0.0 = no relevant evidence.
- If sources contradict: list ALL contradictions AND lower quality_score by 0.1 per contradiction.
- If no authoritative primary source found: quality_score <= 0.3.
- Include at least the top 5 most relevant bullets.
- source_index = 0-based index of the source above.
- Do NOT fabricate data. If a source doesn't contain a number, don't invent one.

Return ONLY valid JSON, no markdown fences.
"""


class EvidenceExtractor:
    """Extract structured evidence from sources using an LLM."""

    def __init__(self, config: ForecastingConfig):
        self._config = config
        self._llm = AsyncOpenAI()

    async def extract(
        self,
        market_id: str,
        question: str,
        sources: list[FetchedSource],
        market_type: str = "UNKNOWN",
    ) -> EvidencePackage:
        """Extract evidence from a list of fetched sources."""
        if not sources:
            log.warning("evidence_extractor.no_sources", market_id=market_id)
            return EvidencePackage(
                market_id=market_id,
                question=question,
                market_type=market_type,
                quality_score=0.0,
                summary="No sources available for analysis.",
            )

        # Build sources block
        source_lines: list[str] = []
        for i, s in enumerate(sources):
            source_lines.append(
                f"[{i}] {s.title}\n"
                f"    URL: {s.url}\n"
                f"    Publisher: {s.publisher}\n"
                f"    Date: {s.date or 'unknown'}\n"
                f"    Authority: {s.authority_score:.1f}\n"
                f"    Snippet: {s.snippet[:500]}"
            )
        sources_block = "\n\n".join(source_lines)

        prompt = _EXTRACTION_PROMPT.format(
            question=question,
            market_type=market_type,
            sources_block=sources_block,
        )

        try:
            resp = await self._llm.chat.completions.create(
                model=self._config.llm_model,
                temperature=0.1,
                max_tokens=self._config.llm_max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise research analyst. "
                            "Return only valid JSON. Never fabricate data."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            raw_text = resp.choices[0].message.content or "{}"
            # Strip markdown code fences if present
            raw_text = raw_text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            parsed = json.loads(raw_text)
        except Exception as e:
            log.error("evidence_extractor.llm_failed", market_id=market_id, error=str(e))
            return EvidencePackage(
                market_id=market_id,
                question=question,
                market_type=market_type,
                quality_score=0.0,
                summary=f"LLM extraction failed: {e}",
            )

        return _build_package(market_id, question, market_type, sources, parsed)


def _build_package(
    market_id: str,
    question: str,
    market_type: str,
    sources: list[FetchedSource],
    parsed: dict[str, Any],
) -> EvidencePackage:
    """Build an EvidencePackage from parsed LLM output."""
    bullets: list[EvidenceBullet] = []
    for b in parsed.get("bullets", []):
        idx = b.get("source_index", 0)
        src = sources[idx] if 0 <= idx < len(sources) else None
        citation = Citation(
            url=src.url if src else "",
            publisher=src.publisher if src else "",
            date=src.date if src else "",
            title=src.title if src else "",
        )
        bullets.append(
            EvidenceBullet(
                text=b.get("text", ""),
                citation=citation,
                relevance=float(b.get("relevance", 0.5)),
                is_numeric=bool(b.get("is_numeric", False)),
                metric_name=b.get("metric_name", ""),
                metric_value=b.get("metric_value", ""),
                metric_unit=b.get("metric_unit", ""),
                metric_date=b.get("metric_date", ""),
                confidence=float(b.get("confidence", 0.5)),
            )
        )

    contradictions: list[Contradiction] = []
    for c in parsed.get("contradictions", []):
        idx_a = c.get("source_a_index", 0)
        idx_b = c.get("source_b_index", 0)
        src_a = sources[idx_a] if 0 <= idx_a < len(sources) else None
        src_b = sources[idx_b] if 0 <= idx_b < len(sources) else None
        contradictions.append(
            Contradiction(
                claim_a=c.get("claim_a", ""),
                source_a=Citation(
                    url=src_a.url if src_a else "",
                    publisher=src_a.publisher if src_a else "",
                    date=src_a.date if src_a else "",
                ),
                claim_b=c.get("claim_b", ""),
                source_b=Citation(
                    url=src_b.url if src_b else "",
                    publisher=src_b.publisher if src_b else "",
                    date=src_b.date if src_b else "",
                ),
                description=c.get("description", ""),
            )
        )

    package = EvidencePackage(
        market_id=market_id,
        question=question,
        market_type=market_type,
        bullets=bullets,
        contradictions=contradictions,
        quality_score=float(parsed.get("quality_score", 0.0)),
        num_sources=len(sources),
        summary=parsed.get("summary", ""),
        raw_llm_response=parsed,
    )

    log.info(
        "evidence_extractor.extracted",
        market_id=market_id,
        bullets=len(bullets),
        contradictions=len(contradictions),
        quality=package.quality_score,
    )
    return package


def parse_evidence_from_raw(
    market_id: str,
    question: str,
    sources: list[FetchedSource],
    raw_json: dict[str, Any],
    market_type: str = "UNKNOWN",
) -> EvidencePackage:
    """Public helper to build an EvidencePackage from already-parsed JSON (for tests)."""
    return _build_package(market_id, question, market_type, sources, raw_json)
