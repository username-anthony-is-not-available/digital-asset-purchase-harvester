"""LLM client wrapper that provides caching functionality."""

from __future__ import annotations

import logging
from typing import Optional

from .cache import LLMCache
from .provider import LLMProvider, LLMResult

logger = logging.getLogger(__name__)


class CachingLLMClient(LLMProvider):
    """Wraps an LLMProvider with a caching layer."""

    def __init__(self, inner: LLMProvider, cache: LLMCache) -> None:
        self.inner = inner
        self.cache = cache

    def generate_json(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        retries: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResult:
        # Check cache first
        cached_data = self.cache.get(prompt, model=model, temperature=temperature)
        if cached_data:
            logger.info("Retrieved LLM result from cache")
            return LLMResult(
                data=cached_data["data"],
                raw_text=cached_data.get("raw_text", ""),
                metadata={"cached": True},
            )

        # Call inner provider
        result = self.inner.generate_json(
            prompt, model=model, retries=retries, temperature=temperature
        )

        # Cache the result
        self.cache.set(
            prompt,
            {"data": result.data, "raw_text": result.raw_text},
            model=model,
            temperature=temperature,
        )

        # Add metadata indicating it was a fresh call
        if result.metadata is None:
            result.metadata = {}
        result.metadata["cached"] = False

        return result
