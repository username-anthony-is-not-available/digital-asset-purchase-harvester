"""Template definitions for various exchanges."""

from .models import ExtractionTemplate, TransactionPattern, SectionConfig

COINBASE_TEMPLATE = ExtractionTemplate(
    vendor="Coinbase",
    sender_patterns=[r"coinbase\.com"],
    subject_patterns=[
        r"purchase of",
        r"you bought",
        r"you received",
        r"recent purchase",
        r"staking reward"
    ],
    global_patterns=[
        # You successfully purchased 0.001 BTC for $100.00 USD.
        TransactionPattern(
            regex=r"(?:purchased|bought|buy)\s+(?P<amount>[\d,.]+)\s+(?P<item_name>[A-Z0-9]{2,10})\s+for\s+(?P<currency_symbol>[$€£¥])?(?P<total_spent>[\d,.]+)\s*(?P<currency>[A-Z]{3,5})?",
            transaction_type="buy"
        ),
        # purchased $100 of BTC
        TransactionPattern(
            regex=r"purchased\s+(?P<currency_symbol>[$€£¥])?(?P<total_spent>[\d,.]+)\s+of\s+(?P<item_name>[A-Z0-9]{2,10})",
            transaction_type="buy"
        ),
        # You just earned 0.00001234 ETH in staking rewards!
        TransactionPattern(
            regex=r"(?:earned|received)\s+(?P<amount>[\d,.]+)\s+(?P<item_name>[A-Z0-9]{2,10})\s+in\s+staking rewards",
            transaction_type="staking_reward"
        ),
        # Fee info (global)
        TransactionPattern(
            regex=r"(?:fee of|Coinbase Fee)\s*(?P<currency_symbol>[$€£¥])?(?P<fee_amount>[\d,.]+)\s*(?P<fee_currency>[A-Z]{3,5})?",
        )
    ]
)

BINANCE_TEMPLATE = ExtractionTemplate(
    vendor="Binance",
    sender_patterns=[r"binance\.com"],
    subject_patterns=[
        r"trade confirmation",
        r"order to buy",
        r"order execution",
        r"filled",
        r"deposit successful",
        r"withdrawal successful",
        r"distribution confirmation"
    ],
    global_patterns=[
        # Your order to buy 0.1 ETH for 200.00 USD has been filled.
        TransactionPattern(
            regex=r"buy\s+(?P<amount>[\d,.]+)\s+(?P<item_name>[A-Z0-9]{2,10})\s+for\s+(?P<total_spent>[\d,.]+)\s+(?P<currency>[A-Z0-9]{3,5})",
            transaction_type="buy"
        ),
        # Your account has been credited with 0.5 SOL for SOL Staking.
        TransactionPattern(
            regex=r"credited with\s+(?P<amount>[\d,.]+)\s+(?P<item_name>[A-Z0-9]{2,10})",
            transaction_type="staking_reward"
        ),
        # deposited/withdrawn 0.1 BTC
        TransactionPattern(
            regex=r"(?P<tx_type>deposited|withdrawn)\s+(?P<amount>[\d,.]+)\s+(?P<item_name>[A-Z0-9]{2,10})",
            field_map={"tx_type": "transaction_type"}
        )
    ],
    sections=SectionConfig(
        split_by=r"(?:Order Details|Details:|- Pair:)",
        transaction_patterns=[
            TransactionPattern(
                regex=r"Amount:\s*(?P<amount>[\d,.]+)\s*(?P<item_name>[A-Z0-9]{2,10})?",
            ),
            TransactionPattern(
                regex=r"(?:Total|Total Cost):\s*(?P<total_spent>[\d,.]+)\s*(?P<currency>[A-Z0-9]{3,10})?",
            ),
            TransactionPattern(
                regex=r"Side:\s*(?P<side>Buy|Sell)",
                field_map={"side": "transaction_type"}
            ),
            TransactionPattern(
                regex=r"Fee:\s*(?P<fee_amount>[\d,.]+)\s*(?P<fee_currency>[A-Z0-9]{2,10})?",
            )
        ]
    )
)

KRAKEN_TEMPLATE = ExtractionTemplate(
    vendor="Kraken",
    sender_patterns=[r"kraken\.com"],
    subject_patterns=[
        r"trade confirmation",
        r"kraken order",
        r"staking reward received",
        r"staking rewards? are here",
        r"staking payout summary",
        r"reward summary"
    ],
    global_patterns=[
        # You bought 0.75 XBT (BTC) for $35,000.00 USD.
        TransactionPattern(
            regex=r"(?:bought|buy)\s+(?P<amount>[\d,.]+)\s+(?P<item_name>[A-Z0-9]{2,10})(?:\s+\([A-Z0-9]+\))?\s+for\s+(?P<currency_symbol>[$€£¥])?(?P<total_spent>[\d,.]+)\s*(?P<currency>[A-Z]{3,5})?",
            transaction_type="buy"
        ),
        # credited your account with 10.5 ADA
        TransactionPattern(
            regex=r"credited your account with\s+(?P<amount>[\d,.]+)\s+(?P<item_name>[A-Z0-9]{2,10})",
            transaction_type="staking_reward"
        ),
        # staking reward of 0.05 DOT
        TransactionPattern(
            regex=r"staking reward of\s+(?P<amount>[\d,.]+)\s+(?P<item_name>[A-Z0-9]{2,10})",
            transaction_type="staking_reward"
        ),
        # * 0.00123 ETH
        TransactionPattern(
            regex=r"[*•-]\s+(?P<amount>[\d,.]+)\s+(?P<item_name>[A-Z0-9]{2,10})(?:\s|$)",
            transaction_type="staking_reward"
        ),
        # Fee: $105.00 USD
        TransactionPattern(
            regex=r"Fee:\s*(?P<currency_symbol>[$€£¥])?(?P<fee_amount>[\d,.]+)\s*(?P<fee_currency>[A-Z]{3,5})?",
        )
    ],
    ticker_map={
        "XBT": "BTC",
        "XDG": "DOGE",
    }
)

EXCHANGE_TEMPLATES = [
    COINBASE_TEMPLATE,
    BINANCE_TEMPLATE,
    KRAKEN_TEMPLATE,
]
