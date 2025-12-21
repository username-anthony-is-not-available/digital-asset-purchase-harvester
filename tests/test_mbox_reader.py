from unittest.mock import MagicMock, patch
from digital_asset_harvester.ingest.mbox_reader import MboxDataExtractor

@patch("mailbox.mbox")
def test_mbox_data_extractor_handles_missing_subject(mock_mbox):
    mock_message = MagicMock()
    mock_message.get.side_effect = lambda key, default: "" if key == "subject" else "test"
    mock_message.is_multipart.return_value = False
    mock_message.get_payload.return_value = b""
    mock_mbox.return_value.values.return_value = [mock_message]

    extractor = MboxDataExtractor("test.mbox")
    emails = extractor.extract_all_emails()

    assert list(emails)[0]["subject"] == ""

@patch("mailbox.mbox")
def test_mbox_data_extractor_handles_multipart_email(mock_mbox):
    mock_part = MagicMock()
    mock_part.get_content_type.return_value = "text/plain"
    mock_part.get_payload.return_value = b"test body"

    mock_message = MagicMock()
    mock_message.walk.return_value = [mock_part]
    mock_message.is_multipart.return_value = True
    mock_mbox.return_value.values.return_value = [mock_message]

    extractor = MboxDataExtractor("test.mbox")
    emails = extractor.extract_all_emails()

    assert list(emails)[0]["body"] == "test body"
