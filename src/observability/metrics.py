"""Simple in-process metrics collection.

Stores counters, gauges, and histograms in memory.
Can be dumped to JSON for reporting.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class MetricPoint:
    name: str
    value: float
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Thread-safe in-process metrics collector."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._events: list[MetricPoint] = []

    def incr(self, name: str, value: float = 1.0, **tags: str) -> None:
        with self._lock:
            self._counters[name] += value
            self._events.append(MetricPoint(name=name, value=value, tags=tags))

    def gauge(self, name: str, value: float, **tags: str) -> None:
        with self._lock:
            self._gauges[name] = value
            self._events.append(MetricPoint(name=name, value=value, tags=tags))

    def histogram(self, name: str, value: float, **tags: str) -> None:
        with self._lock:
            self._histograms[name].append(value)
            self._events.append(MetricPoint(name=name, value=value, tags=tags))

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot of all metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    k: {
                        "count": len(v),
                        "min": min(v) if v else 0,
                        "max": max(v) if v else 0,
                        "avg": sum(v) / len(v) if v else 0,
                    }
                    for k, v in self._histograms.items()
                },
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._events.clear()


# Global singleton
metrics = MetricsCollector()
