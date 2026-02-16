from unittest.mock import MagicMock

import pytest

from digital_asset_harvester.cli import process_emails
from digital_asset_harvester.telemetry import StructuredLoggerFactory


def test_process_emails_progress_callback():
    # Setup
    emails = [
        {"subject": "test1", "sender": "test@example.com", "date": "2023-01-01", "body": "test1"},
        {"subject": "test2", "sender": "test@example.com", "date": "2023-01-01", "body": "test2"},
        {"subject": "test3", "sender": "test@example.com", "date": "2023-01-01", "body": "test3"},
    ]

    extractor = MagicMock()
    extractor.settings.enable_parallel_processing = False
    extractor.settings.enable_multiprocessing = False
    extractor.process_email.return_value = {"has_purchase": False}

    logger_factory = StructuredLoggerFactory(json_output=False)

    progress_updates = []

    def callback(current, total):
        progress_updates.append((current, total))

    # Execute
    process_emails(emails, extractor, logger_factory, show_progress=False, progress_callback=callback)

    # Verify
    assert len(progress_updates) == 3
    assert progress_updates == [(1, 3), (2, 3), (3, 3)]


def test_process_emails_progress_callback_parallel():
    # Setup
    emails = [
        {"subject": "test1", "sender": "test@example.com", "date": "2023-01-01", "body": "test1"},
        {"subject": "test2", "sender": "test@example.com", "date": "2023-01-01", "body": "test2"},
        {"subject": "test3", "sender": "test@example.com", "date": "2023-01-01", "body": "test3"},
    ]

    extractor = MagicMock()
    extractor.settings.enable_parallel_processing = True
    extractor.settings.enable_multiprocessing = False
    extractor.settings.max_workers = 2
    extractor.process_email.return_value = {"has_purchase": False}

    logger_factory = StructuredLoggerFactory(json_output=False)

    progress_updates = []

    def callback(current, total):
        progress_updates.append((current, total))

    # Execute
    process_emails(emails, extractor, logger_factory, show_progress=False, progress_callback=callback)

    # Verify
    assert len(progress_updates) == 3
    # In parallel mode, order might not be guaranteed, but we check if we got all 3
    # and if the last one reported 3/3 (since we update processed_count)
    assert any(p == (3, 3) for p in progress_updates)
    assert all(p[1] == 3 for p in progress_updates)
    # Check that we have 1, 2, 3 in some order (well, current increments so it should be 1, 2, 3)
    sorted_updates = sorted(progress_updates)
    assert sorted_updates == [(1, 3), (2, 3), (3, 3)]
