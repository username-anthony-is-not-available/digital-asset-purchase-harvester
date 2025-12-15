"""Performance benchmarking tests.

Run with: pytest tests/performance/ --benchmark-only
"""

import pytest

from digital_asset_harvester import get_settings
from digital_asset_harvester.processing.email_purchase_extractor import (
    EmailPurchaseExtractor as ExtractorClass,
)
from digital_asset_harvester.telemetry import StructuredLoggerFactory


# Sample email for benchmarking
SAMPLE_PURCHASE_EMAIL = """Subject: You bought Bitcoin
From: no-reply@coinbase.com
Date: Mon, 15 Jan 2024 10:00:00 -0500

You purchased 0.001 BTC for $45.00 USD.
Transaction ID: TEST123
Date: January 15, 2024
"""

SAMPLE_NEWSLETTER = """Subject: Crypto News Weekly
From: news@cryptonews.com
Date: Mon, 15 Jan 2024 10:00:00 -0500

This week in crypto markets...
Bitcoin, Ethereum, and other cryptocurrencies showed movement.
"""


@pytest.fixture
def extractor():
    """Create extractor instance for benchmarking."""
    settings = get_settings()
    logger_factory = StructuredLoggerFactory(json_output=False)
    return ExtractorClass(settings=settings, logger_factory=logger_factory)


@pytest.mark.performance
@pytest.mark.benchmark(group="preprocessing")
def test_benchmark_preprocessing_crypto_email(benchmark, extractor):
    """Benchmark preprocessing on crypto-related email."""

    def run_preprocessing():
        return extractor._is_likely_crypto_related(SAMPLE_PURCHASE_EMAIL)

    result = benchmark(run_preprocessing)
    assert result is True


@pytest.mark.performance
@pytest.mark.benchmark(group="preprocessing")
def test_benchmark_preprocessing_newsletter(benchmark, extractor):
    """Benchmark preprocessing on newsletter email."""

    def run_preprocessing():
        return extractor._is_likely_crypto_related(SAMPLE_NEWSLETTER)

    result = benchmark(run_preprocessing)
    # Newsletter should still pass crypto check (mentions Bitcoin, Ethereum)


@pytest.mark.performance
@pytest.mark.benchmark(group="preprocessing")
def test_benchmark_purchase_keyword_check(benchmark, extractor):
    """Benchmark purchase keyword detection."""

    def run_check():
        return extractor._is_likely_purchase_related(SAMPLE_PURCHASE_EMAIL)

    result = benchmark(run_check)
    assert result is True


@pytest.mark.performance
@pytest.mark.benchmark(group="validation")
def test_benchmark_email_metadata_extraction(benchmark, extractor):
    """Benchmark email metadata extraction."""

    def run_extraction():
        return extractor._extract_email_metadata(SAMPLE_PURCHASE_EMAIL)

    metadata = benchmark(run_extraction)
    assert "subject" in metadata
    assert "body" in metadata


@pytest.mark.performance
def test_processing_speed_estimate(extractor):
    """Estimate emails per minute processing speed."""
    import time

    # Process 10 sample emails and measure time
    emails = [SAMPLE_PURCHASE_EMAIL] * 5 + [SAMPLE_NEWSLETTER] * 5

    start = time.time()
    processed = 0

    for email_content in emails:
        # Only do preprocessing (no LLM calls for speed test)
        extractor._is_likely_crypto_related(email_content)
        extractor._is_likely_purchase_related(email_content)
        processed += 1

    elapsed = time.time() - start
    emails_per_second = processed / elapsed if elapsed > 0 else 0
    emails_per_minute = emails_per_second * 60

    print(f"\nPreprocessing speed: {emails_per_minute:.0f} emails/minute")

    # Preprocessing should be very fast (thousands per minute)
    assert emails_per_minute > 100, "Preprocessing should handle >100 emails/minute"
