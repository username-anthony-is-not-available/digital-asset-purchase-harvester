import os
import time
from unittest.mock import patch
from digital_asset_harvester.utils.file_utils import (
    ensure_directory_exists,
    get_unique_filename,
)


def test_ensure_directory_exists_creates_directory():
    with patch("os.makedirs") as mock_makedirs:
        ensure_directory_exists("path/to/file.txt")
        mock_makedirs.assert_called_once_with("path/to", exist_ok=True)


def test_ensure_directory_exists_handles_no_directory():
    with patch("os.makedirs") as mock_makedirs:
        ensure_directory_exists("file.txt")
        mock_makedirs.assert_not_called()


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
