"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LLMResult:
    """Container for structured LLM responses."""

    data: Dict[str, Any]
    raw_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> LLMResult:
        """Execute a prompt expecting JSON output."""
        raise NotImplementedError
