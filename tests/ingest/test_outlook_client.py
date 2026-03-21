from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from digital_asset_harvester.ingest.outlook_client import OutlookClient


@pytest.fixture
def mock_outlook_responses():
    """Fixture for mocking httpx Client responses."""
    with patch("httpx.Client.get") as mock_get:
        yield mock_get


@patch("digital_asset_harvester.ingest.outlook_client.get_outlook_credentials")
def test_outlook_client_initialization(mock_get_credentials):
    """Tests that the Outlook client is initialized correctly."""
    mock_get_credentials.return_value = "test_token"
    client = OutlookClient("client_id", "authority")
    assert client.token == "test_token"
    assert client.headers["Authorization"] == "Bearer test_token"
    mock_get_credentials.assert_called_once()


@patch("digital_asset_harvester.ingest.outlook_client.get_outlook_credentials")
def test_search_emails(mock_get_credentials, mock_outlook_responses):
    """Tests that the search_emails method works correctly."""
    mock_get_credentials.return_value = "test_token"

    # Mock message list response
    mock_list_response = MagicMock()
    mock_list_response.json.return_value = {"value": [{"id": "msg1"}, {"id": "msg2"}]}
    mock_list_response.raise_for_status.return_value = None

    # Mock MIME content responses
    mock_mime_response1 = MagicMock()
    mock_mime_response1.content = (
        b"Subject: Test 1\r\nFrom: test1@example.com\r\nDate: Mon, 1 Jan 2024 00:00:00 +0000\r\n\r\nBody 1"
    )
    mock_mime_response1.raise_for_status.return_value = None

    mock_mime_response2 = MagicMock()
    mock_mime_response2.content = (
        b"Subject: Test 2\r\nFrom: test2@example.com\r\nDate: Tue, 2 Jan 2024 00:00:00 +0000\r\n\r\nBody 2"
    )
    mock_mime_response2.raise_for_status.return_value = None

    mock_outlook_responses.side_effect = [mock_list_response, mock_mime_response1, mock_mime_response2]

    client = OutlookClient("client_id", "authority")
    emails = list(client.search_emails("test query"))

    assert len(emails) == 2
    assert emails[0]["subject"] == "Test 1"
    assert emails[1]["subject"] == "Test 2"
    assert emails[0]["sender"] == "test1@example.com"


@patch("digital_asset_harvester.ingest.outlook_client.get_outlook_credentials")
def test_search_emails_pagination(mock_get_credentials, mock_outlook_responses):
    """Tests that the search_emails method handles pagination correctly."""
    mock_get_credentials.return_value = "test_token"

    # Page 1
    mock_list_response1 = MagicMock()
    mock_list_response1.json.return_value = {
        "value": [{"id": "msg1"}],
        "@odata.nextLink": "https://graph.microsoft.com/v1.0/me/messages?$skip=1",
    }
    mock_list_response1.raise_for_status.return_value = None

    # MIME for Page 1
    mock_mime_response1 = MagicMock()
    mock_mime_response1.content = b"Subject: Test 1\r\n\r\nBody 1"
    mock_mime_response1.raise_for_status.return_value = None

    # Page 2
    mock_list_response2 = MagicMock()
    mock_list_response2.json.return_value = {"value": [{"id": "msg2"}]}
    mock_list_response2.raise_for_status.return_value = None

    # MIME for Page 2
    mock_mime_response2 = MagicMock()
    mock_mime_response2.content = b"Subject: Test 2\r\n\r\nBody 2"
    mock_mime_response2.raise_for_status.return_value = None

    mock_outlook_responses.side_effect = [
        mock_list_response1,
        mock_mime_response1,
        mock_list_response2,
        mock_mime_response2,
    ]

    client = OutlookClient("client_id", "authority")
    emails = list(client.search_emails("test query"))

    assert len(emails) == 2
    assert emails[0]["subject"] == "Test 1"
    assert emails[1]["subject"] == "Test 2"
    assert mock_outlook_responses.call_count == 4


@patch("digital_asset_harvester.ingest.outlook_client.get_outlook_credentials")
def test_search_emails_http_error(mock_get_credentials, mock_outlook_responses):
    """Tests that the search_emails method handles HTTP errors gracefully."""
    mock_get_credentials.return_value = "test_token"

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Error", request=MagicMock(), response=MagicMock()
    )
    mock_outlook_responses.return_value = mock_response

    client = OutlookClient("client_id", "authority")
    emails = list(client.search_emails("test query"))

    assert len(emails) == 0
