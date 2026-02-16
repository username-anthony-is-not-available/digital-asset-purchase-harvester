from __future__ import annotations

import base64
import logging
from email import message_from_bytes
from typing import Any, Dict, Iterator

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .email_parser import message_to_dict
from .oauth import get_gmail_credentials

logger = logging.getLogger(__name__)


class GmailClient:
    """A client for interacting with the Gmail API."""

    def __init__(self) -> None:
        """Initializes the Gmail client."""
        self.creds = get_gmail_credentials()
        self.service = build("gmail", "v1", credentials=self.creds)

    def search_emails(self, query: str, raw: bool = False) -> Iterator[Any]:
        """
        Searches for emails matching the given query.

        :param query: The query to search for.
        :param raw: Whether to return raw message bytes.
        :return: An iterator of email messages.
        """
        try:
            next_page_token = None
            while True:
                response = (
                    self.service.users().messages().list(userId="me", q=query, pageToken=next_page_token).execute()
                )
                messages = response.get("messages", [])

                for message in messages:
                    raw_message = (
                        self.service.users().messages().get(userId="me", id=message["id"], format="raw").execute()
                    )
                    msg_bytes = base64.urlsafe_b64decode(raw_message["raw"].encode("ASCII"))

                    if raw:
                        yield {"raw": msg_bytes, "id": message["id"]}
                        continue

                    email_msg = message_from_bytes(msg_bytes)
                    yield message_to_dict(email_msg)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return iter(())
