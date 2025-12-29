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
