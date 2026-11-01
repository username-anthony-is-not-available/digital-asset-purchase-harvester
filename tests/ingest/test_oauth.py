"""Tests for OAuth credentials management in Gmail and Outlook."""

from __future__ import annotations

from unittest.mock import MagicMock, mock_open, patch

import pytest

import digital_asset_harvester.ingest.oauth as oauth
from digital_asset_harvester.ingest.oauth import (
    GMAIL_SCOPES,
    OUTLOOK_SCOPES,
    get_gmail_credentials,
    get_outlook_credentials,
)


def test_get_gmail_credentials_existing_valid_token():
    """Test retrieving valid Gmail credentials from an existing token file."""
    mock_creds = MagicMock()
    mock_creds.valid = True

    with patch("os.path.exists", return_value=True):
        with patch.object(oauth.Credentials, "from_authorized_user_file", return_value=mock_creds) as mock_from_file:
            creds = get_gmail_credentials()

            mock_from_file.assert_called_once_with("gmail_token.json", GMAIL_SCOPES)
            assert creds == mock_creds


def test_get_gmail_credentials_expired_token_refreshed():
    """Test refreshing an expired Gmail token with a refresh token."""
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "valid_refresh_token"
    mock_creds.to_json.return_value = '{"token": "refreshed"}'

    with patch("os.path.exists", return_value=True):
        with patch.object(oauth.Credentials, "from_authorized_user_file", return_value=mock_creds):
            with patch("builtins.open", mock_open()) as mocked_file:
                creds = get_gmail_credentials()

                mock_creds.refresh.assert_called_once()
                mocked_file().write.assert_called_once_with('{"token": "refreshed"}')
                assert creds == mock_creds


def test_get_gmail_credentials_new_flow():
    """Test initiating new OAuth flow when no token file exists."""
    mock_flow = MagicMock()
    mock_creds = MagicMock()
    mock_creds.to_json.return_value = '{"token": "new"}'
    mock_flow.run_local_server.return_value = mock_creds

    with patch("os.path.exists", return_value=False):
        with patch.object(
            oauth.InstalledAppFlow, "from_client_secrets_file", return_value=mock_flow
        ) as mock_from_secrets:
            with patch("builtins.open", mock_open()) as mocked_file:
                creds = get_gmail_credentials()

                mock_from_secrets.assert_called_once_with("credentials.json", GMAIL_SCOPES)
                mock_flow.run_local_server.assert_called_once_with(port=0)
                mocked_file().write.assert_called_once_with('{"token": "new"}')
                assert creds == mock_creds


def test_get_gmail_credentials_missing_dependencies():
    """Test that get_gmail_credentials raises ImportError when dependencies are unavailable."""
    with patch.object(oauth, "OAUTH_DEPENDENCIES_AVAILABLE", False):
        with pytest.raises(ImportError, match="Gmail dependencies"):
            get_gmail_credentials()


def test_get_outlook_credentials_silent_success():
    """Test acquiring Outlook token silently when cached accounts exist."""
    mock_app = MagicMock()
    mock_app.get_accounts.return_value = [{"username": "user@outlook.com"}]
    mock_app.acquire_token_silent.return_value = {"access_token": "silent_token_123"}

    with patch.object(oauth.msal, "PublicClientApplication", return_value=mock_app):
        token = get_outlook_credentials(client_id="test_client", authority="https://login.microsoftonline.com/common")

        assert token == "silent_token_123"
        mock_app.acquire_token_silent.assert_called_once_with(
            OUTLOOK_SCOPES, account={"username": "user@outlook.com"}
        )


def test_get_outlook_credentials_device_flow():
    """Test acquiring Outlook token via device flow when no cached token is available."""
    mock_app = MagicMock()
    mock_app.get_accounts.return_value = []
    mock_app.initiate_device_flow.return_value = {
        "user_code": "ABCD",
        "message": "To sign in, use a web browser to open the page https://microsoft.com/devicelogin",
    }
    mock_app.acquire_token_by_device_flow.return_value = {"access_token": "device_token_456"}

    with patch.object(oauth.msal, "PublicClientApplication", return_value=mock_app):
        token = get_outlook_credentials(client_id="test_client", authority="https://login.microsoftonline.com/common")

        assert token == "device_token_456"
        mock_app.initiate_device_flow.assert_called_once_with(scopes=OUTLOOK_SCOPES)


def test_get_outlook_credentials_device_flow_failure():
    """Test Outlook device flow handling when authentication fails."""
    mock_app = MagicMock()
    mock_app.get_accounts.return_value = []
    mock_app.initiate_device_flow.return_value = {"message": "Go to login"}
    mock_app.acquire_token_by_device_flow.return_value = {"error_description": "User cancelled login"}

    with patch.object(oauth.msal, "PublicClientApplication", return_value=mock_app):
        with pytest.raises(Exception, match="User cancelled login"):
            get_outlook_credentials(client_id="test_client", authority="https://login.microsoftonline.com/common")


def test_get_outlook_credentials_missing_dependencies():
    """Test that get_outlook_credentials raises ImportError when dependencies are unavailable."""
    with patch.object(oauth, "OAUTH_DEPENDENCIES_AVAILABLE", False):
        with pytest.raises(ImportError, match="Outlook dependencies"):
            get_outlook_credentials(client_id="test_client", authority="https://login.microsoftonline.com/common")
