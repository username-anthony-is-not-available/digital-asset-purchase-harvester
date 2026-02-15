from __future__ import annotations

import logging
from email import message_from_bytes
from typing import Any, Iterator

import httpx

from .email_parser import message_to_dict
from .oauth import GRAPH_SCOPES, get_outlook_credentials

logger = logging.getLogger(__name__)


class OutlookClient:
    """A client for interacting with the Microsoft Graph API."""

    def __init__(self, client_id: str, authority: str) -> None:
        """
        Initializes the Outlook client.

        :param client_id: The OAuth2 client ID.
        :param authority: The OAuth2 authority URL.
        """
        self.client_id = client_id
        self.authority = authority
        self.token = get_outlook_credentials(client_id, authority, scopes=GRAPH_SCOPES)
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def search_emails(self, query: str, raw: bool = False) -> Iterator[Any]:
        """
        Searches for emails matching the given query.

        :param query: The query to search for.
        :param raw: Whether to return raw message bytes.
        :return: An iterator of email messages.
        """
        try:
            url = f"{self.base_url}/me/messages"
            # Using $search for query
            # Note: Graph API $search requires double quotes around the query for some reason
            # if it contains special characters or to ensure exact matching in some contexts.
            params = {"$search": f'"{query}"'}

            while url:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        url, headers=self.headers, params=params if url.endswith("/messages") else None
                    )
                    response.raise_for_status()
                    data = response.json()
                    messages = data.get("value", [])

                    for message in messages:
                        msg_id = message["id"]
                        # Fetch raw MIME content
                        mime_url = f"{self.base_url}/me/messages/{msg_id}/$value"
                        mime_response = client.get(mime_url, headers=self.headers)
                        mime_response.raise_for_status()
                        msg_bytes = mime_response.content

                        if raw:
                            yield {"raw": msg_bytes, "id": msg_id}
                            continue

                        email_msg = message_from_bytes(msg_bytes)
                        yield message_to_dict(email_msg)

                    url = data.get("@odata.nextLink")
                    params = None  # Parameters are already in the nextLink

        except httpx.HTTPStatusError as error:
            logger.error(f"HTTP error occurred: {error}")
            return iter(())
        except Exception as error:
            logger.error(f"An unexpected error occurred: {error}")
            return iter(())
