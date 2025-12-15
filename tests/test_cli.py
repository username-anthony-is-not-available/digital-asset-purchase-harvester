"""Tests for the CLI utilities."""

from digital_asset_harvester.cli import build_parser, process_emails
from digital_asset_harvester.telemetry import StructuredLoggerFactory


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["inbox.mbox"])
    assert args.mbox_file == "inbox.mbox"
    assert args.output == "output/purchase_data.csv"


def test_process_emails_collects_metrics():
    class DummyExtractor:
        def process_email(self, _content):
            return {
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

    purchases, metrics = process_emails(
        emails, DummyExtractor(), factory, show_progress=False
    )

    assert len(purchases) == 1
    assert metrics.get("emails_processed") == 1
    assert metrics.get("purchases_detected") == 1
    assert metrics.get("non_purchase_emails") == 0
