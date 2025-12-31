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
            "total_spent": 62.50,
            "currency": "USD",
            "amount": 2.5,
            "item_name": "SOL",
            "vendor": "Crypto Exchange",
            "purchase_date": "2024-01-01T12:30:00Z",
        },
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.process_email(email_content)
    assert result["has_purchase"]
    assert result["purchase_info"]["total_spent"] == 62.50
