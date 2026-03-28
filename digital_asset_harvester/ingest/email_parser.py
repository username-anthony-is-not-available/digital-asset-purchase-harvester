import email
import re
from email.header import decode_header, make_header
from typing import Any, Dict


def decode_header_value(value: str) -> str:
    """Safely decodes email header values."""
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except (ValueError, TypeError, HeaderParseError):
        return str(value)


class HeaderParseError(Exception):
    """Exception raised for errors during header parsing."""
    pass


def strip_html_tags(html: str) -> str:
    """Basic HTML tag stripping using regex."""
    # Remove script and style elements
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Replace common block elements with newlines to preserve some structure
    html = re.sub(r"<(p|br|div|tr|h1|h2|h3|h4|h5|h6)[^>]*>", "\n", html, flags=re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", "", html)
    # Unescape common entities
    text = (
        text.replace("&nbsp;", " ")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
    )
    # Cleanup whitespace
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def extract_body(message: email.message.Message) -> str:
    """Extracts the body from an email message, falling back to HTML if plain text is missing."""
    html_content = ""

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")

            if "attachment" in content_disposition:
                continue

            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        plain_text = payload.decode(charset, errors="ignore")
                        if plain_text.strip():
                            return plain_text
                except (UnicodeDecodeError, AttributeError):
                    pass
            elif content_type == "text/html":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        html_content = payload.decode(charset, errors="ignore")
                except (UnicodeDecodeError, AttributeError):
                    pass
    else:
        content_type = message.get_content_type()
        body = ""
        try:
            payload = message.get_payload(decode=True)
            if payload:
                charset = message.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="ignore")
        except (UnicodeDecodeError, AttributeError):
            pass

        if content_type == "text/plain":
            return body
        elif content_type == "text/html":
            html_content = body

    if html_content.strip():
        return strip_html_tags(html_content)

    return ""


def message_to_dict(message: email.message.Message) -> Dict[str, Any]:
    """Converts an email.message.Message to a dictionary."""
    return {
        "subject": decode_header_value(message.get("subject", "")),
        "sender": decode_header_value(message.get("from", "")),
        "date": decode_header_value(message.get("date", "")),
        "body": extract_body(message),
        "message_id": message.get("Message-ID", ""),
    }
