"""Specialized extractor for Kraken emails."""

from __future__ import annotations

from typing import Any, Dict, List

from .base import BaseExtractor
from digital_asset_harvester.parsers.definitions import KRAKEN_TEMPLATE
from digital_asset_harvester.parsers.engine import TemplateEngine


class KrakenExtractor(BaseExtractor):
    """Extractor for Kraken trade confirmation emails."""

    def __init__(self):
        self.engine = TemplateEngine(KRAKEN_TEMPLATE)

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Kraken email."""
        return self.engine.can_handle(subject, sender)

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Kraken email."""
        return self.engine.extract(subject, body)
