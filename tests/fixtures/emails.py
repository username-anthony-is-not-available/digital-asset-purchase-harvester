import pytest

EMAIL_FIXTURES = {
    "coinbase_purchase": """
    From: Coinbase <no-reply@coinbase.com>
    Subject: Your Coinbase purchase of 0.001 BTC

    You successfully purchased 0.001 BTC for $100.00 USD.
    """,
    "binance_purchase": """
    From: Binance <do-not-reply@binance.com>
    Subject: Your order to buy 0.1 ETH has been filled

    Your order to buy 0.1 ETH for 200.00 USD has been filled.
    """,
    "non_purchase": """
    From: Crypto News <alerts@cryptonews.com>
    Subject: Bitcoin Price Alert

    Bitcoin is up 5% in the last 24 hours.
    """,
}


@pytest.fixture
def mock_purchase_email():
    """
    Provides a mock email body for testing.
    """
    return EMAIL_FIXTURES["coinbase_purchase"]
