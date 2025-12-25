import mailbox
from typing import Any, Dict, Generator

from .email_parser import message_to_dict

class MboxDataExtractor:
    """Extracts data from an mbox file."""

    def __init__(self, mbox_file: str):
        self.mbox_file = mbox_file

    def extract_emails(self) -> Generator[Dict[str, Any], None, None]:
        try:
            mbox = mailbox.mbox(self.mbox_file)
        except (FileNotFoundError, mailbox.Error):
            return

        for message in mbox:
            yield message_to_dict(message)
