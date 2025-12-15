"""Compatibility shim for legacy imports.

This module re-exports public APIs from :mod:`digital_asset_harvester` so
existing imports continue to work while the codebase transitions to the
packaged layout.
"""

from digital_asset_harvester.processing.email_purchase_extractor import (
    EmailPurchaseExtractor,
    PurchaseInfo,
)

__all__ = ["EmailPurchaseExtractor", "PurchaseInfo"]
