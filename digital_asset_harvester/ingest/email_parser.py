import email
from email.header import decode_header, make_header
from typing import Dict, Any


def decode_header_value(value: str) -> str:
    """Safely decodes email header values."""
    if not value:
        return ""
    return str(make_header(decode_header(value)))


def extract_body(message: email.message.Message) -> str:
    """Extracts the text/plain body from an email message."""
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                charset = part.get_content_charset() or "utf-8"
                try:
                    return payload.decode(charset, errors="ignore")
                except (UnicodeDecodeError, AttributeError):
                    return str(payload)
    else:
        payload = message.get_payload(decode=True)
        charset = message.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="ignore")
        except (UnicodeDecodeError, AttributeError):
            return str(payload)
    return ""


def message_to_dict(message: email.message.Message) -> Dict[str, Any]:
    """Converts an email.message.Message to a dictionary."""
    return {
        "subject": decode_header_value(message.get("subject", "")),
        "sender": decode_header_value(message.get("from", "")),
        "date": decode_header_value(message.get("date", "")),
        "body": extract_body(message),
    }
