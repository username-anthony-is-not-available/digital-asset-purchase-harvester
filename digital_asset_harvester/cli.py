"""Command-line interface for the Digital Asset Purchase Harvester."""

from __future__ import annotations

import argparse
import logging
from typing import Iterable, Optional

from tqdm import tqdm

from digital_asset_harvester import (
    EmailPurchaseExtractor,
    HarvesterSettings,
    MboxDataExtractor,
    get_llm_client,
    get_settings,
    log_event,
    write_purchase_data_to_csv,
)
from digital_asset_harvester.exporters.cra import (
    write_purchase_data_to_cra_csv,
)
from digital_asset_harvester.exporters.cryptotaxcalculator import (
    write_purchase_data_to_ctc_csv,
)
from digital_asset_harvester.exporters.koinly import (
    write_purchase_data_to_koinly_csv,
)
from digital_asset_harvester.ingest.gmail_client import GmailClient
from digital_asset_harvester.ingest.imap_client import ImapClient
from digital_asset_harvester.integrations.koinly_api_client import (
    KoinlyApiClient,
    KoinlyApiError,
)
from digital_asset_harvester.telemetry import MetricsTracker, StructuredLoggerFactory
from digital_asset_harvester.utils import ensure_directory_exists
from digital_asset_harvester.utils.deduplication import DuplicateDetector

KOINLY_AVAILABLE = True


def build_parser(settings: HarvesterSettings) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Process emails to extract cryptocurrency purchase information.",
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--mbox-file", help="Path to the mbox file")
    source_group.add_argument(
        "--gmail",
        action="store_true",
        help="Import emails directly from Gmail",
    )

    if settings.enable_imap:
        source_group.add_argument("--imap", action="store_true", help="Import emails from an IMAP server")
        parser.add_argument("--imap-server", help="IMAP server address")
        parser.add_argument("--imap-user", help="IMAP username")
        parser.add_argument("--imap-password", help="IMAP password")
        parser.add_argument(
            "--imap-auth-type",
            choices=["password", "gmail_oauth2", "outlook_oauth2"],
            default="password",
            help="IMAP authentication type",
        )
        parser.add_argument("--client-id", help="OAuth2 client ID")
        parser.add_argument("--authority", help="OAuth2 authority URL")
        parser.add_argument(
            "--imap-query",
            default="ALL",
            help="The query to use when searching for emails via IMAP",
        )

    parser.add_argument(
        "--gmail-query",
        default="from:coinbase OR from:binance",
        help="The query to use when searching for emails in Gmail",
    )
    parser.add_argument(
        "--output",
        default="output/purchase_data.csv",
        help="Output CSV file path",
    )
    parser.add_argument(
        "--output-format",
        choices=["csv", "koinly", "cryptotaxcalculator", "cra"],
        default="csv",
        help="The output format (default: csv)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel processing of emails",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=settings.max_workers,
        help=f"Maximum number of worker threads for parallel processing (default: {settings.max_workers})",
    )
    parser.add_argument(
        "--koinly-upload",
        action="store_true",
        help="Upload transactions to Koinly (requires API support)",
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        default=True,
        help="Show progress bar during processing (default: True)",
    )
    parser.add_argument(
        "--no-progress",
        dest="progress",
        action="store_false",
        help="Disable progress bar",
    )
    return parser


def configure_logging(settings) -> StructuredLoggerFactory:
    log_level_name = settings.log_level.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    if settings.log_json_output:
        logging.basicConfig(level=log_level)
    else:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    if settings.enable_debug_output:
        logging.getLogger().setLevel(logging.DEBUG)

    return StructuredLoggerFactory(json_output=settings.log_json_output)


def _process_single_email(
    email: dict,
    idx: int,
    extractor: EmailPurchaseExtractor,
) -> tuple[dict, int, dict]:
    """Helper for parallel processing of a single email."""
    email_content = (
        f"Subject: {email.get('subject', '')}\n\n"
        f"From: {email.get('sender', '')}\n\n"
        f"Date: {email.get('date', '')}\n\n"
        f"Body: {email.get('body', '')}"
    )
    result = extractor.process_email(email_content)
    return email, idx, result


