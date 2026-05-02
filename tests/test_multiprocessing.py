from unittest.mock import MagicMock

import pytest

from digital_asset_harvester.cli import HarvesterSettings, process_emails
from digital_asset_harvester.processing.email_purchase_extractor import EmailPurchaseExtractor
from digital_asset_harvester.telemetry import StructuredLoggerFactory


def test_process_emails_uses_multiprocessing(mocker, tmp_path):
    # GIVEN
    settings = HarvesterSettings(
        enable_multiprocessing=True,
        max_workers=3,
        llm_cache_file=str(tmp_path / ".llm_cache.json")
    )
    mock_extractor = MagicMock()
    mock_extractor.settings = settings
    factory = StructuredLoggerFactory(json_output=False)

    emails = ["raw email 1", "raw email 2"]

    m_executor = mocker.patch("concurrent.futures.ProcessPoolExecutor")
    m_as_completed = mocker.patch("concurrent.futures.as_completed", return_value=[])

    # WHEN
    process_emails(
        emails,
        mock_extractor,
        factory,
        show_progress=False,
        history_path=str(tmp_path / ".processed_hashes.json")
    )

    # THEN
    # We now use initializer and initargs
    args, kwargs = m_executor.call_args
    assert kwargs["max_workers"] == 3
    assert "initializer" in kwargs
    assert "initargs" in kwargs


def test_cli_multiprocessing_flag():
    from digital_asset_harvester.cli import build_parser

    settings = HarvesterSettings()
    parser = build_parser(settings)
    args = parser.parse_args(["extract", "--mbox-file", "test.mbox", "--multiprocessing"])
    assert args.multiprocessing is True
