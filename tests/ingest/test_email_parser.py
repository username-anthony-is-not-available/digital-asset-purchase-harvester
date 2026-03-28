"""Tests for the email_parser module."""

import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytest

from digital_asset_harvester.ingest.email_parser import (
    decode_header_value,
    extract_body,
    message_to_dict,
    strip_html_tags,
)


class TestStripHtmlTags:
    """Tests for strip_html_tags function."""

    def test_strip_html_basic(self):
        html = "<p>Hello <b>World</b></p>"
        assert strip_html_tags(html) == "Hello World"

    def test_strip_html_script_style(self):
        html = "<script>alert('hi')</script><style>body {color: red;}</style><p>Content</p>"
        assert strip_html_tags(html) == "Content"

    def test_strip_html_block_elements(self):
        html = "<div>Line 1</div><p>Line 2</p>Line 3<br>Line 4"
        text = strip_html_tags(html)
        assert "Line 1" in text
        assert "Line 2" in text
        assert "Line 3" in text
        assert "Line 4" in text

    def test_strip_html_entities(self):
        html = "Fish &amp; Chips &nbsp; &lt; &gt; &quot;"
        assert strip_html_tags(html) == 'Fish & Chips   < > "'


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

    def test_extract_body_html_only(self):
        """Test extracting body from an HTML-only email."""
        msg = MIMEText("<html><body>HTML only body</body></html>", "html")
        body = extract_body(msg)
        assert body == "HTML only body"

    def test_extract_body_multipart_html_only(self):
        """Test extracting body from a multipart email with only HTML."""
        msg = MIMEMultipart("alternative")
        html_part = MIMEText("<html><body>HTML body in multipart</body></html>", "html")
        msg.attach(html_part)

        body = extract_body(msg)
        assert body == "HTML body in multipart"

    def test_extract_body_empty(self):
        """Test extracting body from an empty email."""
        msg = MIMEMultipart("alternative")
        assert extract_body(msg) == ""

    def test_extract_body_decode_error(self):
        """Test extracting body with a decoding error."""
        msg = email.message.Message()
        msg.set_payload(b"\xff\xfe\xfd")
        msg["Content-Type"] = "text/plain; charset=utf-8"
        # Since we use errors="ignore", it should return a string even if garbage
        body = extract_body(msg)
        assert isinstance(body, str)

    def test_extract_body_multipart_decode_error(self):
        """Test extracting body with a decoding error in a multipart email."""
        msg = MIMEMultipart("alternative")
        part = email.message.Message()
        part.set_payload(b"\xff\xfe\xfd")
        part["Content-Type"] = "text/plain; charset=utf-8"
        msg.attach(part)

        # It should ignore errors and return something or continue
        body = extract_body(msg)
        assert isinstance(body, str)

    def test_extract_body_multipart_html_decode_error(self):
        """Test extracting body with a decoding error in HTML part of multipart email."""
        msg = MIMEMultipart("alternative")
        part = email.message.Message()
        part.set_payload(b"\xff\xfe\xfd")
        part["Content-Type"] = "text/html; charset=utf-8"
        msg.attach(part)

        body = extract_body(msg)
        assert isinstance(body, str)

    def test_extract_body_no_text_at_all(self):
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText("", "plain"))
        msg.attach(MIMEText("", "html"))
        assert extract_body(msg) == ""

    def test_extract_body_multipart_with_plain_text_return(self):
        """Test that multipart returns early if plain text is found."""
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText("Plain", "plain"))
        msg.attach(MIMEText("HTML", "html"))
        assert extract_body(msg) == "Plain"

    def test_extract_body_multipart_attachment(self):
        """Test that multipart skips attachments."""
        msg = MIMEMultipart()
        attachment = MIMEText("content")
        attachment.add_header("Content-Disposition", "attachment", filename="test.txt")
        msg.attach(attachment)
        assert extract_body(msg) == ""


class TestExtractBodyAdvanced:
    """Advanced tests for extract_body requiring mocking."""

    def test_extract_body_multipart_decode_exception(self, mocker):
        msg = MIMEMultipart("alternative")
        part = MIMEText("Plain", "plain")
        # Mock get_payload to fail on first call (with decode=True)
        # But we want it to succeed on the second call (without decode=True) to test fallback
        # However, the code calls it again with decode=True in the except block.
        # Let's just make it return a specific value in the second call.
        mock_payload = mocker.Mock()
        mock_payload.decode.side_effect = AttributeError("mock error")
        mocker.patch.object(part, "get_payload", return_value=mock_payload)

        msg.attach(part)

        body = extract_body(msg)
        assert isinstance(body, str)

    def test_extract_body_multipart_html_decode_exception(self, mocker):
        msg = MIMEMultipart("alternative")
        part = MIMEText("<html>HTML</html>", "html")
        mock_payload = mocker.Mock()
        mock_payload.decode.side_effect = AttributeError("mock error")
        mocker.patch.object(part, "get_payload", return_value=mock_payload)
        msg.attach(part)

        body = extract_body(msg)
        assert isinstance(body, str)

    def test_extract_body_non_multipart_decode_exception(self, mocker):
        msg = MIMEText("Plain", "plain")
        mock_payload = mocker.Mock()
        mock_payload.decode.side_effect = AttributeError("mock error")
        mocker.patch.object(msg, "get_payload", return_value=mock_payload)

        body = extract_body(msg)
        assert isinstance(body, str)


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
