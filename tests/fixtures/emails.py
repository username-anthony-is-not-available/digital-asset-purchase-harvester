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
    "kraken_purchase": """
    From: Kraken <noreply@kraken.com>
    Subject: Trade Confirmation: Buy 0.5 XMR

    You have successfully bought 0.5 XMR for 50.00 EUR.
    """,
    "non_purchase": """
    From: Crypto News <alerts@cryptonews.com>
    Subject: Bitcoin Price Alert

    Bitcoin is up 5% in the last 24 hours.
    """,
    "marketing_email": """
    From: Ledger <hello@ledger.com>
    Subject: Ledger Nano X is back in stock!

    Don't miss out on our new hardware wallet.
    """,
    "security_alert": """
    From: Gemini <security@gemini.com>
    Subject: Security Alert: New device login

    A new device has been logged into your account.
    """,
    "complex_purchase": """
    From: "Crypto Exchange" <noreply@crypto.com>
    To: user@example.com
    Subject: Your order #12345 has been executed
    Date: Tue, 1 Jan 2024 12:30:00 +0000
    Content-Type: text/plain; charset="UTF-8"

    Your market order to buy 2.5 SOL has been filled at a price of $25.00 per SOL.
    Total cost: $62.50 USD.
    """,
}


@pytest.fixture
def mock_purchase_email():
    """
    Provides a mock email body for testing.
    """
    return EMAIL_FIXTURES["coinbase_purchase"]
