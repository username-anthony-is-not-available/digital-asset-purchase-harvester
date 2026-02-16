"""Detailed metrics tracking utilities."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class MetricsTracker:
    """Simple in-memory counter and timing tracker."""

    counters: Dict[str, int] = field(default_factory=dict)
    latencies: Dict[str, List[float]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def increment(self, name: str, value: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + value

    def record_latency(self, name: str, duration: float) -> None:
        if name not in self.latencies:
            self.latencies[name] = []
        self.latencies[name].append(duration)

    def set_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def get(self, name: str) -> int:
        return self.counters.get(name, 0)

    def get_average_latency(self, name: str) -> float:
        times = self.latencies.get(name, [])
        if not times:
            return 0.0
        return sum(times) / len(times)

    def merge(self, other: MetricsTracker) -> None:
        """Merge another MetricsTracker into this one."""
        for name, count in other.counters.items():
            self.increment(name, count)
        for name, lats in other.latencies.items():
            if name not in self.latencies:
                self.latencies[name] = []
            self.latencies[name].extend(lats)
        self.metadata.update(other.metadata)

    def snapshot(self) -> Dict[str, Any]:
        """Return a combined snapshot of all metrics."""
        summary = dict(self.counters)
        for name in self.latencies:
            summary[f"{name}_avg_latency"] = self.get_average_latency(name)
            summary[f"{name}_count"] = len(self.latencies[name])
        summary.update(self.metadata)
        return summary
