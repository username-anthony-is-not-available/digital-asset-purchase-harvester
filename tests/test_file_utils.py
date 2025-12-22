"""Tests for utility helpers."""

import os
import time
from digital_asset_harvester.utils.file_utils import get_unique_filename


def test_get_unique_filename(tmp_path):
    directory = str(tmp_path)
    filename = "output.csv"
    filepath = os.path.join(directory, filename)
    with open(filepath, "w") as f:
        f.write("data")

    unique_filepath = get_unique_filename(directory, filename)
    assert unique_filepath != filepath
    base, ext = os.path.splitext(unique_filepath)
    assert ext == ".csv"
    assert base.startswith(os.path.join(directory, "output_"))
    timestamp_str = base.split("_")[-1]
    assert timestamp_str.isdigit()
    timestamp = int(timestamp_str)
    assert abs(time.time() - timestamp) < 5  # Allow for a small delay
