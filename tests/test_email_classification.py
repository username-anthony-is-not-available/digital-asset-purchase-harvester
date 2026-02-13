from tests.fixtures.emails import EMAIL_FIXTURES


def test_process_email_non_purchase(extractor_factory):
    """
    Tests that a non-purchase email is correctly classified.
    """
    email_content = EMAIL_FIXTURES["non_purchase"]
    llm_responses = [
        {
            "is_crypto_purchase": False,
            "confidence": 0.9,
            "reasoning": "Price alert",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.process_email(email_content)
    assert not result["has_purchase"]


def test_process_email_purchase(extractor_factory):
    """
    Tests that a purchase email is correctly classified.
    """
    email_content = EMAIL_FIXTURES["complex_purchase"]
    llm_responses = [
        {
            "is_crypto_purchase": True,
            "confidence": 0.99,
            "reasoning": "The email contains keywords like 'purchase' and 'order'.",
        },
        {
            "transactions": [
                {
                    "total_spent": 62.50,
                    "currency": "USD",
                    "amount": 2.5,
                    "item_name": "SOL",
                    "vendor": "Crypto Exchange",
                    "purchase_date": "2024-01-01T12:30:00Z",
                }
            ]
        },
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.process_email(email_content)
    assert result["has_purchase"]
    assert result["purchases"][0]["total_spent"] == 62.50


def test_process_email_marketing(extractor_factory):
    """
    Tests that a marketing email is correctly classified as non-purchase.
    """
    email_content = EMAIL_FIXTURES["marketing_email"]
    llm_responses = [
        {
            "is_crypto_purchase": False,
            "confidence": 0.95,
            "reasoning": "Marketing email about hardware wallet",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.process_email(email_content)
    assert not result["has_purchase"]


def test_process_email_security_alert(extractor_factory):
    """
    Tests that a security alert is correctly classified as non-purchase.
    """
    email_content = EMAIL_FIXTURES["security_alert"]
    llm_responses = [
        {
            "is_crypto_purchase": False,
            "confidence": 0.98,
            "reasoning": "Security notification, not a purchase",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.process_email(email_content)
    assert not result["has_purchase"]


def test_process_email_gemini_purchase(extractor_factory):
    """
    Tests that a Gemini purchase email is correctly classified.
    """
    email_content = EMAIL_FIXTURES["gemini_purchase"]
    llm_responses = [
        {
            "is_crypto_purchase": True,
            "confidence": 0.95,
            "reasoning": "Order confirmation from Gemini",
        },
        {
            "transactions": [
                {
                    "total_spent": 150.0,
                    "currency": "USD",
                    "amount": 0.005,
                    "item_name": "BTC",
                    "vendor": "Gemini",
                    "purchase_date": "2024-01-15T00:00:00Z",
                    "transaction_id": "GEM-2024-001",
                }
            ]
        },
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.process_email(email_content)
    assert result["has_purchase"]
    assert result["purchases"][0]["vendor"] == "Gemini"


def test_process_email_withdrawal_not_purchase(extractor_factory):
    """
    Tests that a withdrawal email is not classified as a purchase.
    """
    email_content = EMAIL_FIXTURES["withdrawal_email"]
    llm_responses = [
        {
            "is_crypto_purchase": False,
            "confidence": 0.9,
            "reasoning": "Withdrawal, not a purchase",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.process_email(email_content)
    assert not result["has_purchase"]


def test_process_email_failed_purchase(extractor_factory):
    """
    Tests that a failed purchase is correctly classified as non-purchase.
    """
    email_content = EMAIL_FIXTURES["failed_purchase"]
    llm_responses = [
        {
            "is_crypto_purchase": False,
            "confidence": 0.85,
            "reasoning": "Purchase attempt failed",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.process_email(email_content)
    assert not result["has_purchase"]


def test_process_email_newsletter(extractor_factory):
    """
    Tests that a crypto newsletter is correctly classified as non-purchase.
    """
    email_content = EMAIL_FIXTURES["newsletter_crypto"]
    llm_responses = [
        {
            "is_crypto_purchase": False,
            "confidence": 0.92,
            "reasoning": "Newsletter content, no transaction",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.process_email(email_content)
    assert not result["has_purchase"]
