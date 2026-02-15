"""Persistent caching for LLM responses."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LLMCache:
    """Handles persistent storage of LLM responses."""

    _instances: Dict[str, LLMCache] = {}

    def __new__(cls, cache_file: str) -> LLMCache:
        if cache_file not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cache_file] = instance
            return instance
        return cls._instances[cache_file]

    def __init__(self, cache_file: str) -> None:
        if hasattr(self, "cache_file"):
            return
        self.cache_file = cache_file
        self.cache: Dict[str, Any] = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from disk."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Failed to load LLM cache from %s: %s", self.cache_file, e)
        return {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save LLM cache to %s: %s", self.cache_file, e)

    def _get_hash(self, prompt: str, model: Optional[str] = None, temperature: Optional[float] = None) -> str:
        """Generate a unique hash for a prompt and its parameters."""
        content = f"{prompt}:{model}:{temperature}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(
        self, prompt: str, model: Optional[str] = None, temperature: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a cached response if available."""
        prompt_hash = self._get_hash(prompt, model, temperature)
        return self.cache.get(prompt_hash)

    def set(
        self, prompt: str, data: Dict[str, Any], model: Optional[str] = None, temperature: Optional[float] = None
    ) -> None:
        """Cache a response."""
        prompt_hash = self._get_hash(prompt, model, temperature)
        self.cache[prompt_hash] = data
        self._save_cache()
