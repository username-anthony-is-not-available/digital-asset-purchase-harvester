import mailbox
import email
from email.header import decode_header
from typing import Any, Dict, Generator

class MboxDataExtractor:
    """Extracts data from an mbox file."""

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
        payload = message.get_payload(decode=True)
        return payload.decode(errors="ignore") if isinstance(payload, (bytes, bytearray)) else str(payload)

    def extract_emails(self) -> Generator[Dict[str, Any], None, None]:
        try:
            mbox = mailbox.mbox(self.mbox_file)
        except (FileNotFoundError, mailbox.Error):
            return

        for message in mbox:
            yield {
                "subject": self.decode_header_value(message.get("subject", "") or ""),
                "sender": self.decode_header_value(message.get("from", "") or ""),
                "date": message.get("date", ""),
                "body": self.extract_body(message),
            }
