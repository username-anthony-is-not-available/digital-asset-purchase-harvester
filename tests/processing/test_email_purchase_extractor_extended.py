import pytest
from unittest.mock import MagicMock, mock_open
from decimal import Decimal
from digital_asset_harvester.processing.email_purchase_extractor import EmailPurchaseExtractor, PurchaseInfo
from digital_asset_harvester.config import HarvesterSettings
from digital_asset_harvester.llm.ollama_client import LLMError

@pytest.fixture
def mock_llm_client():
    client = MagicMock()
    # Mock generate_json response
    result = MagicMock()
    result.data = {
        "is_crypto_purchase": True,
        "confidence": 0.9,
        "reasoning": "Test reasoning",
        "transactions": [
            {
                "total_spent": 100.0,
                "currency": "USD",
                "amount": 0.001,
                "item_name": "BTC",
                "vendor": "Coinbase",
                "purchase_date": "2024-01-01 12:00:00 UTC",
                "transaction_type": "buy",
                "confidence": 0.95
            }
        ]
    }
    result.metadata = {"cached": False, "fallback_used": False}
    client.generate_json.return_value = result
    return client

@pytest.fixture
def extractor(mock_llm_client):
    settings = HarvesterSettings(
        enable_preprocessing=True,
        enable_pii_scrubbing=True,
        enable_currency_conversion=True,
        base_fiat_currency="CAD",
        llm_max_retries=1,
        min_confidence_threshold=0.2,
        enable_regex_extractors=True
    )
    return EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)

def test_load_custom_keywords(mocker):
    m = mock_open(read_data="custom_kw1\ncustom_kw2\n# comment\n  \n")
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", m)

    settings = HarvesterSettings(custom_keywords_file="keywords.txt")
    extractor = EmailPurchaseExtractor(settings=settings)

    assert "custom_kw1" in extractor._exchanges_pattern.pattern
    assert "custom_kw2" in extractor._terms_pattern.pattern

def test_extract_email_metadata_fallback(extractor):
    content = "Subject: Test Subject\nFrom: sender@test.com\n\nBody content here"
    metadata = extractor._extract_email_metadata(content)
    assert metadata["subject"] == "Test Subject"
    assert metadata["sender"] == "sender@test.com"
    assert metadata["body"] == "Body content here"

def test_extract_email_metadata_cli_body(extractor):
    content = "Subject: Test\nFrom: test\nBody: This is the real body"
    metadata = extractor._extract_email_metadata(content)
    assert metadata["body"] == "This is the real body"

def test_is_likely_crypto_related(extractor):
    # Matches exchange
    assert extractor._is_likely_crypto_related("From: Coinbase\nSubject: Hello") is True
    # Matches term
    assert extractor._is_likely_crypto_related("From: someone\nSubject: Bitcoin") is True
    # No match
    assert extractor._is_likely_crypto_related("From: someone\nSubject: Hello") is False

def test_is_likely_purchase_related(extractor):
    # Matches purchase keyword
    assert extractor._is_likely_purchase_related("Subject: Your purchase") is True
    # Matches non-purchase pattern
    assert extractor._is_likely_purchase_related("Subject: Your purchase password reset") is False
    # No match
    assert extractor._is_likely_purchase_related("Subject: Hello") is False

def test_should_skip_llm_analysis(extractor):
    # Should skip if non-purchase
    assert extractor._should_skip_llm_analysis("Subject: password reset") is True
    # Should skip if not crypto related
    assert extractor._should_skip_llm_analysis("Subject: Pizza order") is True
    # Should NOT skip if looks like crypto purchase
    assert extractor._should_skip_llm_analysis("From: Coinbase\nSubject: Your purchase") is False

def test_process_email_full_flow(extractor, mocker):
    # Mock FX service
    mock_fx = mocker.patch("digital_asset_harvester.processing.email_purchase_extractor.fx_service")
    mock_fx.get_rate.return_value = Decimal("1.35")

    email_content = "From: Coinbase\nSubject: Your purchase of 0.001 BTC\n\nYou bought 0.001 BTC for 100 USD."

    result = extractor.process_email(email_content)

    assert result["has_purchase"] is True
    assert len(result["purchases"]) == 1
    purchase = result["purchases"][0]
    assert purchase["item_name"] == "BTC"
    assert purchase["total_spent"] == 100.0
    assert purchase["currency"] == "USD"
    # Currency conversion checked
    assert purchase["fiat_amount_base"] == 135.0
    assert purchase["confidence"] > 0.5

def test_process_email_no_purchase(extractor):
    extractor.llm_client.generate_json.return_value.data = {"is_crypto_purchase": False}

    email_content = "From: Coinbase\nSubject: Hello"
    result = extractor.process_email(email_content)

    assert result["has_purchase"] is False

