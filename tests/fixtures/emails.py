"""Email fixtures for testing."""

EMAIL_FIXTURES = {
    "coinbase_purchase": {
        "subject": "You received bitcoin",
        "sender": "Coinbase <no-reply@coinbase.com>",
        "date": "2024-01-01T12:00:00Z",
        "body": """
        Hi,

        You received 0.001 BTC.

        Thanks,
        The Coinbase Team
        """,
    },
    "binance_purchase": {
        "subject": "Your order to buy ETH has been filled",
        "sender": "Binance <do-not-reply@binance.com>",
        "date": "2024-01-02T12:00:00Z",
        "body": """
        Your order to buy 0.1 ETH has been filled.

        Price: $2,000
        Total: $200
        """,
    },
    "non_purchase": {
        "subject": "Price Alert",
        "sender": "Coinbase <no-reply@coinbase.com>",
        "date": "2024-01-03T12:00:00Z",
        "body": "BTC is up 5%",
    },
}
