import pytest
from unittest.mock import patch, MagicMock
from digital_asset_harvester.web.api import tasks
import uvicorn
from digital_asset_harvester.web.main import app
import threading
import time


@pytest.fixture(scope="session")
def live_server_url():
    """Provides the full URL for the running uvicorn server."""
    return "http://localhost:8000"


@pytest.fixture(scope="session", autouse=True)
def start_live_server(live_server_url):
    """Starts the uvicorn server in a separate thread."""
    server = uvicorn.Server(uvicorn.Config(app, host="localhost", port=8000, log_level="info"))
    thread = threading.Thread(target=server.run)
    thread.daemon = True
    thread.start()
    time.sleep(2)  # Give the server a moment to start
    yield
    # No explicit shutdown needed for daemon threads


@pytest.fixture(scope="function", autouse=True)
def mock_process_mbox_playwright():
    """
    Mocks the backend mbox processing for Playwright tests.
    """

    def mock_task(task_id, temp_path, logger_factory):
        tasks[task_id] = {
            "status": "complete",
            "result": [
                {
                    "email_subject": "Your Coinbase purchase of 0.001 BTC",
                    "vendor": "Coinbase",
                    "currency": "USD",
                    "amount": "100.00",
                    "purchase_date": "2023-11-12",
                    "transaction_id": "N/A",
                    "crypto_currency": "BTC",
                    "crypto_amount": "0.001",
                    "confidence_score": "0.95",
                },
                {
                    "email_subject": "Your order to buy 0.1 ETH has been filled",
                    "vendor": "Binance",
                    "currency": "USD",
                    "amount": "200.00",
                    "purchase_date": "2023-11-12",
                    "transaction_id": "N/A",
                    "crypto_currency": "ETH",
                    "crypto_amount": "0.1",
                    "confidence_score": "0.95",
                },
            ],
        }

    with patch("digital_asset_harvester.web.api.process_mbox_file", side_effect=mock_task) as mock:
        yield mock
