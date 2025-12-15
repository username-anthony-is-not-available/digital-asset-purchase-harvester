"""Lightweight metrics tracking utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class MetricsTracker:
    """Simple in-memory counter tracker."""

    counters: Dict[str, int] = field(default_factory=dict)

    def increment(self, name: str, value: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + value

    def get(self, name: str) -> int:
        return self.counters.get(name, 0)

    def snapshot(self) -> Dict[str, int]:
        return dict(self.counters)
