from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from digital_asset_harvester.ingest.imap_client import ImapClient


@patch("imaplib.IMAP4_SSL")
def test_imap_client_password_auth(mock_imaplib):
    """Tests that the IMAP client logs in with a password."""
    mock_imap_client = MagicMock()
    mock_imaplib.return_value = mock_imap_client

    with ImapClient("imap.example.com", "user", "pass") as client:
        client.search_emails("ALL")

    mock_imap_client.login.assert_called_once_with("user", "pass")
    mock_imap_client.logout.assert_called_once()


@patch("imaplib.IMAP4_SSL")
@patch("digital_asset_harvester.ingest.imap_client.get_gmail_credentials")
def test_imap_client_gmail_oauth2(mock_get_gmail_credentials, mock_imaplib):
    """Tests that the IMAP client authenticates with Gmail OAuth2."""
    mock_imap_client = MagicMock()
    mock_imaplib.return_value = mock_imap_client
    mock_creds = MagicMock()
    mock_creds.token = "gmail_token"
    mock_get_gmail_credentials.return_value = mock_creds

    with ImapClient(
        "imap.gmail.com", "user", auth_type="gmail_oauth2"
    ) as client:
        client.search_emails("ALL")

    mock_imap_client.authenticate.assert_called_once()
    mock_imap_client.logout.assert_called_once()


@patch("imaplib.IMAP4_SSL")
@patch("digital_asset_harvester.ingest.imap_client.get_outlook_credentials")
def test_imap_client_outlook_oauth2(mock_get_outlook_credentials, mock_imaplib):
    """Tests that the IMAP client authenticates with Outlook OAuth2."""
    mock_imap_client = MagicMock()
    mock_imaplib.return_value = mock_imap_client
    mock_get_outlook_credentials.return_value = "outlook_token"

    with ImapClient(
        "outlook.office365.com",
        "user",
        auth_type="outlook_oauth2",
        client_id="client_id",
        authority="authority",
    ) as client:
        client.search_emails("ALL")

    mock_imap_client.authenticate.assert_called_once()
    mock_imap_client.logout.assert_called_once()


@patch("imaplib.IMAP4_SSL")
def test_imap_client_search_emails(mock_imaplib):
    """Tests that the IMAP client searches for and parses emails using UIDs."""
    mock_imap_client = MagicMock()
    mock_imaplib.return_value = mock_imap_client
    mock_imap_client.uid.side_effect = [
        ("OK", [b"101 102"]),  # SEARCH
        ("OK", [(b"101 (RFC822)", b"From: a@b.c\r\n\r\nBody1")]),  # FETCH 101
        ("OK", [(b"102 (RFC822)", b"From: d@e.f\r\n\r\nBody2")]),  # FETCH 102
    ]

    with ImapClient("imap.example.com", "user", "pass") as client:
        emails = list(client.search_emails("ALL"))

    assert len(emails) == 2
    assert emails[0]["sender"] == "a@b.c"
    assert emails[0]["uid"] == "101"
    assert emails[1]["sender"] == "d@e.f"
    assert emails[1]["uid"] == "102"

    # Verify UID calls
    assert mock_imap_client.uid.call_count == 3
