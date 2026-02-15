"""Specialized extractors for major cryptocurrency exchanges."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import BaseExtractor
from .binance import BinanceExtractor
from .coinbase import CoinbaseExtractor
from .kraken import KrakenExtractor
from .gemini import GeminiExtractor
from .cryptocom import CryptocomExtractor
from .ftx import FTXExtractor
from .coinspot import CoinSpotExtractor


class ExtractorRegistry:
    """Registry for managing and selecting specialized extractors."""

    def __init__(self) -> None:
        self.extractors: List[BaseExtractor] = [
            CoinbaseExtractor(),
            BinanceExtractor(),
            KrakenExtractor(),
            GeminiExtractor(),
            CryptocomExtractor(),
            FTXExtractor(),
            CoinSpotExtractor(),
        ]

    def extract(self, subject: str, sender: str, body: str) -> Optional[List[Dict[str, Any]]]:
        """Attempt to extract data using registered specialized extractors."""
        for extractor in self.extractors:
            if extractor.can_handle(subject, sender, body):
                try:
                    results = extractor.extract(subject, sender, body)
                    if results:
                        return results
                except Exception:
                    # Fallback to next extractor or LLM if one fails
                    continue
        return None


# Global registry instance
registry = ExtractorRegistry()

__all__ = [
    "BaseExtractor",
    "CoinbaseExtractor",
    "BinanceExtractor",
    "KrakenExtractor",
    "ExtractorRegistry",
    "registry",
]
