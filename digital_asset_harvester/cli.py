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
from digital_asset_harvester.ingest.gmail_client import GmailClient
from digital_asset_harvester.ingest.imap_client import ImapClient

# Optional Koinly writer (not yet implemented)
try:
    from digital_asset_harvester.output.koinly_writer import (
        write_purchase_data_to_koinly_csv,
    )
    KOINLY_AVAILABLE = True
except ImportError:
    KOINLY_AVAILABLE = False

from digital_asset_harvester.telemetry import MetricsTracker, StructuredLoggerFactory
from digital_asset_harvester.utils import ensure_directory_exists


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
        source_group.add_argument(
            "--imap", action="store_true", help="Import emails from an IMAP server"
        )
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
        choices=["csv", "koinly"],
        default="csv",
        help="The output format (default: csv)",
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


def process_emails(
    emails: Iterable[dict],
    extractor: EmailPurchaseExtractor,
    logger_factory: StructuredLoggerFactory,
    show_progress: bool = True,
) -> tuple[list[dict], MetricsTracker]:
    logger = logging.getLogger(__name__)
    metrics = MetricsTracker()
    app_logger = logger_factory.build(
        "digital_asset_harvester.app",
        default_fields={"component": "cli"},
    )

    results: list[dict] = []

    iterator = tqdm(
        emails,
        desc="Processing emails",
        unit="email",
        disable=not show_progress,
        ncols=100,
    )

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

        email_content = (
            f"Subject: {email.get('subject', '')}\n\n"
            f"From: {email.get('sender', '')}\n\n"
            f"Date: {email.get('date', '')}\n\n"
            f"Body: {email.get('body', '')}"
        )
        result = extractor.process_email(email_content)

        if "processing_notes" in result:
            for note in result["processing_notes"]:
                logger.debug("Email %d: %s", idx, note)

        if result.get("has_purchase"):
            purchase_info = result["purchase_info"]
            purchase_info["email_subject"] = email.get("subject", "")
            results.append(purchase_info)
            metrics.increment("purchases_detected")
            log_event(
                app_logger,
                "purchase_detected",
                vendor=purchase_info.get("vendor", "unknown"),
                currency=purchase_info.get("currency", ""),
                amount=purchase_info.get("amount", 0),
            )
        else:
            metrics.increment("non_purchase_emails")

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
) -> None:
    """Helper to process emails and save the results."""
    purchases, metrics = process_emails(
        emails, extractor, logger_factory, show_progress=show_progress
    )
    ensure_directory_exists(output_path)

    logger = logging.getLogger(__name__)

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
            write_purchase_data_to_csv(purchases, output_path)
    else:  # 'csv'
        logger.info("Writing output in standard CSV format to %s", output_path)
        write_purchase_data_to_csv(purchases, output_path)

    logger.info("Processing completed")
    logger.info("  Emails processed: %d", metrics.get("emails_processed"))
    logger.info("  Purchases detected: %d", metrics.get("purchases_detected"))


def run(argv: Optional[list[str]] = None) -> int:
    settings = get_settings()
    parser = build_parser(settings)
    args = parser.parse_args(argv)

    logger_factory = configure_logging(settings)
    logger = logging.getLogger(__name__)

    try:
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
            )
        return 0

    except (FileNotFoundError, IOError) as exc:
        logger.error("Error processing mailbox: %s", exc)
        return 1


def main(argv: Optional[list[str]] = None) -> int:
    return run(argv)
