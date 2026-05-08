"""Data models for template-based email parsing."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class TransactionPattern:
    """Regex pattern and configuration for extracting a transaction."""
    regex: str
    transaction_type: Optional[str] = None
    # Map regex group names to field names if not using standard names
    field_map: Dict[str, str] = field(default_factory=dict)
    # Default values for fields not in regex
    defaults: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SectionConfig:
    """Configuration for parsing emails with multiple transaction sections."""
    split_by: str
    transaction_patterns: List[TransactionPattern] = field(default_factory=list)


@dataclass
class ExtractionTemplate:
    """Complete template for an exchange's emails."""
    vendor: str
    sender_patterns: List[str] = field(default_factory=list)
    subject_patterns: List[str] = field(default_factory=list)
    # Patterns applied to the whole body (or subject)
    global_patterns: List[TransactionPattern] = field(default_factory=list)
    # Patterns for sectioned bodies (e.g. Binance multi-asset)
    sections: Optional[SectionConfig] = None
    # Ticker standardization (e.g. XBT -> BTC)
    ticker_map: Dict[str, str] = field(default_factory=dict)
    # Currency symbol mapping
    symbol_map: Dict[str, str] = field(default_factory=lambda: {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY",
        "A$": "AUD",
        "C$": "CAD"
    })
