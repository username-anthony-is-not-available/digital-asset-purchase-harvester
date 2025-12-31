from tests.fixtures.emails import EMAIL_FIXTURES


def test_extract_purchase_info_coinbase(extractor_factory):
    """
    Tests that purchase info is correctly extracted from a Coinbase email.
    """
    email_content = EMAIL_FIXTURES["coinbase_purchase"]
    llm_responses = [
        {
            "total_spent": 100.0,
            "currency": "USD",
            "amount": 0.001,
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-01 12:00:00",
            "confidence": 0.9,
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.extract_purchase_info(email_content)

    assert result
    assert result["total_spent"] == 100.0
    assert result["currency"] == "USD"
    assert result["amount"] == 0.001
    assert result["item_name"] == "BTC"
    assert result["vendor"] == "Coinbase"
    assert result["purchase_date"] == "2024-01-01 12:00:00 UTC"


def test_extract_purchase_info_extraction_fails(extractor_factory):
    """
    Tests that extract_purchase_info returns None when extraction fails.
    """
    email_content = EMAIL_FIXTURES["binance_purchase"]
    llm_responses = [{"error": "extraction failed"}]
    extractor = extractor_factory(llm_responses)
    result = extractor.extract_purchase_info(email_content)
    assert result is None
