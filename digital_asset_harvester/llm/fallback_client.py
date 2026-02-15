"""Fallback LLM provider that switches to a secondary provider if the primary fails."""

from __future__ import annotations

import logging
from typing import Optional

from .ollama_client import LLMError
from .provider import LLMProvider, LLMResult

logger = logging.getLogger(__name__)


class FallbackLLMClient(LLMProvider):
    """LLM provider that tries a primary provider and falls back to a secondary one on failure."""

    def __init__(
        self,
        primary: LLMProvider,
        secondary: LLMProvider,
        name: str = "FallbackClient",
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.name = name

    def generate_json(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        retries: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResult:
        try:
            logger.info("Trying primary LLM provider...")
            result = self.primary.generate_json(
                prompt, model=model, retries=retries, temperature=temperature
            )
            if result.metadata is None:
                result.metadata = {}
            result.metadata["fallback_used"] = False
            result.metadata["provider_used"] = "primary"
            return result
        except (LLMError, Exception) as exc:
            logger.warning(
                "Primary LLM provider failed, falling back to secondary: %s", exc
            )
            result = self.secondary.generate_json(
                prompt, model=model, retries=retries, temperature=temperature
            )
            if result.metadata is None:
                result.metadata = {}
            result.metadata["fallback_used"] = True
            result.metadata["provider_used"] = "secondary"
            return result