def test_process_email_no_transactions_field(extractor):
    # Classified as purchase but extraction returns dict without transactions field
    extractor.llm_client.generate_json.side_effect = [
        MagicMock(data={"is_crypto_purchase": True, "confidence": 0.9}),
        MagicMock(data={})
    ]

    email_content = "From: Coinbase\nSubject: Your purchase"
    result = extractor.process_email(email_content)

    assert result["has_purchase"] is False

def test_extract_purchase_info_regex(extractor, mocker):
    mock_extract = mocker.patch("digital_asset_harvester.processing.extractors.registry.extract")
    mock_extract.return_value = [{
        "total_spent": 50.0,
        "currency": "USD",
        "amount": 0.5,
        "item_name": "ETH",
        "vendor": "Kraken",
        "purchase_date": "2024-01-02 12:00:00 UTC",
        "transaction_type": "buy"
    }]

    results = extractor.extract_purchase_info("Some email content")
    assert len(results) == 1
    assert results[0]["item_name"] == "ETH"
    assert results[0]["extraction_method"] == "regex"

def test_process_extracted_transactions_staking(extractor):
    transactions = [{
        "amount": 10.0,
        "item_name": "SOL",
        "vendor": "Kraken",
        "transaction_type": "staking_reward",
        "purchase_date": "2024-01-03 12:00:00 UTC"
    }]
    processed = extractor._process_extracted_transactions(transactions)
    assert len(processed) == 1
    assert processed[0]["item_name"] == "SOL"

def test_validate_purchase_data_invalid(extractor):
    invalid_data = {
        "total_spent": -100,  # Invalid
        "currency": "USD",
        "amount": 1.0,
        "item_name": "BTC",
        "vendor": "Coinbase"
    }
    is_valid, errors = extractor._validate_purchase_data(invalid_data)
    assert is_valid is False
    assert any("total_spent" in e for e in errors)

def test_process_email_validation_failure(extractor):
    # Classified as purchase, but extracted data is invalid
    extractor.llm_client.generate_json.side_effect = [
        MagicMock(data={"is_crypto_purchase": True, "confidence": 0.9}),
        MagicMock(data={"transactions": [{
            "total_spent": -100,
            "currency": "USD",
            "amount": 1.0,
            "item_name": "BTC",
            "vendor": "Coinbase",
            "confidence": 0.9
        }]})
    ]

    result = extractor.process_email("From: Coinbase\nSubject: Your purchase")
    assert result["has_purchase"] is False

def test_is_crypto_purchase_email_low_confidence(extractor):
    extractor.llm_client.generate_json.return_value.data = {
        "is_crypto_purchase": True,
        "confidence": 0.1,  # Below default 0.6
        "reasoning": "Unsure"
    }
    assert extractor.is_crypto_purchase_email("Subject: maybe purchase") is False

def test_process_extracted_dates_invalid(extractor):
    transactions = [{"purchase_date": "invalid-date", "item_name": "BTC"}]
    processed = extractor._process_extracted_dates(transactions)
    assert processed[0]["purchase_date"] is not None

def test_scrub_pii_if_enabled(extractor):
    content = "My email is test@example.com"
    scrubbed = extractor._scrub_pii_if_enabled(content)
    assert "[EMAIL]" in scrubbed
    # Test caching
    scrubbed2 = extractor._scrub_pii_if_enabled(content)
    assert scrubbed == scrubbed2

def test_process_email_pydantic_error(extractor, mocker):
    # This should trigger the generic Exception catch in process_email
    mocker.patch("digital_asset_harvester.validation.PurchaseRecord.model_validate", side_effect=Exception("pydantic error"))

    email_content = "From: Coinbase\nSubject: Your purchase"
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is False
    assert any("Error processing extracted purchase: pydantic error" in note for note in result["processing_notes"])

def test_is_crypto_purchase_email_llm_error(extractor):
    extractor.llm_client.generate_json.side_effect = LLMError("llm down")
    assert extractor.is_crypto_purchase_email("Subject: buy btc") is False

def test_extract_purchase_info_llm_error(extractor):
    extractor.llm_client.generate_json.side_effect = LLMError("llm down")
    assert extractor.extract_purchase_info("Subject: buy btc") == []

def test_extract_purchase_info_malformed_response(extractor):
    # Transactions is not a list
    extractor.llm_client.generate_json.return_value.data = {"transactions": "not a list"}
    assert extractor.extract_purchase_info("Subject: buy btc") == []

def test_process_email_extraction_failed(extractor):
    # Classified as purchase but extraction returns nothing
    extractor.llm_client.generate_json.side_effect = [
        MagicMock(data={"is_crypto_purchase": True, "confidence": 0.9}),
        MagicMock(data={"transactions": []})
    ]

    email_content = "From: Coinbase\nSubject: Your purchase"
    result = extractor.process_email(email_content)

    assert result["has_purchase"] is False
