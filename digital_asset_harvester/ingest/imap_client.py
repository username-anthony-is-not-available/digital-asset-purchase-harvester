from __future__ import annotations

import email
import imaplib
import logging
from typing import Any, Dict, Iterator, Optional

from .email_parser import message_to_dict
from .oauth import get_gmail_credentials, get_outlook_credentials

logger = logging.getLogger(__name__)


class ImapClient:
    """A client for interacting with an IMAP server."""

    def __init__(
        self,
        server: str,
        user: str,
        password: Optional[str] = None,
        auth_type: str = "password",
        client_id: Optional[str] = None,
        authority: Optional[str] = None,
    ) -> None:
        """
        Initializes the IMAP client.
        """
        self.server = server
        self.user = user
        self.password = password
        self.auth_type = auth_type
        self.client_id = client_id
        self.authority = authority
        self.client = imaplib.IMAP4_SSL(self.server)

    def __enter__(self) -> "ImapClient":
        """Logs in to the IMAP server."""
        self._authenticate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Logs out of the IMAP server."""
        self.client.logout()

    def _authenticate(self) -> None:
        """Authenticates the client with the IMAP server."""
        if self.auth_type == "password":
            self.client.login(self.user, self.password)
        elif self.auth_type == "gmail_oauth2":
            creds = get_gmail_credentials()
            auth_string = f"user={self.user}\1auth=Bearer {creds.token}\1\1"
            self.client.authenticate("XOAUTH2", lambda x: auth_string)
        elif self.auth_type == "outlook_oauth2":
            token = get_outlook_credentials(self.client_id, self.authority)
            auth_string = f"user={self.user}\1auth=Bearer {token}\1\1"
            self.client.authenticate("XOAUTH2", lambda x: auth_string)
        else:
            raise ValueError(f"Unsupported auth type: {self.auth_type}")

    def uid_search(self, query: str, folder: str = "INBOX") -> list[str]:
        """
        Searches for emails matching the given query and returns their UIDs.
        """
        self.client.select(folder)
        status, message_ids = self.client.uid("SEARCH", None, query)
        if status != "OK":
            return []
        return [uid.decode() for uid in message_ids[0].split()]

    def fetch_emails_by_uids(
        self, uids: list[str], folder: str = "INBOX", raw: bool = False
    ) -> Iterator[Any]:
        """
        Fetches emails for the given UIDs.
        """
        self.client.select(folder)
        for uid in uids:
            status, message_data = self.client.uid("FETCH", uid, "(RFC822)")
            if status != "OK":
                continue

            if raw:
                # Find the raw message bytes in the response
                raw_content = None
                for response_part in message_data:
                    if isinstance(response_part, tuple):
                        raw_content = response_part[1]
                        break

                if raw_content:
                    yield {"raw": raw_content, "uid": uid}
                continue

            email_msg = self._parse_message(message_data)
            email_dict = message_to_dict(email_msg)
            email_dict["uid"] = uid
            yield email_dict

    def search_emails(
        self, query: str, folder: str = "INBOX", raw: bool = False
    ) -> Iterator[Any]:
        """
        Searches for emails matching the given query.
        """
        uids = self.uid_search(query, folder)
        yield from self.fetch_emails_by_uids(uids, folder, raw=raw)

    def _parse_message(self, message_data: list) -> email.message.Message:
        """
        Parses a raw email message into a more usable format.
        """
        for response_part in message_data:
            if isinstance(response_part, tuple):
                return email.message_from_bytes(response_part[1])
        raise ValueError("Could not parse email message")
