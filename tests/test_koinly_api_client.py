"""Tests for Koinly API client."""

import pytest
from digital_asset_harvester.integrations.koinly_api_client import (
    KoinlyApiClient,
    KoinlyApiError,
    KoinlyTransaction,
)


def test_koinly_transaction_creation():
    """Test creating a KoinlyTransaction."""
    tx = KoinlyTransaction(
        date="2024-01-15T10:30:00Z",
        sent_amount=100.0,
        sent_currency="USD",
        received_amount=0.002,
        received_currency="BTC",
        description="Purchase from Coinbase",
        tx_hash="abc123",
        label="purchase",
    )

    assert tx.date == "2024-01-15T10:30:00Z"
    assert tx.sent_amount == 100.0
    assert tx.sent_currency == "USD"
    assert tx.received_amount == 0.002
    assert tx.received_currency == "BTC"


def test_koinly_api_client_requires_api_key():
    """Test that API client requires an API key."""
    with pytest.raises(ValueError, match="API key is required"):
        KoinlyApiClient(api_key="", portfolio_id="test-portfolio")


def test_koinly_api_client_requires_portfolio_id():
    """Test that API client requires a portfolio ID."""
    with pytest.raises(ValueError, match="portfolio ID is required"):
        KoinlyApiClient(api_key="test-key", portfolio_id="")


def test_koinly_api_client_initialization():
    """Test successful initialization of API client."""
    client = KoinlyApiClient(
        api_key="test-key",
        portfolio_id="test-portfolio",
    )

    assert client.api_key == "test-key"
    assert client.portfolio_id == "test-portfolio"
    assert client.base_url == "https://api.koinly.io/v1"
    assert client.timeout == 30


def test_koinly_api_client_custom_base_url():
    """Test API client with custom base URL."""
    client = KoinlyApiClient(
        api_key="test-key",
        portfolio_id="test-portfolio",
        base_url="https://custom.api.com/v2/",
    )

    assert client.base_url == "https://custom.api.com/v2"


def test_koinly_api_client_context_manager():
    """Test API client as context manager."""
    with KoinlyApiClient(
        api_key="test-key",
        portfolio_id="test-portfolio",
    ) as client:
        assert client.api_key == "test-key"

    # After context, client should be closed
    assert client._client is None


def test_koinly_api_not_available():
    """Test that Koinly API reports as not available."""
    assert KoinlyApiClient.is_available() is False


def test_koinly_api_test_connection_raises_error():
    """Test that test_connection raises appropriate error."""
    client = KoinlyApiClient(
        api_key="test-key",
        portfolio_id="test-portfolio",
    )

    with pytest.raises(KoinlyApiError, match="does not currently offer a public API"):
        client.test_connection()


def test_koinly_api_upload_transaction_raises_error():
    """Test that upload_transaction raises appropriate error."""
    client = KoinlyApiClient(
        api_key="test-key",
        portfolio_id="test-portfolio",
    )

    tx = KoinlyTransaction(
        date="2024-01-15T10:30:00Z",
        sent_amount=100.0,
        sent_currency="USD",
        received_amount=0.002,
        received_currency="BTC",
    )

    with pytest.raises(KoinlyApiError, match="does not currently offer a public API"):
        client.upload_transaction(tx)


def test_koinly_api_upload_transactions_raises_error():
    """Test that upload_transactions raises appropriate error."""
    client = KoinlyApiClient(
        api_key="test-key",
        portfolio_id="test-portfolio",
    )

    transactions = [
        KoinlyTransaction(
            date="2024-01-15T10:30:00Z",
            sent_amount=100.0,
            sent_currency="USD",
        )
    ]

    with pytest.raises(KoinlyApiError, match="does not currently offer a public API"):
        client.upload_transactions(transactions)


def test_koinly_api_upload_purchases_raises_error():
    """Test that upload_purchases raises appropriate error."""
    client = KoinlyApiClient(
        api_key="test-key",
        portfolio_id="test-portfolio",
    )

    purchases = [
        {
            "total_spent": 100,
            "currency": "USD",
            "amount": 0.002,
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-15T10:30:00Z",
        }
    ]

    with pytest.raises(KoinlyApiError, match="does not currently offer a public API"):
        client.upload_purchases(purchases)


def test_koinly_api_get_setup_instructions():
    """Test getting setup instructions."""
    instructions = KoinlyApiClient.get_setup_instructions()

    assert "Koinly API Setup" in instructions
    assert "does not currently provide a public API" in instructions
    assert "digital-asset-harvester" in instructions
    assert "--output-format koinly" in instructions
