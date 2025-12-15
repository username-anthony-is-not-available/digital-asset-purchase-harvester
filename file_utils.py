"""Compatibility shim for legacy imports."""

from digital_asset_harvester.utils.file_utils import (
    ensure_directory_exists,
    get_unique_filename,
)

__all__ = ["ensure_directory_exists", "get_unique_filename"]
