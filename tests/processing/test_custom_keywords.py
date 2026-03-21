import os
import pytest
import tempfile
from digital_asset_harvester.processing.email_purchase_extractor import EmailPurchaseExtractor
from digital_asset_harvester.config import HarvesterSettings

def test_load_custom_keywords():
    """Test that custom keywords are correctly loaded from a file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write("niche_exchange\n")
        tmp.write("# comment line\n")
        tmp.write("another_keyword\n")
        tmp.write("\n")
        tmp_path = tmp.name

    try:
        settings = HarvesterSettings(custom_keywords_file=tmp_path)
        extractor = EmailPurchaseExtractor(settings=settings)

        keywords = extractor._load_custom_keywords()
        assert "niche_exchange" in keywords
        assert "another_keyword" in keywords
        assert "# comment line" not in keywords
        assert "" not in keywords
        assert len(keywords) == 2
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_custom_keyword_prevents_filtering():
    """Test that a custom keyword prevents an email from being filtered out."""
    # Use keywords that are definitely NOT in the default lists
    email_content = (
        "Subject: Your MAGICWORD info\n"
        "From: service@example.com\n\n"
        "This is a MAGICWORD notification."
    )

    # First, verify it's filtered out with default settings
    default_settings = HarvesterSettings(custom_keywords_file="non_existent.txt")
    default_extractor = EmailPurchaseExtractor(settings=default_settings)
    assert default_extractor._should_skip_llm_analysis(email_content) is True

    # Now, add MAGICWORD as a custom keyword
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write("MAGICWORD\n")
        tmp_path = tmp.name

    try:
        custom_settings = HarvesterSettings(custom_keywords_file=tmp_path)
        custom_extractor = EmailPurchaseExtractor(settings=custom_settings)

        # Should NOT skip now because MAGICWORD is in the instance-level patterns
        assert custom_extractor._should_skip_llm_analysis(email_content) is False

        # Verify it's considered crypto related (since we add custom keywords to exchanges)
        assert custom_extractor._is_likely_crypto_related(email_content) is True

        # Verify it's considered purchase related (since we add custom keywords to purchase_keywords)
        assert custom_extractor._is_likely_purchase_related(email_content) is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_empty_custom_keywords_file():
    """Test that an empty or missing file doesn't cause errors."""
    settings = HarvesterSettings(custom_keywords_file="non_existent_file.txt")
    extractor = EmailPurchaseExtractor(settings=settings)
    assert extractor._load_custom_keywords() == []
