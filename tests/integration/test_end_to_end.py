"""End-to-end integration tests for the harvester.

These tests require Ollama to be running with the llama3.2:3b model installed.
Run with: pytest tests/integration/ -v --timeout=300
"""

import csv
import mailbox


import pytest

from digital_asset_harvester import (
    EmailPurchaseExtractor,
    MboxDataExtractor,
    OllamaLLMClient,
    get_settings,
    write_purchase_data_to_csv,
)
from digital_asset_harvester.telemetry import StructuredLoggerFactory


@pytest.mark.integration
@pytest.mark.skip(reason="Integration tests require a running Ollama instance")
def test_end_to_end_single_purchase(temp_mbox_file, sample_coinbase_email, tmp_path):
    """Test complete pipeline: mbox → extraction → CSV output."""
    # Create mbox file with one purchase email
    mbox = mailbox.mbox(str(temp_mbox_file))
    msg = mailbox.mboxMessage()

    # Parse the sample email
    lines = sample_coinbase_email.strip().split("\n")
    msg["Subject"] = lines[0].replace("Subject: ", "")
    msg["From"] = lines[1].replace("From: ", "")
    msg["Date"] = lines[2].replace("Date: ", "")
    msg.set_payload("\n".join(lines[4:]))

    mbox.add(msg)
    mbox.close()

    # Process the mbox file
    settings = get_settings()
    mbox_reader = MboxDataExtractor(str(temp_mbox_file))
    llm_client = OllamaLLMClient(settings=settings)
    logger_factory = StructuredLoggerFactory(json_output=False)
    extractor = EmailPurchaseExtractor(
        settings=settings,
        llm_client=llm_client,
        logger_factory=logger_factory,
    )

    emails = mbox_reader.extract_emails()
    purchases = []

    for email in emails:
        email_content = (
            f"Subject: {email.get('subject', '')}\n\n"
            f"From: {email.get('sender', '')}\n\n"
            f"Date: {email.get('date', '')}\n\n"
            f"Body: {email.get('body', '')}"
        )
        result = extractor.process_email(email_content)

        if result.get("has_purchase"):
            purchase_info = result["purchase_info"]
            purchase_info["email_subject"] = email.get("subject", "")
            purchases.append(purchase_info)

    # Write to CSV
    output_file = tmp_path / "purchases.csv"
    write_purchase_data_to_csv(str(output_file), purchases)

    # Verify CSV output
    assert output_file.exists()

    with open(output_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    purchase = rows[0]

    # Verify purchase data (be flexible with LLM extraction)
    assert purchase["vendor"].lower() in ["coinbase", "coinbase.com"]
    assert (
        "btc" in purchase["item_name"].lower()
        or "bitcoin" in purchase["item_name"].lower()
    )
    assert float(purchase["amount"]) > 0
    assert float(purchase["total_spent"]) > 0
    assert purchase["currency"] == "USD"


@pytest.mark.integration
@pytest.mark.skip(reason="Integration tests require a running Ollama instance")
def test_end_to_end_multiple_purchases(
    temp_mbox_file,
    sample_coinbase_email,
    sample_binance_email,
    sample_kraken_email,
    tmp_path,
):
    """Test processing multiple purchase emails."""
    # Create mbox with multiple purchases
    mbox = mailbox.mbox(str(temp_mbox_file))

    for email_content in [
        sample_coinbase_email,
        sample_binance_email,
        sample_kraken_email,
    ]:
        msg = mailbox.mboxMessage()
        lines = email_content.strip().split("\n")
        msg["Subject"] = lines[0].replace("Subject: ", "")
        msg["From"] = lines[1].replace("From: ", "")
        msg["Date"] = lines[2].replace("Date: ", "")
        msg.set_payload("\n".join(lines[4:]))
        mbox.add(msg)

    mbox.close()

    # Process
    settings = get_settings()
    mbox_reader = MboxDataExtractor(str(temp_mbox_file))
    llm_client = OllamaLLMClient(settings=settings)
    logger_factory = StructuredLoggerFactory(json_output=False)
    extractor = EmailPurchaseExtractor(
        settings=settings,
        llm_client=llm_client,
        logger_factory=logger_factory,
    )

    emails = mbox_reader.extract_emails()
    purchases = []

    for email in emails:
        email_content = (
            f"Subject: {email.get('subject', '')}\n\n"
            f"From: {email.get('sender', '')}\n\n"
            f"Date: {email.get('date', '')}\n\n"
            f"Body: {email.get('body', '')}"
        )
        result = extractor.process_email(email_content)

        if result.get("has_purchase"):
            purchase_info = result["purchase_info"]
            purchase_info["email_subject"] = email.get("subject", "")
            purchases.append(purchase_info)

    # Should detect 3 purchases
    assert len(purchases) >= 2, f"Expected at least 2 purchases, got {len(purchases)}"

    # Verify we got different vendors
    vendors = {p["vendor"].lower() for p in purchases}
    assert len(vendors) >= 2, "Should detect purchases from multiple vendors"


@pytest.mark.integration
@pytest.mark.skip(reason="Integration tests require a running Ollama instance")
def test_newsletter_filtering(temp_mbox_file, sample_newsletter_email, tmp_path):
    """Test that newsletters are correctly filtered out."""
    # Create mbox with newsletter
    mbox = mailbox.mbox(str(temp_mbox_file))
    msg = mailbox.mboxMessage()
    lines = sample_newsletter_email.strip().split("\n")
    msg["Subject"] = lines[0].replace("Subject: ", "")
    msg["From"] = lines[1].replace("From: ", "")
    msg["Date"] = lines[2].replace("Date: ", "")
    msg.set_payload("\n".join(lines[4:]))
    mbox.add(msg)
    mbox.close()

    # Process
    settings = get_settings()
    mbox_reader = MboxDataExtractor(str(temp_mbox_file))
    llm_client = OllamaLLMClient(settings=settings)
    logger_factory = StructuredLoggerFactory(json_output=False)
    extractor = EmailPurchaseExtractor(
        settings=settings,
        llm_client=llm_client,
        logger_factory=logger_factory,
    )

    emails = mbox_reader.extract_emails()
    purchases = []

    for email in emails:
        email_content = (
            f"Subject: {email.get('subject', '')}\n\n"
            f"From: {email.get('sender', '')}\n\n"
            f"Date: {email.get('date', '')}\n\n"
            f"Body: {email.get('body', '')}"
        )
        result = extractor.process_email(email_content)

        if result.get("has_purchase"):
            purchases.append(result["purchase_info"])

    # Newsletter should NOT be detected as purchase
    assert len(purchases) == 0, "Newsletter should not be detected as purchase"
