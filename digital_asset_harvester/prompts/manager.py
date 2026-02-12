"""Prompt management utilities."""

from __future__ import annotations

from dataclasses import dataclass
from string import Template
from typing import Dict, Optional


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    template: Template

    def render(self, **context: str) -> str:
        return self.template.safe_substitute(**context)


class PromptManager:
    def __init__(self, templates: Optional[Dict[str, PromptTemplate]] = None) -> None:
        self._templates: Dict[str, PromptTemplate] = templates or {}

    def register(self, name: str, text: str) -> None:
        self._templates[name] = PromptTemplate(name=name, template=Template(text))

    def get(self, name: str) -> PromptTemplate:
        if name not in self._templates:
            raise KeyError(f"Prompt '{name}' not registered")
        return self._templates[name]

    def render(self, name: str, **context: str) -> str:
        return self.get(name).render(**context)


DEFAULT_PROMPTS = PromptManager()

DEFAULT_PROMPTS.register(
    "classification",
    """You are an expert at analyzing cryptocurrency purchase emails. Determine if the following email content represents an ACTUAL cryptocurrency purchase transaction (not marketing, news, or other non-transactional content).

EMAIL CONTENT:
${email_content}

ANALYSIS CRITERIA:
- Look for ACTUAL purchase/buy transactions, order confirmations, trade executions, or staking rewards/distributions
- Cryptocurrency exchanges: Coinbase, Binance, Kraken, Gemini, etc.
- Purchase indicators: "bought", "purchased", "order filled", "transaction completed", "payment processed", "staking reward", "earned", "distribution confirmation"
- Specific amounts and cryptocurrency names (Bitcoin, Ethereum, BTC, ETH, etc.)
- Transaction IDs, order numbers, or confirmation codes

EXCLUDE these types of emails:
- Marketing emails, newsletters, promotional content
- Price alerts, market analysis, or news updates
- Account notifications, security alerts, or general announcements  
- Educational content, blog posts, or webinars
- Referral programs, contests, or airdrops
- Failed transactions or declined orders

Return a JSON object with this exact structure:
{
    "is_crypto_purchase": boolean,
    "confidence": float (0.0 to 1.0),
    "reasoning": "Brief explanation of your decision"
}
""",
)

DEFAULT_PROMPTS.register(
    "extraction",
    """You are an expert at extracting cryptocurrency purchase details from transaction emails. Analyze the following email content and extract precise purchase information.

EMAIL CONTENT:
${email_content}

EXTRACTION INSTRUCTIONS:
Extract the following information with high accuracy:

1. TOTAL_SPENT: The exact amount of fiat currency paid (look for phrases like "Total:", "Amount charged:", "You paid:", "Cost:")
2. CURRENCY: The fiat currency code (USD, EUR, GBP, CAD, AUD, etc.)
3. AMOUNT: The exact quantity of cryptocurrency received (look for crypto amounts, not fiat)
4. ITEM_NAME: The full cryptocurrency name or symbol (Bitcoin, BTC, Ethereum, ETH, etc.)
5. VENDOR: The exchange/platform name (Coinbase, Binance, Kraken, etc.)
6. PURCHASE_DATE: Extract from email headers, transaction timestamps, or order dates

COMMON EMAIL PATTERNS TO LOOK FOR:
- Coinbase: "You bought X BTC for $Y USD", "Order #12345 completed"
- Binance: "Buy order filled", "Transaction completed", "Deposit Successful", "Withdrawal Successful", "Distribution Confirmation"
- Kraken: "Order executed", "Trade confirmation", "Staking Reward Received"
- General: "Purchase confirmation", "Transaction receipt", "Order summary", "You just earned X staking rewards"

EXTRACTION EXAMPLES:
- "You bought 0.001 BTC for $25.00 USD" → total_spent: 25.00, currency: "USD", amount: 0.001, item_name: "BTC", transaction_type: "buy"
- "Order filled: 0.5 ETH at $1,500.00" → total_spent: 1500.00, currency: "USD", amount: 0.5, item_name: "ETH", transaction_type: "buy"
- "Binance - Deposit Successful - You've received 0.1 BTC" → total_spent: null, currency: null, amount: 0.1, item_name: "BTC", transaction_type: "deposit"
- "You just earned 0.0001 ETH in staking rewards" → total_spent: null, currency: null, amount: 0.0001, item_name: "ETH", transaction_type: "staking_reward"
- "$100.00 USD → 0.0025 Bitcoin" → total_spent: 100.00, currency: "USD", amount: 0.0025, item_name: "Bitcoin", transaction_type: "buy"

IMPORTANT RULES:
- Extract EXACT numerical values, don't round or estimate
- Use null for any field you cannot determine with confidence
- For item_name, use the EXACT term from the email (BTC vs Bitcoin, ETH vs Ethereum)
- For vendor, extract the actual company name, not generic terms
- Extract transaction IDs, reference numbers, or order numbers into a "transaction_id" field if available
- Parse dates carefully - look for transaction time, not email send time
- If timezone missing, assume ${default_timezone}

Return JSON with this exact structure:
{
    "transaction_type": "buy" | "deposit" | "withdrawal" | "staking_reward",
    "total_spent": float or null,
    "currency": string or null,
    "amount": float or null, 
    "item_name": string or null,
    "vendor": string or null,
    "purchase_date": string or null,
    "confidence": float (0.0 to 1.0),
    "extraction_notes": "Any relevant notes about extraction quality or concerns"
}

If no valid purchase information can be extracted, return null for the entire object.
""",
)
