from __future__ import annotations

import os

try:
    import msal
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    OAUTH_DEPENDENCIES_AVAILABLE = True
except ImportError:
    OAUTH_DEPENDENCIES_AVAILABLE = False
    msal = None
    Request = None
    Credentials = None
    InstalledAppFlow = None

# Scopes for Gmail and Outlook
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
OUTLOOK_SCOPES = ["https://outlook.office.com/IMAP.AccessAsUser.All"]
GRAPH_SCOPES = ["https://graph.microsoft.com/Mail.Read"]


def get_gmail_credentials(
    token_file: str = "gmail_token.json",
    credentials_file: str = "credentials.json",
) -> Credentials:
    """Authenticate with the Gmail API using OAuth 2.0.

    :param token_file: Path to stored OAuth token JSON file.
    :param credentials_file: Path to OAuth client secrets JSON file.
    :return: Google OAuth Credentials instance.
    """
    if not OAUTH_DEPENDENCIES_AVAILABLE:
        raise ImportError("Gmail dependencies (google-auth, google-auth-oauthlib) are not installed.")

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    return creds


def get_outlook_credentials(client_id: str, authority: str, scopes: list[str] = None) -> str:
    """
    Authenticates with the Outlook API using OAuth 2.0.
    """
    if not OAUTH_DEPENDENCIES_AVAILABLE or msal is None:
        raise ImportError("Outlook dependencies (msal) are not installed.")

    if scopes is None:
        scopes = OUTLOOK_SCOPES

    app = msal.PublicClientApplication(client_id=client_id, authority=authority)

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
        if result:
            return result["access_token"]

    flow = app.initiate_device_flow(scopes=scopes)
    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(result.get("error_description", "Could not authenticate."))
