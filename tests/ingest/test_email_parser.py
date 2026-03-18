"""Tests for the email_parser module."""

import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytest

from digital_asset_harvester.ingest.email_parser import (
    decode_header_value,
    extract_body,
    message_to_dict,
)


class TestDecodeHeaderValue:
    """Tests for decode_header_value function."""

    def test_decode_simple_header(self):
        """Test decoding a simple ASCII header."""
        result = decode_header_value("Test Subject")
        assert result == "Test Subject"

    def test_decode_empty_header(self):
        """Test decoding an empty header."""
        result = decode_header_value("")
        assert result == ""

    def test_decode_none_header(self):
        """Test decoding a None header."""
        result = decode_header_value(None)
        assert result == ""

    def test_decode_utf8_header(self):
        """Test decoding a UTF-8 encoded header."""
        # Test with a simple UTF-8 string
        result = decode_header_value("Bitcoin Purchase ₿")
        assert "Bitcoin Purchase" in result


class TestExtractBody:
    """Tests for extract_body function."""

    def test_extract_body_simple_text(self):
        """Test extracting body from a simple text email."""
        msg = MIMEText("This is the email body")
        body = extract_body(msg)
        assert body == "This is the email body"

    def test_extract_body_multipart(self):
        """Test extracting body from a multipart email."""
        msg = MIMEMultipart()
        text_part = MIMEText("This is the text body")
        msg.attach(text_part)

        body = extract_body(msg)
        assert body == "This is the text body"

    def test_extract_body_multipart_with_html(self):
        """Test extracting text body from multipart email with HTML."""
        msg = MIMEMultipart("alternative")
        text_part = MIMEText("Plain text body", "plain")
        html_part = MIMEText("<html><body>HTML body</body></html>", "html")
        msg.attach(text_part)
        msg.attach(html_part)

        body = extract_body(msg)
        assert "Plain text body" in body

    def test_extract_body_with_attachment(self):
        """Test extracting body when email has attachments."""
        msg = MIMEMultipart()
        text_part = MIMEText("Email body with attachment")
        msg.attach(text_part)

        # Add an attachment
        attachment = MIMEText("attachment content")
        attachment.add_header("Content-Disposition", "attachment", filename="test.txt")
        msg.attach(attachment)

        body = extract_body(msg)
        assert "Email body with attachment" in body
        assert "attachment content" not in body

    def test_extract_body_empty_message(self):
        """Test extracting body from an empty message."""
        msg = email.message.Message()
        body = extract_body(msg)
        # Should return empty string or handle gracefully
        assert isinstance(body, str)

    def test_extract_body_with_charset(self):
        """Test extracting body with non-UTF-8 charset."""
        msg = MIMEText("Test body", "plain", "utf-8")
        body = extract_body(msg)
        assert body == "Test body"


class TestMessageToDict:
    """Tests for message_to_dict function."""

    def test_message_to_dict_complete(self):
        """Test converting a complete email message to dict."""
        msg = MIMEText("Email body content")
        msg["Subject"] = "Test Subject"
        msg["From"] = "sender@example.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"

        result = message_to_dict(msg)

        assert result["subject"] == "Test Subject"
        assert result["sender"] == "sender@example.com"
        assert result["date"] == "Mon, 01 Jan 2024 12:00:00 +0000"
        assert result["body"] == "Email body content"

    def test_message_to_dict_missing_headers(self):
        """Test converting email with missing headers."""
        msg = MIMEText("Body only")

        result = message_to_dict(msg)

        assert result["subject"] == ""
        assert result["sender"] == ""
        assert result["date"] == ""
        assert result["body"] == "Body only"

    def test_message_to_dict_coinbase_style(self):
        """Test converting a Coinbase-style purchase email."""
        msg = MIMEText("You successfully purchased 0.001 BTC for $100.00 USD.")
        msg["Subject"] = "Your Coinbase purchase of 0.001 BTC"
        msg["From"] = "Coinbase <no-reply@coinbase.com>"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"

        result = message_to_dict(msg)

        assert "Coinbase purchase" in result["subject"]
        assert "Coinbase" in result["sender"]
        assert "0.001 BTC" in result["body"]

    def test_message_to_dict_multipart_email(self):
        """Test converting a multipart email message."""
        msg = MIMEMultipart()
        msg["Subject"] = "Multipart Email"
        msg["From"] = "test@example.com"
        msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"

        text_part = MIMEText("This is the body")
        msg.attach(text_part)

        result = message_to_dict(msg)

        assert result["subject"] == "Multipart Email"
        assert result["sender"] == "test@example.com"
        assert "This is the body" in result["body"]

    def test_message_to_dict_with_special_characters(self):
        """Test converting email with special characters in headers."""
        msg = MIMEText("Purchase confirmed")
        msg["Subject"] = "Bitcoin Purchase: ₿ 1.5 BTC"
        msg["From"] = "Exchange <support@exchange.com>"

        result = message_to_dict(msg)

        assert "Bitcoin Purchase" in result["subject"]
        assert "Exchange" in result["sender"]
