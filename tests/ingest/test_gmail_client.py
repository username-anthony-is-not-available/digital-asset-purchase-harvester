from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from digital_asset_harvester.ingest.gmail_client import GmailClient


@pytest.fixture
def mock_gmail_service():
    """Fixture for mocking the Gmail API service."""
    with patch("googleapiclient.discovery.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        yield mock_service


@patch("digital_asset_harvester.ingest.gmail_client.get_gmail_credentials")
def test_gmail_client_initialization(mock_get_credentials, mock_gmail_service):
    """Tests that the Gmail client is initialized correctly."""
    mock_get_credentials.return_value = MagicMock()
    client = GmailClient()
    assert client.service is not None


@patch("digital_asset_harvester.ingest.gmail_client.get_gmail_credentials")
def test_search_emails(mock_get_credentials, mock_gmail_service):
    """Tests that the search_emails method works correctly."""
    mock_get_credentials.return_value = MagicMock()

    mock_gmail_service.users().messages().list.return_value.execute.return_value = {
        "messages": [{"id": "1"}, {"id": "2"}]
    }
    mock_gmail_service.users().messages().get.return_value.execute.side_effect = [
        {"raw": "U3ViamVjdDogVGVzdCBFbWFpbCAxCkZyb206IHRlc3QxQGV4YW1wbGUuY29tCgpCb2R5IDE="},
        {"raw": "U3ViamVjdDogVGVzdCBFbWFpbCAyCkZyb206IHRlc3QyQGV4YW1wbGUuY29tCgpCb2R5IDI="},
    ]

    with patch("digital_asset_harvester.ingest.gmail_client.build") as mock_build:
        mock_build.return_value = mock_gmail_service
        client = GmailClient()
        emails = list(client.search_emails("test query"))

    assert len(emails) == 2
    assert emails[0]["subject"] == "Test Email 1"
    assert emails[1]["subject"] == "Test Email 2"


@patch("digital_asset_harvester.ingest.gmail_client.get_gmail_credentials")
def test_search_emails_multipart(mock_get_credentials, mock_gmail_service):
    """Tests that the search_emails method works correctly with multipart emails."""
    mock_get_credentials.return_value = MagicMock()

    mock_gmail_service.users().messages().list.return_value.execute.return_value = {"messages": [{"id": "1"}]}
    mock_gmail_service.users().messages().get.return_value.execute.return_value = {
        "raw": "RnJvbTogdGVzdEBleGFtcGxlLmNvbQpUbzogcmVjaXBpZW50QGV4YW1wbGUuY29tClN1YmplY3Q6IE11bHRpcGFydCBFbWFpbApNSU1FLVZlcnNpb246IDEuMApDb250ZW50LVR5cGU6IG11bHRpcGFydC9hbHRlcm5hdGl2ZTsgYm91bmRhcnk9ImJvdW5kYXJ5X3N0cmluZyIKCi0tYm91bmRhcnlfc3RyaW5nCkNvbnRlbnQtVHlwZTogdGV4dC9wbGFpbjsgY2hhcnNldD1VVEYtOAoKVGhpcyBpcyB0aGUgcGxhaW4gdGV4dCBwYXJ0LgoKLS1ib3VuZGFyeV9zdHJpbmcKQ29udGVudC1UeXBlOiB0ZXh0L2h0bWw7IGNoYXJzZXQ9VVRGLTgKCjxwPlRoaXMgaXMgdGhlIDxiPmh0bWw8L2I+IHBhcnQuPC9wPgoKLS1ib3VuZGFyeV9zdHJpbmctLQ=="
    }

    with patch("digital_asset_harvester.ingest.gmail_client.build") as mock_build:
        mock_build.return_value = mock_gmail_service
        client = GmailClient()
        emails = list(client.search_emails("test query"))

    assert len(emails) == 1
    assert emails[0]["subject"] == "Multipart Email"
