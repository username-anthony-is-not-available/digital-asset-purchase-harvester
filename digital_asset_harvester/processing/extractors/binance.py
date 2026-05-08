"""Specialized extractor for Binance emails."""

from __future__ import annotations

from typing import Any, Dict, List

from .base import BaseExtractor
from digital_asset_harvester.parsers.definitions import BINANCE_TEMPLATE
from digital_asset_harvester.parsers.engine import TemplateEngine


class BinanceExtractor(BaseExtractor):
    """Extractor for Binance trade confirmation emails."""

    def __init__(self):
        self.engine = TemplateEngine(BINANCE_TEMPLATE)

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Binance email."""
        return self.engine.can_handle(subject, sender)

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Binance email."""
        return self.engine.extract(subject, body)
