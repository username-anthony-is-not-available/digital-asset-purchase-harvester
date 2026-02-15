"""Calculate the confidence of an extraction."""

from __future__ import annotations
import enum

from digital_asset_harvester.validation.schemas import PurchaseRecord


class ExtractionMethod(enum.Enum):
    """The method used to extract the purchase information."""

    REGEX = "regex"
    HEURISTIC = "heuristic"
    LLM = "llm"


def calculate_confidence(purchase: PurchaseRecord) -> float:
    """
    Calculate the confidence of an extraction based on the method used.

    If the purchase record already has a confidence score (e.g., from an LLM),
    that score is prioritized. Otherwise, a default score is returned based
    on the extraction method.
    """
    # Prioritize existing confidence if available
    if purchase.confidence is not None:
        return purchase.confidence

    # Fallback to defaults based on method
    if purchase.extraction_method == ExtractionMethod.REGEX.value:
        return 0.95
    elif purchase.extraction_method == ExtractionMethod.HEURISTIC.value:
        return 0.8
    elif purchase.extraction_method == ExtractionMethod.LLM.value:
        return 0.7
    else:
        return 0.5
