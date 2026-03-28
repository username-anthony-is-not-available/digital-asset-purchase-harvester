"""Tests for the CLI utilities."""

from unittest.mock import MagicMock, patch

import pytest

from digital_asset_harvester.cli import build_parser, process_emails, run
from digital_asset_harvester.config import HarvesterSettings
from digital_asset_harvester.telemetry import StructuredLoggerFactory


@pytest.fixture(autouse=True)
def mock_common_cli_deps(mocker):
    m_get_settings = mocker.patch("digital_asset_harvester.cli.get_settings")
    settings = HarvesterSettings(
        enable_blockchain_verification=False,
        vault_path=".vault.json",
        imap_server=None,
        imap_user=None,
        imap_password=None,
        imap_client_id=None,
        imap_authority=None,
        enable_imap=True  # Ensure parser has imap arguments for all tests
    )
    m_get_settings.return_value = settings
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("digital_asset_harvester.cli.configure_logging")
    mocker.patch("digital_asset_harvester.llm.ollama_client.OllamaLLMClient")
    mocker.patch("digital_asset_harvester.cli.EmailPurchaseExtractor")
    m_process_emails = mocker.patch("digital_asset_harvester.cli.process_emails")
    m_process_emails.return_value = ([], MagicMock(get=lambda x: 0))
    mocker.patch("digital_asset_harvester.cli.ensure_directory_exists")
    mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_csv")
    return m_get_settings


def test_build_parser_defaults():
    settings = HarvesterSettings(enable_imap=True)
    parser = build_parser(settings)
    args = parser.parse_args(["extract", "--mbox-file", "inbox.mbox"])
    assert args.mbox_file == "inbox.mbox"
    assert args.output == "output/purchase_data.csv"


def test_build_parser_no_progress():
    settings = HarvesterSettings(enable_imap=True)
    parser = build_parser(settings)
    args = parser.parse_args(["extract", "--mbox-file", "inbox.mbox", "--no-progress"])
    assert not args.progress


