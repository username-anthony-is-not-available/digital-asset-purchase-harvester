"""Command-line interface for the Digital Asset Purchase Harvester."""

from __future__ import annotations

import argparse
import logging
from typing import Iterable, Optional

from tqdm import tqdm

from digital_asset_harvester import (
    MboxDataExtractor,
    EmailPurchaseExtractor,
    EmailPurchaseExtractor,
    MboxDataExtractor,
    OllamaLLMClient,
    get_settings,
    log_event,
    write_purchase_data_to_csv,
)
from digital_asset_harvester.telemetry import MetricsTracker, StructuredLoggerFactory
from digital_asset_harvester.utils import ensure_directory_exists


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Process an mbox file to extract cryptocurrency purchase information.",
    )
    parser.add_argument("mbox_file", help="Path to the mbox file")
    parser.add_argument(
        "--output",
        default="output/purchase_data.csv",
        help="Output CSV file path",
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

    # Convert to list to get total count for progress bar
    emails_list = list(emails)
    total_emails = len(emails_list)

    # Create progress bar if requested
    iterator = tqdm(
        emails_list,
        desc="Processing emails",
        unit="email",
        disable=not show_progress,
        total=total_emails,
        ncols=100,
    )

    for idx, email in enumerate(iterator, 1):
        if show_progress:
            # Update progress bar description with current email subject
            subject_preview = email.get("subject", "")[:40]
            iterator.set_postfix_str(f"Current: {subject_preview}...")

        logger.info(
            "Processing email %d/%d: %s",
            idx,
            total_emails,
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


def run(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = get_settings()

    logger_factory = configure_logging(settings)
    logger = logging.getLogger(__name__)

    try:
        mbox_reader = MboxDataExtractor(args.mbox_file)
        llm_client = OllamaLLMClient(settings=settings)
        extractor = EmailPurchaseExtractor(
            settings=settings,
            llm_client=llm_client,
            logger_factory=logger_factory,
        )

        emails = mbox_reader.extract_all_emails()
        purchases, metrics = process_emails(
            emails, extractor, logger_factory, show_progress=args.progress
        )

        ensure_directory_exists(args.output)
        write_purchase_data_to_csv(args.output, purchases)

        logger.info("Processing completed")
        logger.info("  Emails processed: %d", metrics.get("emails_processed"))
        logger.info("  Purchases detected: %d", metrics.get("purchases_detected"))
        return 0

    except (FileNotFoundError, IOError) as exc:
        logger.error("Error processing mailbox: %s", exc)
        return 1


def main(argv: Optional[list[str]] = None) -> int:
    return run(argv)
