"""Tests for the Koinly API client."""

import pytest
from unittest.mock import Mock, patch

from digital_asset_harvester.output.koinly_api_client import (
    KoinlyApiClient,
    KoinlyApiError,
    KoinlyAuthenticationError,
)


def test_koinly_api_client_init():
    """Test that KoinlyApiClient initializes correctly."""
    client = KoinlyApiClient(
        api_key="test_key",
        api_url="https://api.test.com",
        timeout=60,
        max_retries=5,
    )
    
    assert client.api_key == "test_key"
    assert client.api_url == "https://api.test.com"
    assert client.timeout == 60
    assert client.max_retries == 5


def test_koinly_api_client_init_requires_api_key():
    """Test that KoinlyApiClient requires an API key."""
    with pytest.raises(KoinlyAuthenticationError, match="API key is required"):
        KoinlyApiClient(api_key="")


def test_koinly_api_client_context_manager():
    """Test that KoinlyApiClient works as a context manager."""
    with KoinlyApiClient(api_key="test_key") as client:
        assert client.api_key == "test_key"
    
    # Client should be closed after exiting context
    assert client._client is None


@patch("digital_asset_harvester.output.koinly_api_client.httpx.Client")
def test_koinly_api_client_test_connection_success(mock_client_class):
    """Test successful API connection test."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    client = KoinlyApiClient(api_key="test_key")
    result = client.test_connection()
    
    assert result is True
    mock_client.get.assert_called_once_with("https://api.koinly.io/api/v1/account")


@patch("digital_asset_harvester.output.koinly_api_client.httpx.Client")
def test_koinly_api_client_test_connection_auth_failure(mock_client_class):
    """Test API connection test with authentication failure."""
    mock_response = Mock()
    mock_response.status_code = 401
    
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    client = KoinlyApiClient(api_key="invalid_key")
    
    with pytest.raises(KoinlyAuthenticationError, match="Invalid API key"):
        client.test_connection()


@patch("digital_asset_harvester.output.koinly_api_client.httpx.Client")
def test_koinly_api_client_upload_transactions_success(mock_client_class):
    """Test successful transaction upload."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success", "uploaded": 2}
    mock_response.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    client = KoinlyApiClient(api_key="test_key")
    
    transactions = [
        {
            "total_spent": "100",
            "currency": "USD",
            "amount": "0.01",
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-10",
        },
        {
            "total_spent": "200",
            "currency": "USD",
            "amount": "0.02",
            "item_name": "ETH",
            "vendor": "Binance",
            "purchase_date": "2024-01-11",
        },
    ]
    
    result = client.upload_transactions(transactions)
    
    assert result["status"] == "success"
    assert result["uploaded"] == 2
    mock_client.post.assert_called_once()


@patch("digital_asset_harvester.output.koinly_api_client.httpx.Client")
def test_koinly_api_client_upload_transactions_empty_list(mock_client_class):
    """Test uploading empty transaction list."""
    mock_client = Mock()
    mock_client_class.return_value = mock_client
    
    client = KoinlyApiClient(api_key="test_key")
    result = client.upload_transactions([])
    
    assert result["status"] == "success"
    assert result["uploaded"] == 0
    mock_client.post.assert_not_called()


@patch("digital_asset_harvester.output.koinly_api_client.httpx.Client")
def test_koinly_api_client_upload_transactions_with_wallet_id(mock_client_class):
    """Test transaction upload with wallet ID."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_response.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    client = KoinlyApiClient(api_key="test_key")
    
    transactions = [
        {
            "total_spent": "100",
            "currency": "USD",
            "amount": "0.01",
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-10",
        }
    ]
    
    result = client.upload_transactions(transactions, wallet_id="wallet123")
    
    # Verify wallet_id was included in the payload
    call_args = mock_client.post.call_args
    payload = call_args[1]["json"]
    assert payload["transactions"][0]["wallet_id"] == "wallet123"


@patch("digital_asset_harvester.output.koinly_api_client.httpx.Client")
def test_koinly_api_client_upload_transactions_auth_error(mock_client_class):
    """Test transaction upload with authentication error."""
    mock_response = Mock()
    mock_response.status_code = 401
    
    mock_client = Mock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    client = KoinlyApiClient(api_key="invalid_key")
    
    transactions = [{"total_spent": "100"}]
    
    with pytest.raises(KoinlyAuthenticationError, match="Invalid API key"):
        client.upload_transactions(transactions)


@patch("digital_asset_harvester.output.koinly_api_client.httpx.Client")
def test_koinly_api_client_upload_transactions_retry_on_server_error(mock_client_class):
    """Test that client retries on server errors."""
    import httpx
    
    # First two attempts fail with 500, third succeeds
    mock_response_fail = Mock()
    mock_response_fail.status_code = 500
    mock_request = Mock()
    
    def raise_http_error():
        raise httpx.HTTPStatusError(
            "Server error",
            request=mock_request,
            response=mock_response_fail
        )
    
    mock_response_fail.raise_for_status.side_effect = raise_http_error
    
    mock_response_success = Mock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {"status": "success"}
    mock_response_success.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.post.side_effect = [
        mock_response_fail,
        mock_response_fail,
        mock_response_success,
    ]
    mock_client_class.return_value = mock_client
    
    client = KoinlyApiClient(api_key="test_key", max_retries=3)
    
    transactions = [{"total_spent": "100"}]
    result = client.upload_transactions(transactions)
    
    assert result["status"] == "success"
    assert mock_client.post.call_count == 3


@patch("digital_asset_harvester.output.koinly_api_client.httpx.Client")
def test_koinly_api_client_get_wallets(mock_client_class):
    """Test retrieving wallets from API."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "wallets": [
            {"id": "wallet1", "name": "My Wallet"},
            {"id": "wallet2", "name": "Trading Wallet"},
        ]
    }
    mock_response.raise_for_status = Mock()
    
    mock_client = Mock()
    mock_client.get.return_value = mock_response
    mock_client_class.return_value = mock_client
    
    client = KoinlyApiClient(api_key="test_key")
    wallets = client.get_wallets()
    
    assert len(wallets) == 2
    assert wallets[0]["id"] == "wallet1"
    assert wallets[1]["name"] == "Trading Wallet"
    mock_client.get.assert_called_once_with("https://api.koinly.io/api/v1/wallets")


def test_koinly_api_client_format_transactions_for_api():
    """Test transaction formatting for API."""
    client = KoinlyApiClient(api_key="test_key")
    
    transactions = [
        {
            "total_spent": "123.45",
            "currency": "USD",
            "amount": "0.01",
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-10 10:00:00",
        }
    ]
    
    formatted = client._format_transactions_for_api(transactions)
    
    assert "transactions" in formatted
    assert "source" in formatted
    assert formatted["source"] == "digital-asset-harvester"
    assert len(formatted["transactions"]) == 1
    
    txn = formatted["transactions"][0]
    assert txn["timestamp"] == "2024-01-10 10:00:00"
    assert txn["sent_amount"] == "123.45"
    assert txn["sent_currency"] == "USD"
    assert txn["received_amount"] == "0.01"
    assert txn["received_currency"] == "BTC"
    assert txn["label"] == "buy"
    assert "Coinbase" in txn["description"]