def test_process_emails_collects_metrics(mocker):
    # GIVEN
    mock_extractor = MagicMock()
    mock_extractor.process_email.return_value = {
        "has_purchase": True,
        "purchases": [
            {
                "vendor": "Coinbase",
                "currency": "USD",
                "amount": 0.1,
            }
        ],
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
    purchases, metrics = process_emails(emails, mock_extractor, factory, show_progress=False, history_path=None)

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
    m_mbox_extractor = mocker.patch("digital_asset_harvester.cli.MboxDataExtractor")
    m_mbox_extractor.return_value.extract_emails.return_value = []

    # WHEN
    result = run(["extract", "--mbox-file", "test.mbox"])

    # THEN
    assert result == 0
    m_mbox_extractor.assert_called_once_with("test.mbox")


def test_run_imap_gmail_oauth2(mocker, mock_common_cli_deps):
    # GIVEN
    mocker.patch("digital_asset_harvester.cli.get_settings", return_value=HarvesterSettings(enable_imap=True, enable_blockchain_verification=False, vault_path=".vault.json", imap_server=None, imap_user=None, imap_password=None, imap_client_id=None, imap_authority=None, imap_auth_type="gmail_oauth2"))
    m_imap_client = mocker.patch("digital_asset_harvester.cli.ImapClient")
    m_imap_client.return_value.__enter__.return_value.search_emails.return_value = []

    # WHEN
    result = run(
        [
            "extract",
            "--imap",
            "--imap-server",
            "imap.gmail.com",
            "--imap-user",
            "user",
            "--imap-auth-type",
            "gmail_oauth2",
        ]
    )

    # THEN
    assert result == 0
    m_imap_client.assert_called_once_with("imap.gmail.com", "user", None, "gmail_oauth2", None, None)


def test_run_imap_outlook_oauth2(mocker, mock_common_cli_deps):
    # GIVEN
    mocker.patch("digital_asset_harvester.cli.get_settings", return_value=HarvesterSettings(enable_imap=True, enable_blockchain_verification=False, vault_path=".vault.json", imap_server=None, imap_user=None, imap_password=None, imap_client_id=None, imap_authority=None, imap_auth_type="outlook_oauth2"))
    m_imap_client = mocker.patch("digital_asset_harvester.cli.ImapClient")
    m_imap_client.return_value.__enter__.return_value.search_emails.return_value = []

    # WHEN
    result = run(
        [
            "extract",
            "--imap",
            "--imap-server",
            "outlook.office365.com",
            "--imap-user",
            "user",
            "--imap-auth-type",
            "outlook_oauth2",
            "--client-id",
            "client_id",
            "--authority",
            "authority",
        ]
    )

    # THEN
    assert result == 0
    m_imap_client.assert_called_once_with(
        "outlook.office365.com",
        "user",
        None,
        "outlook_oauth2",
        "client_id",
        "authority",
    )


def test_run_gmail_calls_dependencies(mocker, mock_common_cli_deps):
    # GIVEN
    settings = HarvesterSettings(gmail_query="from:coinbase OR from:binance", enable_blockchain_verification=False, vault_path=".vault.json", enable_imap=True)
    mocker.patch("digital_asset_harvester.cli.get_settings", return_value=settings)
    m_gmail_client = mocker.patch("digital_asset_harvester.cli.GmailClient")
    m_gmail_client.return_value.search_emails.return_value = []

    # WHEN
    result = run(["extract", "--gmail", "--gmail-query", "test query"])

    # THEN
    assert result == 0
    m_gmail_client.assert_called_once()
    m_gmail_client.return_value.search_emails.assert_called_once_with(
        "test query", raw=settings.enable_multiprocessing
    )


def test_run_outlook_calls_dependencies(mocker, mock_common_cli_deps):
    # GIVEN
    settings = HarvesterSettings(outlook_query="from:coinbase OR from:binance", enable_blockchain_verification=False, vault_path=".vault.json", outlook_client_id="id", outlook_authority="auth", enable_imap=True)
    mocker.patch("digital_asset_harvester.cli.get_settings", return_value=settings)
    m_outlook_client = mocker.patch("digital_asset_harvester.cli.OutlookClient")
    m_outlook_client.return_value.search_emails.return_value = []

    # WHEN
    result = run(["extract", "--outlook", "--client-id", "id", "--authority", "auth"])

    # THEN
    assert result == 0
    m_outlook_client.assert_called_once_with("id", "auth")
    m_outlook_client.return_value.search_emails.assert_called_once_with(
        "from:coinbase OR from:binance", raw=settings.enable_multiprocessing
    )


def test_run_file_not_found(mocker, caplog):
    # GIVEN
    mocker.patch("digital_asset_harvester.cli.MboxDataExtractor", side_effect=FileNotFoundError("File not found"))

    # WHEN
    result = run(["extract", "--mbox-file", "nonexistent.mbox"])

    # THEN
    assert result == 1
    assert "Error processing mailbox: File not found" in caplog.text


def test_run_imap_calls_dependencies(mocker, mock_common_cli_deps):
    # GIVEN
    mocker.patch("digital_asset_harvester.cli.get_settings", return_value=HarvesterSettings(enable_imap=True, enable_blockchain_verification=False, vault_path=".vault.json", imap_server=None, imap_user=None, imap_password=None, imap_client_id=None, imap_authority=None))
    m_imap_client = mocker.patch("digital_asset_harvester.cli.ImapClient")
    m_imap_client.return_value.__enter__.return_value.search_emails.return_value = []

    # WHEN
    result = run(
        [
            "extract",
            "--imap",
            "--imap-server",
            "imap.example.com",
            "--imap-user",
            "user",
            "--imap-password",
            "pass",
        ]
    )

    # THEN
    assert result == 0
    m_imap_client.assert_called_once_with("imap.example.com", "user", "pass", "password", None, None)


def test_run_koinly_output_enabled(mocker, mock_common_cli_deps):
    # GIVEN
    mocker.patch("digital_asset_harvester.cli.get_settings", return_value=HarvesterSettings(enable_koinly_csv_export=True, enable_blockchain_verification=False, vault_path=".vault.json", enable_imap=True))
    mocker.patch("digital_asset_harvester.cli.MboxDataExtractor")
    m_write_koinly_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_koinly_csv")
    m_write_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_csv")

    # WHEN
    run(["extract", "--mbox-file", "test.mbox", "--output-format", "koinly"])

    # THEN
    m_write_koinly_csv.assert_called_once()
    m_write_csv.assert_not_called()


def test_run_koinly_output_disabled(mocker, caplog, mock_common_cli_deps):
    # GIVEN
    mocker.patch("digital_asset_harvester.cli.get_settings", return_value=HarvesterSettings(enable_koinly_csv_export=False, enable_blockchain_verification=False, vault_path=".vault.json", enable_imap=True))
    mocker.patch("digital_asset_harvester.cli.MboxDataExtractor")
    m_write_koinly_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_koinly_csv")
    m_write_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_csv")

    # WHEN
    run(["extract", "--mbox-file", "test.mbox", "--output-format", "koinly"])

    # THEN
    m_write_koinly_assert_not_called = getattr(m_write_koinly_csv, "assert_not_called")
    m_write_koinly_assert_not_called()
    m_write_csv.assert_called_once()
    assert "Koinly output format is not enabled" in caplog.text


def test_main(mocker):
    # GIVEN
    m_run = mocker.patch("digital_asset_harvester.cli.run", return_value=0)

    # WHEN
    from digital_asset_harvester.cli import main

    result = main()

    # THEN
    assert result == 0
    m_run.assert_called_once()


def test_run_ctc_output_enabled(mocker, mock_common_cli_deps):
    # GIVEN
    mocker.patch("digital_asset_harvester.cli.get_settings", return_value=HarvesterSettings(enable_ctc_csv_export=True, enable_blockchain_verification=False, vault_path=".vault.json", enable_imap=True))
    mocker.patch("digital_asset_harvester.cli.MboxDataExtractor")
    m_write_ctc_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_ctc_csv")
    m_write_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_csv")

    # WHEN
    run(["extract", "--mbox-file", "test.mbox", "--output-format", "cryptotaxcalculator"])

    # THEN
    m_write_ctc_csv.assert_called_once()
    m_write_csv.assert_not_called()


def test_run_cra_output_enabled(mocker, mock_common_cli_deps):
    # GIVEN
    mocker.patch("digital_asset_harvester.cli.get_settings", return_value=HarvesterSettings(enable_cra_csv_export=True, enable_blockchain_verification=False, vault_path=".vault.json", enable_imap=True))
    mocker.patch("digital_asset_harvester.cli.MboxDataExtractor")
    m_write_cra_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_cra_csv")
    m_write_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_csv")

    # WHEN
    run(["extract", "--mbox-file", "test.mbox", "--output-format", "cra"])

    # THEN
    m_write_cra_csv.assert_called_once()
    m_write_csv.assert_not_called()


def test_run_cointracker_output_enabled(mocker, mock_common_cli_deps):
    # GIVEN
    mocker.patch("digital_asset_harvester.cli.get_settings", return_value=HarvesterSettings(enable_cointracker_csv_export=True, enable_blockchain_verification=False, vault_path=".vault.json", enable_imap=True))
    mocker.patch("digital_asset_harvester.cli.MboxDataExtractor")
    m_write_cointracker_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_cointracker_csv")
    m_write_csv = mocker.patch("digital_asset_harvester.cli.write_purchase_data_to_csv")

    # WHEN
    run(["extract", "--mbox-file", "test.mbox", "--output-format", "cointracker"])

    # THEN
    m_write_cointracker_csv.assert_called_once()
    m_write_csv.assert_not_called()
