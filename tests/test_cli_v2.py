"""Tests for the CLI utilities."""

from unittest.mock import MagicMock
from digital_asset_harvester.cli import build_parser, process_emails, run
from digital_asset_harvester.telemetry import StructuredLoggerFactory


import pytest

def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["--mbox-file", "inbox.mbox"])
    assert args.mbox_file == "inbox.mbox"
    assert args.output == "output/purchase_data.csv"


def test_build_parser_no_progress():
    parser = build_parser()
    args = parser.parse_args(["--mbox-file", "inbox.mbox", "--no-progress"])
    assert not args.progress


def test_process_emails_collects_metrics(mocker):
    # GIVEN
    mock_extractor = MagicMock()
    mock_extractor.process_email.return_value = {
        "has_purchase": True,
        "purchase_info": {
            "vendor": "Coinbase",
            "currency": "USD",
            "amount": 0.1,
        },
        "processing_notes": [],
    }

    emails = [
        {
            "subject": "Purchase",
            "sender": "noreply@example.com",
            "date": "2024-01-01",
            "body": "You bought crypto",
        }
    ]
    factory = StructuredLoggerFactory(json_output=False)

    # WHEN
    purchases, metrics = process_emails(
        emails, mock_extractor, factory, show_progress=False
    )

    # THEN
    assert len(purchases) == 1
    assert metrics.get("emails_processed") == 1
    assert metrics.get("purchases_detected") == 1
    assert metrics.get("non_purchase_emails") == 0
    mock_extractor.process_email.assert_called_once_with(
        "Subject: Purchase\n\nFrom: noreply@example.com\n\nDate: 2024-01-01\n\nBody: You bought crypto"
    )


def test_run_mbox_calls_dependencies(mocker):
    # GIVEN
    m_get_settings = mocker.patch("digital_asset_harvester.cli.get_settings")
    m_configure_logging = mocker.patch("digital_asset_harvester.cli.configure_logging")
    m_mbox_extractor = mocker.patch("digital_asset_harvester.cli.MboxDataExtractor")
    m_llm_client = mocker.patch("digital_asset_harvester.cli.OllamaLLMClient")
    m_extractor = mocker.patch("digital_asset_harvester.cli.EmailPurchaseExtractor")
    m_process_emails = mocker.patch("digital_asset_harvester.cli.process_emails")
    m_ensure_dir = mocker.patch("digital_asset_harvester.cli.ensure_directory_exists")
    m_write_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_csv")

    m_mbox_extractor.return_value.extract_emails.return_value = []
    m_process_emails.return_value = ([], mocker.MagicMock())

    # WHEN
    result = run(["--mbox-file", "test.mbox"])

    # THEN
    assert result == 0
    m_get_settings.assert_called_once()
    m_configure_logging.assert_called_once()
    m_mbox_extractor.assert_called_once_with("test.mbox")
    m_llm_client.assert_called_once()
    m_extractor.assert_called_once()
    m_process_emails.assert_called_once()
    m_ensure_dir.assert_called_once_with("output/purchase_data.csv")
    m_write_csv.assert_called_once()

def test_run_gmail_calls_dependencies(mocker):
    # GIVEN
    m_get_settings = mocker.patch("digital_asset_harvester.cli.get_settings")
    m_configure_logging = mocker.patch("digital_asset_harvester.cli.configure_logging")
    m_gmail_client = mocker.patch("digital_asset_harvester.cli.GmailClient")
    m_llm_client = mocker.patch("digital_asset_harvester.cli.OllamaLLMClient")
    m_extractor = mocker.patch("digital_asset_harvester.cli.EmailPurchaseExtractor")
    m_process_emails = mocker.patch("digital_asset_harvester.cli.process_emails")
    m_ensure_dir = mocker.patch("digital_asset_harvester.cli.ensure_directory_exists")
    m_write_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_csv")

    m_gmail_client.return_value.search_emails.return_value = []
    m_process_emails.return_value = ([], mocker.MagicMock())

    # WHEN
    result = run(["--gmail", "--gmail-query", "test query"])

    # THEN
    assert result == 0
    m_get_settings.assert_called_once()
    m_configure_logging.assert_called_once()
    m_gmail_client.assert_called_once()
    m_gmail_client.return_value.search_emails.assert_called_once_with("test query")
    m_llm_client.assert_called_once()
    m_extractor.assert_called_once()
    m_process_emails.assert_called_once()
    m_ensure_dir.assert_called_once_with("output/purchase_data.csv")
    m_write_csv.assert_called_once()

def test_run_file_not_found(mocker, caplog):
    # GIVEN
    mocker.patch("digital_asset_harvester.cli.get_settings")
    mocker.patch("digital_asset_harvester.cli.configure_logging")
    mocker.patch("digital_asset_harvester.cli.MboxDataExtractor", side_effect=FileNotFoundError("File not found"))

    # WHEN
    result = run(["--mbox-file", "nonexistent.mbox"])

    # THEN
    assert result == 1
    assert "Error processing mailbox: File not found" in caplog.text


def test_main(mocker):
    # GIVEN
    m_run = mocker.patch("digital_asset_harvester.cli.run", return_value=0)

    # WHEN
    from digital_asset_harvester.cli import main
    result = main()

    # THEN
    assert result == 0
    m_run.assert_called_once()