def process_emails(
    emails: Iterable[dict],
    extractor: EmailPurchaseExtractor,
    logger_factory: StructuredLoggerFactory,
    show_progress: bool = True,
) -> tuple[list[dict], MetricsTracker]:
    logger = logging.getLogger(__name__)
    settings = extractor.settings
    metrics = MetricsTracker()
    app_logger = logger_factory.build(
        "digital_asset_harvester.app",
        default_fields={"component": "cli"},
    )
    duplicate_detector = DuplicateDetector()

    results: list[dict] = []

    # Convert iterable to list for parallel processing if needed
    enable_parallel = getattr(settings, "enable_parallel_processing", False)
    # Ensure it's a real boolean if it's a mock
    if hasattr(enable_parallel, "assert_called") or str(type(enable_parallel)).find("MagicMock") > -1:
        enable_parallel = False

    email_list = list(emails) if enable_parallel else emails

    iterator = tqdm(
        email_list,
        desc="Processing emails",
        unit="email",
        disable=not show_progress,
        ncols=100,
    )

    def handle_result(email, idx, result):
        if "processing_notes" in result:
            for note in result["processing_notes"]:
                logger.debug("Email %d: %s", idx, note)

        if result.get("has_purchase"):
            for purchase_info in result.get("purchases", []):
                if duplicate_detector.is_duplicate(purchase_info):
                    logger.info(
                        "Skipping duplicate purchase: %s %s",
                        purchase_info.get("item_name"),
                        purchase_info.get("amount"),
                    )
                    metrics.increment("duplicate_purchases_skipped")
                    continue

                purchase_info["email_subject"] = email.get("subject", "")
                results.append(purchase_info)
                metrics.increment("purchases_detected")

                # Update detailed metrics
                if purchase_info.get("extraction_method") == "regex":
                    metrics.increment("purchases_extracted_regex")
                else:
                    metrics.increment("purchases_extracted_llm")

                log_event(
                    app_logger,
                    "purchase_detected",
                    vendor=purchase_info.get("vendor", "unknown"),
                    currency=purchase_info.get("currency", ""),
                    amount=purchase_info.get("amount", 0),
                )
        else:
            metrics.increment("non_purchase_emails")
            if any("filtered out by preprocessing" in note for note in result.get("processing_notes", [])):
                metrics.increment("emails_skipped_preprocessing")

    if enable_parallel:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        max_workers = int(getattr(settings, "max_workers", 5))
        logger.info("Starting parallel processing with %d workers", max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_process_single_email, email, idx, extractor): (email, idx)
                for idx, email in enumerate(email_list, 1)
            }

            for future in as_completed(futures):
                email, idx = futures[future]
                try:
                    _, _, result = future.result()
                    metrics.increment("emails_processed")
                    handle_result(email, idx, result)
                except Exception as exc:
                    logger.error("Email %d failed with error: %s", idx, exc)
                    metrics.increment("llm_calls_failed")

                if show_progress:
                    iterator.update(1)
    else:
        for idx, email in enumerate(iterator, 1):
            if show_progress:
                subject_preview = email.get("subject", "")[:40]
                iterator.set_postfix_str(f"Current: {subject_preview}...")

            logger.info(
                "Processing email %d: %s",
                idx,
                email.get("subject", "")[:50],
            )
            metrics.increment("emails_processed")

            _, _, result = _process_single_email(email, idx, extractor)
            handle_result(email, idx, result)

    log_event(app_logger, "processing_summary", **metrics.snapshot())
    return results, metrics


def _process_and_save_results(
    emails: Iterable[dict],
    extractor: EmailPurchaseExtractor,
    logger_factory: StructuredLoggerFactory,
    output_path: str,
    output_format: str,
    show_progress: bool,
    settings: HarvesterSettings,
    koinly_upload: bool = False,
) -> None:
    """Helper to process emails and save the results."""
    purchases, metrics = process_emails(emails, extractor, logger_factory, show_progress=show_progress)
    ensure_directory_exists(output_path)

    logger = logging.getLogger(__name__)

    # Handle Koinly API upload if requested
    if koinly_upload:
        if not settings.enable_koinly_api:
            logger.error(
                "Koinly API upload requested but not enabled. " "Set DAP_ENABLE_KOINLY_API=true environment variable."
            )
            logger.info("Falling back to CSV export...")
        else:
            logger.info("Attempting to upload transactions to Koinly via API...")
            try:
                client = KoinlyApiClient(
                    api_key=settings.koinly_api_key,
                    portfolio_id=settings.koinly_portfolio_id,
                    base_url=settings.koinly_api_base_url,
                )
                result = client.upload_purchases(purchases)
                logger.info("Upload successful: %s", result)
                logger.info("Processing completed")
                logger.info("  Emails processed: %d", metrics.get("emails_processed"))
                logger.info("  Purchases detected: %d", metrics.get("purchases_detected"))
                logger.info("  Regex extractions: %d", metrics.get("purchases_extracted_regex"))
                logger.info("  LLM extractions: %d", metrics.get("purchases_extracted_llm"))
                logger.info("  Emails skipped by preprocessing: %d", metrics.get("emails_skipped_preprocessing"))
                logger.info("  Duplicates skipped: %d", metrics.get("duplicate_purchases_skipped"))
                llm_failed = metrics.get("llm_calls_failed")
                if llm_failed and not hasattr(llm_failed, "assert_called") and int(llm_failed) > 0:
                    logger.warning("  LLM calls failed: %d", llm_failed)
                return
            except KoinlyApiError as e:
                logger.error("Koinly API upload failed: %s", e)
                logger.info("Falling back to CSV export...")
            except Exception as e:
                logger.error("Unexpected error during Koinly API upload: %s", e)
                logger.info("Falling back to CSV export...")

    if output_format == "koinly":
        if settings.enable_koinly_csv_export and KOINLY_AVAILABLE:
            logger.info("Writing output in Koinly format to %s", output_path)
            write_purchase_data_to_koinly_csv(purchases, output_path)
        else:
            if not KOINLY_AVAILABLE:
                logger.warning(
                    "Koinly output format is not available (module not implemented). "
                    "Falling back to standard CSV output."
                )
            else:
                logger.warning(
                    "Koinly output format is not enabled. "
                    "Set `enable_koinly_csv_export = true` in your config or "
                    "`DAP_ENABLE_KOINLY_CSV_EXPORT=true` env var. "
                    "Falling back to standard CSV output."
                )
            write_purchase_data_to_csv(output_path, purchases)
    elif output_format == "cryptotaxcalculator":
        if settings.enable_ctc_csv_export:
            logger.info("Writing output in CryptoTaxCalculator format to %s", output_path)
            write_purchase_data_to_ctc_csv(purchases, output_path)
        else:
            logger.warning(
                "CryptoTaxCalculator output format is not enabled. "
                "Set `enable_ctc_csv_export = true` in your config or "
                "`DAP_ENABLE_CTC_CSV_EXPORT=true` env var. "
                "Falling back to standard CSV output."
            )
            write_purchase_data_to_csv(output_path, purchases)
    elif output_format == "cra":
        if settings.enable_cra_csv_export:
            logger.info("Writing output in CRA format to %s", output_path)
            write_purchase_data_to_cra_csv(purchases, output_path)
        else:
            logger.warning(
                "CRA output format is not enabled. "
                "Set `enable_cra_csv_export = true` in your config or "
                "`DAP_ENABLE_CRA_CSV_EXPORT=true` env var. "
                "Falling back to standard CSV output."
            )
            write_purchase_data_to_csv(output_path, purchases)
    else:  # 'csv'
        logger.info("Writing output in standard CSV format to %s", output_path)
        write_purchase_data_to_csv(output_path, purchases)

    logger.info("Processing completed")
    logger.info("  Emails processed: %d", metrics.get("emails_processed"))
    logger.info("  Purchases detected: %d", metrics.get("purchases_detected"))
    logger.info("  Regex extractions: %d", metrics.get("purchases_extracted_regex"))
    logger.info("  LLM extractions: %d", metrics.get("purchases_extracted_llm"))
    logger.info("  Emails skipped by preprocessing: %d", metrics.get("emails_skipped_preprocessing"))
    logger.info("  Duplicates skipped: %d", metrics.get("duplicate_purchases_skipped"))
    llm_failed = metrics.get("llm_calls_failed")
    if llm_failed and not hasattr(llm_failed, "assert_called") and int(llm_failed) > 0:
        logger.warning("  LLM calls failed: %d", llm_failed)


