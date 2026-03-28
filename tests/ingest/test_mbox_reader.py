from digital_asset_harvester.ingest.mbox_reader import MboxDataExtractor


def test_mbox_reader_initialization(tmp_path):
    """
    Tests that the MboxReader can be initialized.
    """
    non_existent = str(tmp_path / "non_existent_path.mbox")
    reader = MboxDataExtractor(non_existent)
    assert reader is not None


def test_mbox_reader_extract_emails_file_not_found(tmp_path):
    """
    Tests that extract_emails returns an empty generator if the mbox file does not exist.
    """
    non_existent = str(tmp_path / "non_existent_path.mbox")
    reader = MboxDataExtractor(non_existent)
    emails = reader.extract_emails()
    assert list(emails) == []


def test_mbox_reader_extract_emails_from_test_file(mbox_file_path):
    """
    Tests that extract_emails can extract emails from a test mbox file.
    """
    reader = MboxDataExtractor(mbox_file_path)
    emails = list(reader.extract_emails())
    assert len(emails) == 10

    # Check the subjects to make sure they were parsed correctly
    subjects = [email["subject"] for email in emails]
    assert "Your Coinbase purchase of 0.001 BTC" in subjects
    assert "Your order to buy 0.1 ETH has been filled" in subjects
    assert "Bitcoin Price Alert" in subjects
    assert "Trade Confirmation: Buy 0.5 XMR" in subjects
    assert "Order Confirmation - Buy BTC" in subjects

    # Check the bodies contain expected content
    bodies = [email["body"] for email in emails]
    coinbase_body = next((b for b in bodies if "0.001 BTC for $100.00 USD" in b), None)
    assert coinbase_body is not None

    binance_body = next((b for b in bodies if "0.1 ETH for 200.00 USD" in b), None)
    assert binance_body is not None


def test_mbox_reader_extract_emails_empty_file(tmp_path):
    """
    Tests that extract_emails handles an empty mbox file gracefully.
    """
    temp_file = tmp_path / "empty.mbox"
    temp_file.write_text("")

    reader = MboxDataExtractor(str(temp_file))
    emails = list(reader.extract_emails())
    assert emails == []


def test_mbox_reader_extract_emails_single_email(tmp_path):
    """
    Tests extracting a single email from an mbox file.
    """
    mbox_content = """From MAILER-DAEMON Mon Nov 12 11:30:00 2023
From: test@example.com
Subject: Single Test Email

This is a test email body.
"""
    temp_file = tmp_path / "single.mbox"
    temp_file.write_text(mbox_content)

    reader = MboxDataExtractor(str(temp_file))
    emails = list(reader.extract_emails())
    assert len(emails) == 1
    assert emails[0]["subject"] == "Single Test Email"
    assert "test email body" in emails[0]["body"]


def test_mbox_reader_handles_malformed_email(tmp_path):
    """
    Tests that the reader handles malformed emails gracefully.
    """
    mbox_content = """From MAILER-DAEMON Mon Nov 12 11:30:00 2023
From: test@example.com
This is not properly formatted

Body without proper headers
"""
    temp_file = tmp_path / "malformed.mbox"
    temp_file.write_text(mbox_content)

    reader = MboxDataExtractor(str(temp_file))
    emails = list(reader.extract_emails())
    # Should still extract something, even if malformed
    assert isinstance(emails, list)


def test_mbox_reader_extract_emails_with_metadata(mbox_file_path):
    """
    Tests that extract_emails preserves email metadata.
    """
    reader = MboxDataExtractor(mbox_file_path)
    emails = list(reader.extract_emails())

    # All emails should have required keys
    for email in emails:
        assert "subject" in email
        assert "body" in email
        assert "sender" in email or "from" in email
        assert isinstance(email["body"], str)
        assert isinstance(email["subject"], str)


def test_mbox_reader_len(mbox_file_path, tmp_path):
    """Test the __len__ method of MboxDataExtractor."""
    reader = MboxDataExtractor(mbox_file_path)
    assert len(reader) == 10

    # Test with non-existent file
    non_existent = str(tmp_path / "missing.mbox")
    reader_missing = MboxDataExtractor(non_existent)
    assert len(reader_missing) == 0


def test_mbox_reader_len_error(mocker, tmp_path):
    """Test __len__ when mailbox.mbox raises an error."""
    mocker.patch("mailbox.mbox", side_effect=Exception("mailbox error"))
    non_existent = str(tmp_path / "any.mbox")
    reader = MboxDataExtractor(non_existent)
    assert len(reader) == 0


def test_mbox_emails_iterable_raw(mbox_file_path):
    """Test MboxEmailsIterable with raw=True."""
    reader = MboxDataExtractor(mbox_file_path)
    emails = list(reader.extract_emails(raw=True))
    assert len(emails) == 10
    assert isinstance(emails[0], str)
    assert "Coinbase" in emails[0]


def test_mbox_emails_iterable_invalid_file(tmp_path):
    """Test MboxEmailsIterable with an invalid file."""
    from digital_asset_harvester.ingest.mbox_reader import MboxEmailsIterable

    non_existent = str(tmp_path / "non_existent.mbox")
    iterable = MboxEmailsIterable(non_existent, raw=False)
    assert len(iterable) == 0
    assert list(iterable) == []


def test_mbox_emails_iterable_len_error(mocker, tmp_path):
    """Test MboxEmailsIterable.__len__ when len(self.mbox) raises an error."""
    from digital_asset_harvester.ingest.mbox_reader import MboxEmailsIterable

    non_existent = str(tmp_path / "any.mbox")
    iterable = MboxEmailsIterable(non_existent, raw=False)
    iterable.mbox = mocker.MagicMock()
    iterable.mbox.__len__.side_effect = Exception("len error")
    assert len(iterable) == 0


def test_mbox_emails_iterable_init_error(mocker, tmp_path):
    """Test MboxEmailsIterable.__init__ when mailbox.mbox raises an error."""
    from digital_asset_harvester.ingest.mbox_reader import MboxEmailsIterable

    mocker.patch("mailbox.mbox", side_effect=Exception("init error"))
    non_existent = str(tmp_path / "any.mbox")
    iterable = MboxEmailsIterable(non_existent, raw=False)
    assert iterable.mbox == []
