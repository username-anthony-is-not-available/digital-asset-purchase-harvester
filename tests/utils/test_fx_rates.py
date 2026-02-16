import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from digital_asset_harvester.utils.fx_rates import FXRateService

@pytest.fixture
def fx_service():
    return FXRateService()

def test_fx_rate_same_currency(fx_service):
    rate = fx_service.get_rate("2024-01-01", "USD", "USD")
    assert rate == Decimal("1.0")

@patch("httpx.get")
def test_fx_rate_success(mock_get, fx_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "amount": 1.0,
        "base": "USD",
        "date": "2024-01-01",
        "rates": {"CAD": 1.3226}
    }
    mock_get.return_value = mock_response

    rate = fx_service.get_rate("2024-01-01", "USD", "CAD")
    assert rate == Decimal("1.3226")
    mock_get.assert_called_once_with("https://api.frankfurter.app/2024-01-01?from=USD&to=CAD", timeout=10.0)

@patch("httpx.get")
def test_fx_rate_caching(mock_get, fx_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "rates": {"CAD": 1.3226}
    }
    mock_get.return_value = mock_response

    # First call
    rate1 = fx_service.get_rate("2024-01-01", "USD", "CAD")
    # Second call
    rate2 = fx_service.get_rate("2024-01-01", "USD", "CAD")

    assert rate1 == rate2 == Decimal("1.3226")
    assert mock_get.call_count == 1

def test_fx_rate_invalid_date(fx_service):
    rate = fx_service.get_rate("not-a-date", "USD", "CAD")
    assert rate is None

@patch("httpx.get")
def test_fx_rate_api_error(mock_get, fx_service):
    mock_get.side_effect = Exception("API Down")
    rate = fx_service.get_rate("2024-01-01", "USD", "CAD")
    assert rate is None
