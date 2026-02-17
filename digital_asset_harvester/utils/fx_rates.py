"""Utility for fetching historical FX rates."""

import logging
import time
from datetime import datetime, date
from typing import Dict, Optional, Any
from decimal import Decimal
from collections import OrderedDict
import httpx
from dateutil import parser

logger = logging.getLogger(__name__)

class FXRateService:
    """Service to fetch historical FX rates from a reliable external API."""

    def __init__(self, base_url: str = "https://api.frankfurter.app", max_cache_size: int = 1000):
        self.base_url = base_url
        self._cache: OrderedDict[str, Decimal] = OrderedDict()
        self.max_cache_size = max_cache_size

    def get_rate(self, purchase_date_str: str, from_currency: str, to_currency: str, max_retries: int = 3) -> Optional[Decimal]:
        """
        Fetch historical exchange rate for a given date.

        Args:
            purchase_date_str: Date string (e.g., '2024-01-01 12:00:00 UTC')
            from_currency: Source currency ISO code (e.g., 'USD')
            to_currency: Target currency ISO code (e.g., 'CAD')
            max_retries: Maximum number of retries for network requests.

        Returns:
            Exchange rate as Decimal, or None if not found or error.
        """
        if not from_currency or not to_currency or not purchase_date_str:
            return None

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return Decimal("1.0")

        # Parse date to YYYY-MM-DD using dateutil for robustness
        try:
            dt = parser.parse(purchase_date_str)
            date_key = dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError, parser.ParserError):
            logger.warning(f"Could not parse date: {purchase_date_str}")
            return None

        cache_key = f"{date_key}_{from_currency}_{to_currency}"
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        last_error = None
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/{date_key}?from={from_currency}&to={to_currency}"
                response = httpx.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                rate = data.get("rates", {}).get(to_currency)
                if rate is not None:
                    decimal_rate = Decimal(str(rate))
                    self._cache[cache_key] = decimal_rate
                    if len(self._cache) > self.max_cache_size:
                        self._cache.popitem(last=False)
                    return decimal_rate
                else:
                    logger.warning(f"Rate not found for {from_currency} to {to_currency} on {date_key}")
                    return None
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying FX rate fetch in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch FX rate after {max_retries} attempts: {last_error}")

        return None

# Singleton instance
fx_service = FXRateService()
