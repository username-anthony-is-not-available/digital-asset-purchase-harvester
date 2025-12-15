"""Tests for utility helpers."""

from digital_asset_harvester.utils.file_utils import get_unique_filename


def test_get_unique_filename(tmp_path):
    base = tmp_path / "output.csv"
    base.write_text("data")

    unique = get_unique_filename(str(base))
    assert unique != str(base)
    assert unique.endswith("_1.csv")
