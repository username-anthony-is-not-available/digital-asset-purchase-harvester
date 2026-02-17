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

    def __new__(cls, cache_file: str, *args: Any, **kwargs: Any) -> LLMCache:
        if cache_file not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cache_file] = instance
            return instance
        return cls._instances[cache_file]

    def __init__(self, cache_file: str, auto_save: bool = True) -> None:
        if hasattr(self, "cache_file"):
            # If we're changing auto_save for an existing instance
            self.auto_save_enabled = auto_save
            return
        self.cache_file = cache_file
        self.auto_save_enabled = auto_save
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

    def save(self) -> None:
        """Save cache to disk."""
        if not isinstance(self.cache_file, str) or not self.cache_file:
            logger.debug("Skipping cache save: invalid cache_file type or empty path")
            return

        # Defensive check for MagicMock or other objects that might have been passed in tests
        if hasattr(self.cache_file, "assert_called") or "MagicMock" in str(type(self.cache_file)):
            logger.debug("Skipping cache save: cache_file is a mock object")
            return

        try:
            # Use a temporary file for atomic write
            temp_path = f"{self.cache_file}.tmp"
            with open(temp_path, "w") as f:
                json.dump(self.cache, f, indent=2)
            os.replace(temp_path, self.cache_file)
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
        self,
        prompt: str,
        data: Dict[str, Any],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        auto_save: Optional[bool] = None,
    ) -> None:
        """Cache a response."""
        prompt_hash = self._get_hash(prompt, model, temperature)
        self.cache[prompt_hash] = data

        # Use provided auto_save or fallback to instance default
        should_save = auto_save if auto_save is not None else self.auto_save_enabled
        if should_save:
            self.save()
