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
    # Additional exchange purchases
    "gemini_purchase": """
    From: Gemini <orders@gemini.com>
    Subject: Order Confirmation - Buy BTC

    Your order to purchase 0.005 BTC for $150.00 has been completed.
    Transaction ID: GEM-2024-001
    Date: 2024-01-15
    """,
    "ftx_purchase": """
    From: FTX <noreply@ftx.com>
    Subject: Trade Executed: BUY 10 MATIC

    Trade Details:
    Amount: 10 MATIC
    Price per unit: $0.85
    Total: $8.50 USD
    """,
    "coinspot_purchase": """
    From: CoinSpot <support@coinspot.com.au>
    Subject: Purchase Confirmation

    You have successfully purchased 50 ADA for $25.00 AUD.
    Reference: CS-20240115-001
    """,
    # Edge cases
    "partial_data_purchase": """
    From: Unknown Exchange <noreply@exchange.com>
    Subject: Order filled

    Your purchase was successful.
    Amount: 1.5 LTC
    """,
    "multi_currency_purchase": """
    From: Kraken <noreply@kraken.com>
    Subject: Multiple Orders Filled

    Order 1: Bought 0.01 BTC for $400 USD
    Order 2: Bought 0.5 ETH for $1000 USD
    Both orders completed successfully.
    """,
    "price_alert_not_purchase": """
    From: Binance <alerts@binance.com>
    Subject: Price Alert: BTC reached $50,000

    Bitcoin has reached your target price of $50,000.
    This is just an alert, no transaction occurred.
    """,
    "newsletter_crypto": """
    From: CoinDesk <newsletter@coindesk.com>
    Subject: Daily Crypto Briefing

    Top stories today:
    - Bitcoin reaches new high
    - Ethereum upgrade announced
    - New regulations proposed
    """,
    "withdrawal_email": """
    From: Coinbase <no-reply@coinbase.com>
    Subject: Withdrawal Confirmation

    You have successfully withdrawn 0.5 ETH to your external wallet.
    This is not a purchase.
    """,
    "deposit_confirmation": """
    From: Binance <deposits@binance.com>
    Subject: Deposit Received

    Your deposit of 100 USDT has been credited to your account.
    """,
    "failed_purchase": """
    From: Kraken <orders@kraken.com>
    Subject: Order Failed

    Your attempt to purchase 1 BTC has failed due to insufficient funds.
    """,
    # Test multipart and encoded content
    "encoded_subject_purchase": """
    From: Exchange <noreply@exchange.com>
    Subject: =?UTF-8?B?WW91ciBCVEMgcHVyY2hhc2U=?=

    Successfully purchased 0.1 BTC for $5000.
    """,
    "binance_deposit": """
    From: Binance <do-not-reply@binance.com>
    Subject: Deposit Successful

    You have successfully deposited 0.1 BTC.
    Transaction ID: BIN-DEP-2024-001
    """,
    "binance_withdrawal": """
    From: Binance <do-not-reply@binance.com>
    Subject: Withdrawal Successful

    You have successfully withdrawn 0.5 ETH.
    Transaction ID: BIN-WDR-2024-002
    """,
    "coinbase_staking_reward": """
    From: Coinbase <no-reply@coinbase.com>
    Subject: You've earned a staking reward

    You just earned 0.00001234 ETH in staking rewards!
    Your new balance is 1.23456789 ETH.
    Transaction ID: CB-STAKE-2025-ABC
    """,
    "binance_staking_reward": """
    From: Binance <do-not-reply@binance.com>
    Subject: Distribution Confirmation

    Your account has been credited with 0.5 SOL for SOL Staking.
    Reference: BIN-STAKE-2025-XYZ
    """,
    "kraken_staking_reward": """
    From: Kraken <noreply@kraken.com>
    Subject: Staking Reward Received

    We've credited your account with 10.5 ADA in staking rewards.
    ID: KR-STAKE-2025-999
    """,
    "binance_multi_asset": """
    From: Binance <do-not-reply@binance.com>
    Subject: Trade Confirmation
    Date: Wed, 20 Mar 2024 14:00:00 +0000

    Your trade order has been filled.

    Order Details:
    - Pair: BTC/USDT
    - Side: Buy
    - Amount: 0.002 BTC
    - Price: 65,000.00 USDT
    - Total: 130.00 USDT
    - Fee: 0.000002 BTC

    - Pair: ETH/USDT
    - Side: Buy
    - Amount: 0.1 ETH
    - Price: 3,500.00 USDT
    - Total: 350.00 USDT
    - Fee: 0.0001 ETH
    """,
    "binance_order_execution": """
    From: Binance <do-not-reply@binance.com>
    Subject: Order Execution Notice
    Date: Thu, 21 Mar 2024 09:15:00 +0000

    Your order #987654321 has been executed.

    Details:
    Trading Pair: SOL/USDT
    Amount: 5.0 SOL
    Price: 180.00 USDT
    Total Cost: 900.00 USDT
    Fee: 0.005 SOL
    """,
}


@pytest.fixture
def mock_purchase_email():
    """
    Provides a mock email body for testing.
    """
    return EMAIL_FIXTURES["coinbase_purchase"]


@pytest.fixture
def all_email_fixtures():
    """
    Provides all email fixtures for parameterized testing.
    """
    return EMAIL_FIXTURES


@pytest.fixture
def purchase_emails():
    """
    Returns only purchase-related email fixtures.
    """
    purchase_types = {
        "coinbase_purchase",
        "binance_purchase",
        "kraken_purchase",
        "complex_purchase",
        "gemini_purchase",
        "ftx_purchase",
        "coinspot_purchase",
        "partial_data_purchase",
        "multi_currency_purchase",
        "encoded_subject_purchase",
        "binance_multi_asset",
        "binance_order_execution",
    }
    return {k: v for k, v in EMAIL_FIXTURES.items() if k in purchase_types}


@pytest.fixture
def non_purchase_emails():
    """
    Returns only non-purchase email fixtures.
    """
    non_purchase_types = {
        "non_purchase",
        "marketing_email",
        "security_alert",
        "price_alert_not_purchase",
        "newsletter_crypto",
        "withdrawal_email",
        "deposit_confirmation",
        "failed_purchase",
    }
    return {k: v for k, v in EMAIL_FIXTURES.items() if k in non_purchase_types}
