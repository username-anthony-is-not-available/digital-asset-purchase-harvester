"""Tests for the metrics tracker."""

from digital_asset_harvester.telemetry import MetricsTracker


def test_metrics_tracker_counts():
    tracker = MetricsTracker()
    tracker.increment("emails_processed")
    tracker.increment("emails_processed", 2)
    tracker.increment("purchases_detected")

    assert tracker.get("emails_processed") == 3
    assert tracker.get("purchases_detected") == 1
    snapshot = tracker.snapshot()
    assert snapshot == {"emails_processed": 3, "purchases_detected": 1}
