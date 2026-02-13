"""Base class for specialized email extractors."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseExtractor(ABC):
    """Abstract base class for specialized extractors."""

    @abstractmethod
    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this extractor can handle the given email."""
        raise NotImplementedError

    @abstractmethod
    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract purchase information from the email."""
        raise NotImplementedError

    def _find_match(self, pattern: str | re.Pattern, text: str, group: int = 1) -> Optional[str]:
        """Helper to find a single match in text."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return match.group(group).strip()
            except IndexError:
                return None
        return None

    def _find_all_matches(self, pattern: str | re.Pattern, text: str) -> List[re.Match]:
        """Helper to find all matches in text."""
        return list(re.finditer(pattern, text, re.IGNORECASE))
