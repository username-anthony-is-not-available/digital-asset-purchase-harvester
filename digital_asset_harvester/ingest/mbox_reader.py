import mailbox
import logging
from typing import Any, Dict, Generator

from .email_parser import message_to_dict

logger = logging.getLogger(__name__)


class MboxDataExtractor:
    """Extracts data from an mbox file."""

    def __init__(self, mbox_file: str):
        self.mbox_file = mbox_file

    def __len__(self) -> int:
        """Returns the number of messages in the mbox file."""
        try:
            mbox = mailbox.mbox(self.mbox_file)
            return len(mbox)
        except Exception as e:
            logger.debug(f"Error getting mbox length: {e}")
            return 0

    def extract_emails(self, raw: bool = False) -> Any:
        """Returns an iterable that yields emails from the mbox file."""
        return MboxEmailsIterable(self.mbox_file, raw)


class MboxEmailsIterable:
    """Iterable for mbox emails that supports len()."""

    def __init__(self, mbox_file: str, raw: bool):
        self.mbox_file = mbox_file
        self.raw = raw
        try:
            self.mbox = mailbox.mbox(self.mbox_file)
        except Exception as e:
            logger.debug(f"Error opening mbox: {e}")
            self.mbox = []

    def __len__(self) -> int:
        try:
            return len(self.mbox)
        except Exception:
            return 0

    def __iter__(self) -> Generator[Any, None, None]:
        for message in self.mbox:
            if self.raw:
                yield message.as_string()
            else:
                yield message_to_dict(message)
