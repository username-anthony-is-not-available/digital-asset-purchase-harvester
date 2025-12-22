"""Utilities for reading email data from mbox files."""

import email
import mailbox
from email.header import decode_header
from typing import Any, Dict, Generator


class MboxDataExtractor:
    def __init__(self, mbox_file: str):
        self.mbox_file = mbox_file

    def decode_header_value(self, value: str) -> str:
        decoded_value, encoding = decode_header(value)[0]
        if isinstance(decoded_value, bytes):
            return decoded_value.decode(encoding or "utf-8", errors="ignore")
        return decoded_value

    def extract_body(self, message: email.message.Message) -> str:
        if message.is_multipart():
            return "".join(
                part.get_payload(decode=True).decode(errors="ignore")
                for part in message.walk()
                if part.get_content_type() == "text/plain"
            )
        return message.get_payload(decode=True).decode(errors="ignore")

    def extract_emails(self) -> Generator[Dict[str, Any], None, None]:
        try:
            mbox = mailbox.mbox(self.mbox_file)
        except (FileNotFoundError, mailbox.Error):
            return

        for message in mbox:
            yield {
                "subject": self.decode_header_value(message["subject"] or ""),
                "sender": self.decode_header_value(message["from"] or ""),
                "date": message["date"],
                "body": self.extract_body(message),
            }
