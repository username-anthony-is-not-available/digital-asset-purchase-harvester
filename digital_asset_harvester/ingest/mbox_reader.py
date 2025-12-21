import mailbox
from typing import Dict, Generator

class MboxDataExtractor:
    """Extracts data from an mbox file."""

    def __init__(self, mbox_file: str):
        self.mbox_file = mbox_file

    def extract_all_emails(self) -> Generator[Dict[str, str], None, None]:
        """Extracts all emails from the mbox file."""
        mbox = mailbox.mbox(self.mbox_file)
        for message in mbox.values():
            email_data = {
                "sender": message.get("from", ""),
                "recipient": message.get("to", ""),
                "subject": message.get("subject", ""),
                "date": message.get("date", ""),
                "body": "",
            }

            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        email_data["body"] = part.get_payload(decode=True).decode()
                        break
            else:
                email_data["body"] = message.get_payload(decode=True).decode()
            yield email_data
