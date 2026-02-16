"""Utility for fetching historical FX rates."""

import logging
from collections import OrderedDict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class FXRateService:
    """Service to fetch historical FX rates from a reliable external API."""

    def __init__(self, base_url: str = "https://api.frankfurter.app", max_cache_size: int = 1000):
        self.base_url = base_url
        self._cache: OrderedDict[str, Decimal] = OrderedDict()
        self.max_cache_size = max_cache_size

    def get_rate(self, purchase_date_str: str, from_currency: str, to_currency: str) -> Optional[Decimal]:
        """
        Fetch historical exchange rate for a given date.

        Args:
            purchase_date_str: Date string (e.g., '2024-01-01 12:00:00 UTC')
            from_currency: Source currency ISO code (e.g., 'USD')
            to_currency: Target currency ISO code (e.g., 'CAD')

        Returns:
            Exchange rate as Decimal, or None if not found or error.
        """
        if not from_currency or not to_currency:
            return None

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return Decimal("1.0")

        # Parse date to YYYY-MM-DD
        try:
            # Try parsing with time first
            dt = datetime.strptime(purchase_date_str.split()[0], "%Y-%m-%d")
            date_key = dt.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            try:
                # Try parsing ISO format
                dt = datetime.fromisoformat(purchase_date_str.split("T")[0])
                date_key = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                logger.warning(f"Could not parse date: {purchase_date_str}")
                return None

        cache_key = f"{date_key}_{from_currency}_{to_currency}"
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

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
            logger.error(f"Failed to fetch FX rate: {e}")
            return None


# Singleton instance
fx_service = FXRateService()
