import os
import pytest
from pathlib import Path
from digital_asset_harvester.ingest.eml_reader import EmlDataExtractor

def test_eml_reader_initialization():
    """Tests that the EmlDataExtractor can be initialized."""
    reader = EmlDataExtractor("non_existent_dir")
    assert reader is not None

def test_eml_reader_extract_emails_dir_not_found():
    """Tests that extract_emails returns an empty generator if the directory does not exist."""
    reader = EmlDataExtractor("non_existent_dir")
    emails = reader.extract_emails()
    assert list(emails) == []

def test_eml_reader_extract_emails_from_fixtures():
    """Tests that extract_emails can extract emails from the fixtures directory."""
    fixtures_dir = os.path.join("tests", "fixtures", "emls")
    reader = EmlDataExtractor(fixtures_dir)
    emails = list(reader.extract_emails())

    assert len(emails) >= 2

    subjects = [email["subject"] for email in emails]
    assert "Your Coinbase purchase of 0.001 BTC" in subjects
    assert "Your order to buy 0.1 ETH has been filled" in subjects

    # Check bodies
    coinbase_email = next(e for e in emails if "Coinbase" in e["subject"])
    assert "0.001 BTC for $100.00 USD" in coinbase_email["body"]

    binance_email = next(e for e in emails if "0.1 ETH" in e["subject"])
    assert "0.1 ETH for 200.00 USD" in binance_email["body"]

def test_eml_reader_raw_output():
    """Tests that extract_emails can return raw message strings."""
    fixtures_dir = os.path.join("tests", "fixtures", "emls")
    reader = EmlDataExtractor(fixtures_dir)
    emails = list(reader.extract_emails(raw=True))

    assert len(emails) >= 2
    assert isinstance(emails[0], str)
    assert "Subject:" in emails[0]

def test_eml_reader_nested_directories(tmp_path):
    """Tests that the reader can walk through nested directories."""
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()

    eml_content = """From: test@example.com
Subject: Nested Email

This is a nested email.
"""
    (nested_dir / "test.eml").write_text(eml_content)

    reader = EmlDataExtractor(str(tmp_path))
    emails = list(reader.extract_emails())

    assert len(emails) == 1
    assert emails[0]["subject"] == "Nested Email"

def test_eml_reader_ignores_non_eml_files(tmp_path):
    """Tests that the reader ignores files that do not have a .eml extension."""
    (tmp_path / "test.txt").write_text("This is not an eml file.")

    reader = EmlDataExtractor(str(tmp_path))
    emails = list(reader.extract_emails())

    assert len(emails) == 0
