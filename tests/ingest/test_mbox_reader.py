from digital_asset_harvester.ingest.mbox_reader import MboxDataExtractor

def test_mbox_reader_initialization():
    """
    Tests that the MboxReader can be initialized.
    """
    reader = MboxDataExtractor("non_existent_path.mbox")
    assert reader is not None

def test_mbox_reader_extract_emails_file_not_found():
    """
    Tests that extract_emails returns an empty generator if the mbox file does not exist.
    """
    reader = MboxDataExtractor("non_existent_path.mbox")
    emails = reader.extract_emails()
    assert list(emails) == []


def test_mbox_reader_extract_emails_from_test_file(mbox_file_path):
    """
    Tests that extract_emails can extract emails from a test mbox file.
    """
    reader = MboxDataExtractor(mbox_file_path)
    emails = list(reader.extract_emails())
    assert len(emails) == 3

    # Check the subjects to make sure they were parsed correctly
    subjects = [email["subject"] for email in emails]
    assert "Your Coinbase purchase of 0.001 BTC" in subjects
    assert "Your order to buy 0.1 ETH has been filled" in subjects
    assert "Bitcoin Price Alert" in subjects

    # Check the bodies
    bodies = [email["body"] for email in emails]
    assert "You successfully purchased 0.001 BTC for $100.00 USD." in bodies[0]
    assert "Your order to buy 0.1 ETH for 200.00 USD has been filled." in bodies[1]
    assert "Bitcoin is up 5% in the last 24 hours." in bodies[2]
