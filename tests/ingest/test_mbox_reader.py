"""Tests for the mbox_reader utility."""

import mailbox
from unittest.mock import MagicMock, mock_open, patch

import pytest

from digital_asset_harvester.ingest.mbox_reader import MboxDataExtractor


@pytest.fixture
def mock_mbox_file(tmp_path):
    """Creates a mock mbox file with two messages."""
    mbox_path = tmp_path / "test.mbox"
    mbox = mailbox.mbox(mbox_path)
    msg1 = mailbox.mboxMessage()
    msg1.set_payload("This is the body of the first email.")
    msg1["Subject"] = "Test Subject 1"
    msg1["From"] = "sender1@example.com"
    msg1["To"] = "recipient1@example.com"
    msg1["Date"] = "Tue, 23 Jul 2024 10:00:00 -0000"
    mbox.add(msg1)

    msg2 = mailbox.mboxMessage()
    msg2.set_payload("This is the body of the second email.")
    msg2["Subject"] = "Test Subject 2"
    msg2["From"] = "sender2@example.com"
    msg2["To"] = "recipient2@example.com"
    msg2["Date"] = "Tue, 23 Jul 2024 11:00:00 -0000"
    mbox.add(msg2)

    mbox.close()
    return mbox_path


def test_extract_emails_success(mock_mbox_file):
    """Tests that emails are extracted from a valid mbox file."""
    extractor = MboxDataExtractor(mock_mbox_file)
    emails = list(extractor.extract_emails())

    assert len(emails) == 2
    assert emails[0]["subject"] == "Test Subject 1"
    assert emails[1]["body"].strip() == "This is the body of the second email."


def test_extract_emails_file_not_found():
    """Tests that the extractor handles a missing mbox file gracefully."""
    extractor = MboxDataExtractor("non_existent_path.mbox")
    emails = list(extractor.extract_emails())
    assert len(emails) == 0


def test_extract_emails_malformed_file():
    """Tests that the extractor handles a malformed mbox file."""
    with patch("mailbox.mbox", side_effect=mailbox.Error("Malformed mbox")):
        extractor = MboxDataExtractor("malformed.mbox")
        emails = list(extractor.extract_emails())
        assert len(emails) == 0


def test_extract_emails_multipart(tmp_path):
    """Tests that multipart emails are parsed correctly."""
    from email.message import Message

    mbox_path = tmp_path / "test.mbox"
    mbox = mailbox.mbox(mbox_path)
    msg = mailbox.mboxMessage()
    msg["Content-Type"] = "multipart/alternative"
    msg["Subject"] = "Multipart Test"
    msg["From"] = "multipart@example.com"

    plain_part = Message()
    plain_part.set_payload("This is the plain text part.")
    plain_part["Content-Type"] = "text/plain"

    html_part = Message()
    html_part.set_payload("<html><body><p>This is the HTML part.</p></body></html>")
    html_part["Content-Type"] = "text/html"

    msg.set_payload([plain_part, html_part])

    mbox.add(msg)
    mbox.close()

    extractor = MboxDataExtractor(mbox_path)
    emails = list(extractor.extract_emails())

    assert len(emails) == 1
    assert emails[0]["subject"] == "Multipart Test"
    assert "This is the plain text part." in emails[0]["body"]
    assert "<html><body><p>This is the HTML part.</p></body></html>" not in emails[0]["body"]
