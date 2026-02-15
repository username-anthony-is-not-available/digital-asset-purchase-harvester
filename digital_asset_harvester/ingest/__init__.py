"""Email ingestion utilities."""

from .gmail_client import GmailClient
from .imap_client import ImapClient
from .mbox_reader import MboxDataExtractor
from .outlook_client import OutlookClient

__all__ = ["MboxDataExtractor", "ImapClient", "GmailClient", "OutlookClient"]