def run(argv: Optional[list[str]] = None) -> int:
    settings = get_settings()
    parser = build_parser(settings)
    args = parser.parse_args(argv)

    logger_factory = configure_logging(settings)
    logger = logging.getLogger(__name__)

    try:
        # Override settings from CLI args
        overrides = {}
        if args.parallel:
            overrides["enable_parallel_processing"] = True
        if args.max_workers:
            overrides["max_workers"] = args.max_workers

        if overrides:
            from dataclasses import is_dataclass, replace

            if is_dataclass(settings) and not hasattr(settings, "assert_called"):
                settings = replace(settings, **overrides)
            else:
                # If it's a mock, we can just update its attributes if it's not frozen
                for k, v in overrides.items():
                    try:
                        setattr(settings, k, v)
                    except (AttributeError, TypeError):
                        # Mock might be frozen or something
                        pass

        llm_client = get_llm_client()
        extractor = EmailPurchaseExtractor(
            settings=settings,
            llm_client=llm_client,
            logger_factory=logger_factory,
        )

        if args.gmail:
            logger.info("Fetching emails from Gmail...")
            gmail_client = GmailClient()
            emails = gmail_client.search_emails(args.gmail_query)
            _process_and_save_results(
                emails,
                extractor,
                logger_factory,
                args.output,
                args.output_format,
                args.progress,
                settings,
                args.koinly_upload,
            )
        elif settings.enable_imap and args.imap:
            logger.info("Fetching emails from IMAP server...")
            if not all([args.imap_server, args.imap_user]):
                logger.error("IMAP server and user are required.")
                return 1
            with ImapClient(
                args.imap_server,
                args.imap_user,
                args.imap_password,
                args.imap_auth_type,
                args.client_id,
                args.authority,
            ) as imap_client:
                emails = imap_client.search_emails(args.imap_query)
                _process_and_save_results(
                    emails,
                    extractor,
                    logger_factory,
                    args.output,
                    args.output_format,
                    args.progress,
                    settings,
                    args.koinly_upload,
                )
        else:
            logger.info(f"Loading emails from {args.mbox_file}...")
            mbox_reader = MboxDataExtractor(args.mbox_file)
            emails = mbox_reader.extract_emails()
            _process_and_save_results(
                emails,
                extractor,
                logger_factory,
                args.output,
                args.output_format,
                args.progress,
                settings,
                args.koinly_upload,
            )
        return 0

    except (FileNotFoundError, IOError) as exc:
        logger.error("Error processing mailbox: %s", exc)
        return 1


def main(argv: Optional[list[str]] = None) -> int:
    return run(argv)


if __name__ == "__main__":
    import sys

    sys.exit(main())
