"""Utility for fetching historical FX rates."""

import logging
import time
import random
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

        # Parse date using robust dateutil parser
        try:
            dt = parser.parse(purchase_date_str)
            date_key = dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError, OverflowError) as e:
            logger.warning(f"Could not parse date '{purchase_date_str}': {e}")
            return None

        cache_key = f"{date_key}_{from_currency}_{to_currency}"
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        # Retry logic for network requests
        max_attempts = 3
        url = f"{self.base_url}/{date_key}?from={from_currency}&to={to_currency}"

        for attempt in range(1, max_attempts + 1):
            try:
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
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt < max_attempts:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"FX rate fetch attempt {attempt} failed, retrying in {sleep_time:.2f}s: {e}")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Failed to fetch FX rate after {max_attempts} attempts: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching FX rate: {e}")
                break

        return None

# Singleton instance
fx_service = FXRateService()
