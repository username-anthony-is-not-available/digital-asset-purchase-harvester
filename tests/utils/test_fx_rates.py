from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

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
    mock_response.json.return_value = {"amount": 1.0, "base": "USD", "date": "2024-01-01", "rates": {"CAD": 1.3226}}
    mock_get.return_value = mock_response

    rate = fx_service.get_rate("2024-01-01", "USD", "CAD")
    assert rate == Decimal("1.3226")
    mock_get.assert_called_once_with("https://api.frankfurter.app/2024-01-01?from=USD&to=CAD", timeout=10.0)


@patch("httpx.get")
def test_fx_rate_caching(mock_get, fx_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {"CAD": 1.3226}}
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


def test_fx_rate_missing_args(fx_service):
    assert fx_service.get_rate(None, "USD", "CAD") is None
    assert fx_service.get_rate("2024-01-01", None, "CAD") is None
    assert fx_service.get_rate("2024-01-01", "USD", None) is None


@patch("httpx.get")
def test_fx_rate_not_found(mock_get, fx_service):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {}}  # CAD missing
    mock_get.return_value = mock_response

    rate = fx_service.get_rate("2024-01-01", "USD", "CAD")
    assert rate is None


@patch("httpx.get")
def test_fx_rate_retries(mock_get, fx_service):
    import httpx

    # First call fails, second succeeds
    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {"rates": {"CAD": 1.3}}

    mock_get.side_effect = [httpx.RequestError("error"), mock_response_success]

    # Mock time.sleep to speed up test
    with patch("time.sleep"):
        rate = fx_service.get_rate("2024-01-02", "USD", "CAD", max_retries=2)
        assert rate == Decimal("1.3")
        assert mock_get.call_count == 2


@patch("httpx.get")
def test_fx_rate_retries_all_fail(mock_get, fx_service):
    import httpx

    mock_get.side_effect = httpx.RequestError("error")

    with patch("time.sleep"):
        rate = fx_service.get_rate("2024-01-03", "USD", "CAD", max_retries=2)
        assert rate is None
        assert mock_get.call_count == 2


@patch("httpx.get")
def test_fx_rate_http_status_error(mock_get, fx_service):
    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("404", request=None, response=mock_response)
    mock_get.return_value = mock_response

    with patch("time.sleep"):
        rate = fx_service.get_rate("2024-01-04", "USD", "CAD", max_retries=1)
        assert rate is None


def test_fx_rate_cache_eviction(fx_service):
    fx_service.max_cache_size = 2
    # Fill cache
    with patch("httpx.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        mock_response.json.return_value = {"rates": {"CAD": 1.1}}
        fx_service.get_rate("2024-01-01", "USD", "CAD")

        mock_response.json.return_value = {"rates": {"CAD": 1.2}}
        fx_service.get_rate("2024-01-02", "USD", "CAD")

        assert len(fx_service._cache) == 2

        # This should evict 2024-01-01
        mock_response.json.return_value = {"rates": {"CAD": 1.3}}
        fx_service.get_rate("2024-01-03", "USD", "CAD")

        assert len(fx_service._cache) == 2
        assert "2024-01-01_USD_CAD" not in fx_service._cache
