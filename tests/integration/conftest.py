"""Integration test fixtures and utilities."""

import tempfile
from pathlib import Path
from typing import Iterator

import pytest


@pytest.fixture
def temp_mbox_file() -> Iterator[Path]:
    """Create a temporary mbox file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mbox", delete=False) as f:
        temp_path = Path(f.name)
        yield temp_path
        if temp_path.exists():
            temp_path.unlink()


@pytest.fixture
def sample_coinbase_email() -> str:
    """Sample Coinbase purchase confirmation email."""
    return """Subject: You've purchased Bitcoin
From: no-reply@coinbase.com
Date: Mon, 15 Jan 2024 10:30:00 -0500

Hi there,

You bought 0.001 BTC for $45.00 USD.

Transaction details:
- Asset: Bitcoin (BTC)
- Amount: 0.001 BTC
- Total: $45.00 USD
- Date: January 15, 2024
- Transaction ID: CB-123456789

Thanks for using Coinbase!
"""


@pytest.fixture
def sample_binance_email() -> str:
    """Sample Binance purchase confirmation email."""
    return """Subject: Order Filled - Buy BTC
From: do-not-reply@binance.com
Date: Tue, 16 Jan 2024 14:20:00 -0500

Your order has been filled.

Order Summary:
- Pair: BTC/USD
- Type: Buy
- Price: $42,500.00
- Quantity: 0.5 BTC
- Total: $21,250.00

Order ID: 987654321
Time: 2024-01-16 14:20:00 UTC
"""


@pytest.fixture
def sample_kraken_email() -> str:
    """Sample Kraken purchase confirmation email."""
    return """Subject: Trade Confirmation
From: noreply@kraken.com
Date: Wed, 17 Jan 2024 09:15:00 -0500

Trade executed successfully.

Details:
Bought: 2.5 ETH
Spent: $5,000.00 USD
Rate: $2,000.00 per ETH
Trade ID: KRK-ABC123
Executed: 2024-01-17 09:15:00 EST

Thank you for trading with Kraken.
"""


@pytest.fixture
def sample_newsletter_email() -> str:
    """Sample crypto newsletter (should NOT be detected as purchase)."""
    return """Subject: Weekly Crypto Market Update
From: newsletter@cryptonews.com
Date: Thu, 18 Jan 2024 08:00:00 -0500

This week in crypto:

Bitcoin reached a new high! Ethereum shows strong momentum!
Don't miss out on the next big opportunity.

Sign up now to start trading on our platform.
"""
