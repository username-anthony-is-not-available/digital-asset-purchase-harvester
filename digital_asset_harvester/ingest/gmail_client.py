from __future__ import annotations

import base64
import email
import logging
from email import message_from_bytes
from typing import Iterator

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .oauth import get_gmail_credentials

logger = logging.getLogger(__name__)


class GmailClient:
    """A client for interacting with the Gmail API."""

    def __init__(self) -> None:
        """Initializes the Gmail client."""
        self.creds = get_gmail_credentials()
        self.service = build("gmail", "v1", credentials=self.creds)

    def search_emails(self, query: str) -> Iterator[email.message.Message]:
        """
        Searches for emails matching the given query.

        :param query: The query to search for.
        :return: An iterator of email messages.
        """
        try:
            next_page_token = None
            while True:
                response = (
                    self.service.users()
                    .messages()
                    .list(userId="me", q=query, pageToken=next_page_token)
                    .execute()
                )
                messages = response.get("messages", [])

                for message in messages:
                    yield self._get_message_data(message["id"])

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return iter(())

    def _get_message_data(self, message_id: str) -> email.message.Message:
        """
        Gets the data for a single email message.

        :param message_id: The ID of the message to get.
        :return: An email.message.Message object.
        """
        message = (
            self.service.users()
            .messages()
            .get(userId="me", id=message_id, format="raw")
            .execute()
        )
        return self._parse_message(message)

    def _parse_message(self, message: dict) -> email.message.Message:
        """
        Parses a raw email message into a more usable format.

        :param message: The raw message data.
        :return: An email.message.Message object.
        """
        msg_str = base64.urlsafe_b64decode(message["raw"].encode("ASCII"))
        return message_from_bytes(msg_str)
