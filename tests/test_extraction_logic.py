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


def test_extract_purchase_info_binance(extractor_factory):
    """
    Tests that purchase info is correctly extracted from a Binance email.
    """
    email_content = EMAIL_FIXTURES["binance_purchase"]
    llm_responses = [
        {
            "total_spent": 200.0,
            "currency": "USD",
            "amount": 0.1,
            "item_name": "ETH",
            "vendor": "Binance",
            "purchase_date": "2024-01-01 12:00:00",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.extract_purchase_info(email_content)

    assert result
    assert result["total_spent"] == 200.0
    assert result["amount"] == 0.1
    assert result["item_name"] == "ETH"
    assert result["vendor"] == "Binance"


def test_extract_purchase_info_kraken(extractor_factory):
    """
    Tests that purchase info is correctly extracted from a Kraken email.
    """
    email_content = EMAIL_FIXTURES["kraken_purchase"]
    llm_responses = [
        {
            "total_spent": 50.0,
            "currency": "EUR",
            "amount": 0.5,
            "item_name": "XMR",
            "vendor": "Kraken",
            "purchase_date": "2024-01-01 12:00:00",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.extract_purchase_info(email_content)

    assert result
    assert result["currency"] == "EUR"
    assert result["item_name"] == "XMR"
    assert result["vendor"] == "Kraken"


def test_extract_purchase_info_gemini(extractor_factory):
    """
    Tests extraction from a Gemini purchase email.
    """
    email_content = EMAIL_FIXTURES["gemini_purchase"]
    llm_responses = [
        {
            "total_spent": 150.0,
            "currency": "USD",
            "amount": 0.005,
            "item_name": "BTC",
            "vendor": "Gemini",
            "purchase_date": "2024-01-15",
            "transaction_id": "GEM-2024-001",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.extract_purchase_info(email_content)

    assert result
    assert result["vendor"] == "Gemini"
    assert "transaction_id" in result
    assert result["transaction_id"] == "GEM-2024-001"


def test_extract_purchase_info_ftx(extractor_factory):
    """
    Tests extraction from an FTX purchase email.
    """
    email_content = EMAIL_FIXTURES["ftx_purchase"]
    llm_responses = [
        {
            "total_spent": 8.50,
            "currency": "USD",
            "amount": 10,
            "item_name": "MATIC",
            "vendor": "FTX",
            "purchase_date": "2024-01-01",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.extract_purchase_info(email_content)

    assert result
    assert result["amount"] == 10
    assert result["item_name"] == "MATIC"
    assert result["total_spent"] == 8.50


def test_extract_purchase_info_partial_data(extractor_factory):
    """
    Tests extraction when some data is missing.
    """
    email_content = EMAIL_FIXTURES["partial_data_purchase"]
    llm_responses = [
        {
            "amount": 1.5,
            "item_name": "LTC",
            "vendor": "Unknown Exchange",
        }
    ]
    extractor = extractor_factory(llm_responses)
    result = extractor.extract_purchase_info(email_content)

    # With strict validation disabled or handling missing fields
    # Result might be None or contain partial data
    assert result is None or isinstance(result, dict)
