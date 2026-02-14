"""Utility for scrubbing Personally Identifiable Information (PII) from text."""

from __future__ import annotations

import logging
from typing import Optional, Set

import regex as re

logger = logging.getLogger(__name__)


class PIIScrubber:
    """Detects and masks PII in text using regular expressions."""

    def __init__(self, skip_terms: Optional[Set[str]] = None):
        """
        Initialize the scrubber.

        Args:
            skip_terms: A set of terms that should not be masked even if they
                match a PII pattern (e.g., crypto currency names).
        """
        self.skip_terms = {term.lower() for term in (skip_terms or set())}

        # Email addresses
        self.email_re = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE)

        # Phone numbers (broad pattern)
        self.phone_re = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4,6}", re.IGNORECASE)

        # IP Addresses (IPv4)
        self.ip_re = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

        # Credit Card Numbers
        self.cc_re = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")

        # Physical Addresses (Heuristic)
        # Matches: Number + Street Name + Suffix (St, Ave, etc.)
        self.address_re = re.compile(
            r"\b\d{1,5}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+"
            r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Way)",
            re.IGNORECASE,
        )

        # Name patterns (Heuristic)
        # Matches: Hi/Dear/Hello followed by 1-3 capitalized words
        self.name_greeting_re = re.compile(
            r"\b(Hi|Dear|Hello|Greetings)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})", re.MULTILINE
        )

    def _should_mask(self, match_text: str) -> bool:
        """Check if the matched text should actually be masked."""
        return match_text.lower() not in self.skip_terms

    def scrub(self, text: str) -> str:
        """
        Mask PII in the given text.

        Args:
            text: The text to scrub.

        Returns:
            The scrubbed text with PII masked by placeholders.
        """
        if not text:
            return text

        # Scrub emails
        text = self.email_re.sub(lambda m: "[EMAIL]" if self._should_mask(m.group(0)) else m.group(0), text)

        # Scrub phone numbers
        text = self.phone_re.sub(lambda m: "[PHONE]" if self._should_mask(m.group(0)) else m.group(0), text)

        # Scrub IP addresses
        text = self.ip_re.sub("[IP_ADDRESS]", text)

        # Scrub credit cards
        text = self.cc_re.sub("[CREDIT_CARD]", text)

        # Scrub addresses
        text = self.address_re.sub(lambda m: "[ADDRESS]" if self._should_mask(m.group(0)) else m.group(0), text)

        # Scrub names in greetings
        def mask_name(match):
            greeting = match.group(1)
            name = match.group(2)
            if self._should_mask(name):
                return f"{greeting} [NAME]"
            return match.group(0)

        text = self.name_greeting_re.sub(mask_name, text)

        return text
