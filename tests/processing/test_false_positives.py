"""False Positive Regression Suite for identifying non-purchase emails."""

from unittest.mock import MagicMock

import pytest

from digital_asset_harvester.config import HarvesterSettings
from digital_asset_harvester.processing.email_purchase_extractor import EmailPurchaseExtractor
from digital_asset_harvester.processing.extractors import registry

# Define negative test cases
NEGATIVE_EMAILS = [
    {
        "name": "Coinbase Weekly News",
        "subject": "Your weekly crypto news is here",
        "sender": "Coinbase <no-reply@coinbase.com>",
        "body": "Check out the top stories this week. Bitcoin hits new highs! Learn more about the market and what it means for your portfolio. We've added new articles to our blog.",
    },
    {
        "name": "Binance New Listing",
        "subject": "Binance will list NewCoin (NC)",
        "sender": "Binance <do-not-reply@binance.com>",
        "body": "Binance is excited to announce the listing of NewCoin (NC) in the Innovation Zone. Trading for NC/BTC and NC/USDT will open tomorrow. This is an announcement and not a trade confirmation.",
    },
    {
        "name": "Kraken Webinar Invite",
        "subject": "Last chance to join our webinar",
        "sender": "Kraken <noreply@kraken.com>",
        "body": "Join us for a live webinar on the future of DeFi and how Kraken is leading the way. Register now using the link below. Don't miss out on this educational opportunity.",
    },
    {
        "name": "Crypto.com Card Promotion",
        "subject": "Earn 5% back with your Visa Card",
        "sender": "Crypto.com <no-reply@crypto.com>",
        "body": "Upgrade your Crypto.com Visa Card today and start earning more rewards on your everyday spending. This is a promotion for cardholders. Terms and conditions apply.",
    },
    {
        "name": "Gemini Terms Update",
        "subject": "Important updates to our Terms of Service",
        "sender": "Gemini <no-reply@gemini.com>",
        "body": "We are updating our Terms of Service and Privacy Policy to better serve you. Please review the changes on our website. Continued use of our platform constitutes acceptance of these terms.",
    },
    {
        "name": "Binance Security Alert",
        "subject": "New login from a new device",
        "sender": "Binance <do-not-reply@binance.com>",
        "body": "A new login was detected for your account from a new device or IP address (1.2.3.4). If this was not you, please disable your account immediately and contact support.",
    },
    {
        "name": "Coinbase Price Alert",
        "subject": "Price Alert: Bitcoin is up 5%",
        "sender": "Coinbase <no-reply@coinbase.com>",
        "body": "Bitcoin (BTC) has increased by 5.02% in the last 24 hours and is now trading at $65,000.00. Set more alerts in the Coinbase app.",
    },
    {
        "name": "Generic Newsletter",
        "subject": "The Daily Hodl: ETH 2.0 is coming",
        "sender": "The Daily Hodl <newsletter@dailyhodl.com>",
        "body": "Read today's top crypto news. ETH 2.0 is just around the corner, and the market is reacting. Subscribe to our newsletter for more updates.",
    },
    {
        "name": "Referral Program Invite",
        "subject": "Invite friends and earn BTC",
        "sender": "Binance <do-not-reply@binance.com>",
        "body": "Share your referral link with friends. When they sign up and start trading, you'll both earn rewards. Join the Binance referral program today!",
    },
]


@pytest.mark.parametrize("email", NEGATIVE_EMAILS)
def test_regex_extractors_ignore_marketing(email):
    """Verify that specialized regex extractors do not match marketing emails."""
    results = registry.extract(email["subject"], email["sender"], email["body"])
    assert results is None or len(results) == 0, f"Extractor should have ignored {email['name']}"


@pytest.mark.parametrize("email", NEGATIVE_EMAILS)
def test_keyword_filtering_skips_marketing(email):
    """Verify that the preprocessing logic correctly identifies and skips marketing emails."""
    settings = HarvesterSettings(enable_preprocessing=True)
    extractor = EmailPurchaseExtractor(settings=settings)

    email_content = f"Subject: {email['subject']}\nFrom: {email['sender']}\n\n{email['body']}"

    # Test _should_skip_llm_analysis directly
    assert (
        extractor._should_skip_llm_analysis(email_content) is True
    ), f"Keyword filtering should have skipped {email['name']}"


@pytest.mark.parametrize("email", NEGATIVE_EMAILS)
def test_is_crypto_purchase_email_returns_false(email):
    """Verify that the full classification returns False for marketing emails."""
    # Mock LLM client just in case it's called (it shouldn't be if preprocessing works)
    mock_llm = MagicMock()
    mock_llm.generate_json.return_value.data = {
        "is_crypto_purchase": False,
        "confidence": 0.1,
        "reasoning": "Marketing",
    }

    settings = HarvesterSettings(enable_preprocessing=True)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm)

    email_content = f"Subject: {email['subject']}\nFrom: {email['sender']}\n\n{email['body']}"

    result = extractor.is_crypto_purchase_email(email_content)
    assert result is False, f"Email {email['name']} should NOT be classified as a crypto purchase"

    # If preprocessing is enabled, the LLM should not even be called for these cases
    assert (
        mock_llm.generate_json.call_count == 0
    ), f"LLM should not have been called for {email['name']} due to keyword filtering"


def test_mixed_content_handled_correctly():
    """Verify that an email containing both purchase and marketing terms is handled based on logic."""
    # This email contains "purchase" but also "newsletter"
    mixed_email = {
        "subject": "Your Weekly Newsletter and a note about your last purchase",
        "sender": "Coinbase <no-reply@coinbase.com>",
        "body": "Here is your weekly newsletter. Also, thank you for your recent purchase of BTC. Read more in the newsletter.",
    }

    settings = HarvesterSettings(enable_preprocessing=True)
    extractor = EmailPurchaseExtractor(settings=settings)
    email_content = f"Subject: {mixed_email['subject']}\nFrom: {mixed_email['sender']}\n\n{mixed_email['body']}"

    # In _is_likely_purchase_related:
    # has_purchase_keywords = True ("purchase")
    # has_non_purchase_patterns = True ("newsletter")
    # return has_purchase_keywords and not has_non_purchase_patterns => False

    assert extractor._is_likely_purchase_related(email_content) is False
    assert extractor.is_crypto_purchase_email(email_content) is False
