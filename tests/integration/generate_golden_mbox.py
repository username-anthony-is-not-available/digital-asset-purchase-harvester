import json
import mailbox
import os
from datetime import datetime, timezone


def create_golden_mbox():
    mbox_path = "tests/fixtures/golden.mbox"
    expected_path = "tests/fixtures/golden_expected.json"

    # Ensure fixtures directory exists
    os.makedirs("tests/fixtures", exist_ok=True)

    emails = [
        {
            "id": "coinbase_purchase",
            "from": "Coinbase <no-reply@coinbase.com>",
            "subject": "Your Coinbase purchase of 0.001 BTC",
            "body": "You successfully purchased 0.001 BTC for $100.00 USD.",
            "date": "Mon, 1 Jan 2024 10:00:00 +0000",
            "expected": [
                {
                    "amount": 0.001,
                    "item_name": "BTC",
                    "total_spent": 100.0,
                    "currency": "USD",
                    "vendor": "Coinbase",
                    "extraction_method": "regex",
                }
            ],
        },
        {
            "id": "binance_purchase",
            "from": "Binance <do-not-reply@binance.com>",
            "subject": "Your order to buy 0.1 ETH has been filled",
            "body": "Your order to buy 0.1 ETH for 200.00 USD has been filled.",
            "date": "Tue, 2 Jan 2024 11:00:00 +0000",
            "expected": [
                {
                    "amount": 0.1,
                    "item_name": "ETH",
                    "total_spent": 200.0,
                    "currency": "USD",
                    "vendor": "Binance",
                    "extraction_method": "regex",
                }
            ],
        },
        {
            "id": "kraken_purchase",
            "from": "Kraken <noreply@kraken.com>",
            "subject": "Trade Confirmation: Buy 0.5 XMR",
            "body": "You have successfully bought 0.5 XMR for 50.00 EUR.",
            "date": "Wed, 3 Jan 2024 12:00:00 +0000",
            "expected": [
                {
                    "amount": 0.5,
                    "item_name": "XMR",
                    "total_spent": 50.0,
                    "currency": "EUR",
                    "vendor": "Kraken",
                    "extraction_method": "regex",
                }
            ],
        },
        {
            "id": "gemini_purchase",
            "from": "Gemini <orders@gemini.com>",
            "subject": "Order Confirmation - Buy BTC",
            "body": "Your order to purchase 0.005 BTC for $150.00 has been completed.\nTransaction ID: GEM-2024-001",
            "date": "Thu, 4 Jan 2024 13:00:00 +0000",
            "expected": [
                {
                    "amount": 0.005,
                    "item_name": "BTC",
                    "total_spent": 150.0,
                    "currency": "USD",
                    "vendor": "Gemini",
                    "transaction_id": "GEM-2024-001",
                    "extraction_method": "regex",
                }
            ],
        },
        {
            "id": "cryptocom_purchase",
            "from": '"Crypto Exchange" <noreply@crypto.com>',
            "subject": "Your order #12345 has been executed",
            "body": "Your market order #12345 to buy 2.5 SOL has been filled at a price of $25.00 per SOL.\nTotal cost: $62.50 USD.",
            "date": "Fri, 5 Jan 2024 14:00:00 +0000",
            "expected": [
                {
                    "amount": 2.5,
                    "item_name": "SOL",
                    "total_spent": 62.5,
                    "currency": "USD",
                    "vendor": "Crypto.com",
                    "transaction_id": "12345",
                    "extraction_method": "regex",
                }
            ],
        },
        {
            "id": "ftx_purchase",
            "from": "FTX <noreply@ftx.com>",
            "subject": "Trade Executed: BUY 10 MATIC",
            "body": "Amount: 10 MATIC\nPrice per unit: $0.85\nTotal: $8.50 USD",
            "date": "Sat, 6 Jan 2024 15:00:00 +0000",
            "expected": [
                {
                    "amount": 10.0,
                    "item_name": "MATIC",
                    "total_spent": 8.5,
                    "currency": "USD",
                    "vendor": "FTX",
                    "extraction_method": "regex",
                }
            ],
        },
        {
            "id": "coinspot_purchase",
            "from": "CoinSpot <support@coinspot.com.au>",
            "subject": "Purchase Confirmation",
            "body": "You have successfully purchased 50 ADA for $25.00 AUD.\nReference: CS-20240115-001",
            "date": "Sun, 7 Jan 2024 16:00:00 +0000",
            "expected": [
                {
                    "amount": 50.0,
                    "item_name": "ADA",
                    "total_spent": 25.0,
                    "currency": "AUD",
                    "vendor": "CoinSpot",
                    "transaction_id": "CS-20240115-001",
                    "extraction_method": "regex",
                }
            ],
        },
        {
            "id": "coinbase_staking",
            "from": "Coinbase <no-reply@coinbase.com>",
            "subject": "You've earned a staking reward",
            "body": "You just earned 0.00001234 ETH in staking rewards!\nTransaction ID: CB-STAKE-2025-ABC",
            "date": "Mon, 8 Jan 2024 17:00:00 +0000",
            "expected": [
                {
                    "amount": 0.00001234,
                    "item_name": "ETH",
                    "vendor": "Coinbase",
                    "transaction_id": "CB-STAKE-2025-ABC",
                    "transaction_type": "staking_reward",
                    "extraction_method": "regex",
                }
            ],
        },
        {
            "id": "binance_multi",
            "from": "Binance <do-not-reply@binance.com>",
            "subject": "Trade Confirmation",
            "body": "Your trade order has been filled.\n\nOrder Details:\n- Pair: BTC/USDT\n- Side: Buy\n- Amount: 0.002 BTC\n- Price: 65,000.00 USDT\n- Total: 130.00 USDT\n\n- Pair: ETH/USDT\n- Side: Buy\n- Amount: 0.1 ETH\n- Price: 3,500.00 USDT\n- Total: 350.00 USDT",
            "date": "Tue, 9 Jan 2024 18:00:00 +0000",
            "expected": [
                {
                    "amount": 0.002,
                    "item_name": "BTC",
                    "total_spent": 130.0,
                    "currency": "USDT",
                    "vendor": "Binance",
                    "extraction_method": "regex",
                },
                {
                    "amount": 0.1,
                    "item_name": "ETH",
                    "total_spent": 350.0,
                    "currency": "USDT",
                    "vendor": "Binance",
                    "extraction_method": "regex",
                },
            ],
        },
        {
            "id": "generic_llm_purchase",
            "from": "info@someexchange.io",
            "subject": "Receipt for your order",
            "body": "You bought 1000 DOGE for 0.1 ETH on our platform.",
            "date": "Wed, 10 Jan 2024 19:00:00 +0000",
            "expected": [
                {
                    "amount": 1000.0,
                    "item_name": "DOGE",
                    "total_spent": 0.1,
                    "currency": "ETH",
                    "vendor": "SomeExchange",
                    "extraction_method": "llm",
                }
            ],
        },
        {
            "id": "newsletter",
            "from": "Newsletter <news@crypto.com>",
            "subject": "Crypto Weekly",
            "body": "Market is bullish today. Bitcoin is up 5%.",
            "date": "Thu, 11 Jan 2024 20:00:00 +0000",
            "expected": [],
        },
        {
            "id": "security_alert",
            "from": "Security <security@binance.com>",
            "subject": "New login from unknown device",
            "body": "We detected a login from a new device in London.",
            "date": "Fri, 12 Jan 2024 21:00:00 +0000",
            "expected": [],
        },
    ]

    # Remove existing mbox if any
    if os.path.exists(mbox_path):
        os.remove(mbox_path)

    mbox = mailbox.mbox(mbox_path)
    expected_data = {}

    for email_info in emails:
        msg = mailbox.mboxMessage()
        msg["From"] = email_info["from"]
        msg["Subject"] = email_info["subject"]
        msg["Date"] = email_info["date"]
        msg["Message-ID"] = f"<{email_info['id']}@golden-test.local>"
        msg.set_payload(email_info["body"])
        mbox.add(msg)

        expected_data[email_info["id"]] = email_info["expected"]

    mbox.flush()
    mbox.close()

    with open(expected_path, "w") as f:
        json.dump(expected_data, f, indent=4)
        f.write("\n")

    print(f"Generated {mbox_path} and {expected_path}")


if __name__ == "__main__":
    create_golden_mbox()
