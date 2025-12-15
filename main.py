import argparse
import logging

from digital_asset_harvester import (
    EmailPurchaseExtractor,
    MboxDataExtractor,
    OllamaLLMClient,
    MetricsTracker,
    StructuredLoggerFactory,
    log_event,
    get_settings,
    write_purchase_data_to_csv,
)
from digital_asset_harvester.utils import ensure_directory_exists

SETTINGS = get_settings()
log_level_name = SETTINGS.log_level.upper()
log_level = getattr(logging, log_level_name, logging.INFO)

if SETTINGS.log_json_output:
    """Shim script kept for backwards compatibility.

    Prefer running ``python -m digital_asset_harvester.cli`` or the
    ``digital-asset-harvester`` console script created during installation.
    """

    from __future__ import annotations

    from digital_asset_harvester.cli import main


    if __name__ == "__main__":  # pragma: no cover - script entrypoint
        raise SystemExit(main())
    llm_client = OllamaLLMClient(settings=SETTINGS)
