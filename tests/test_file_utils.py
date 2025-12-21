import os
from unittest.mock import patch
from digital_asset_harvester.utils.file_utils import (
    ensure_directory_exists,
    get_unique_filename,
)

def test_get_unique_filename_returns_unique_name():
    with patch("os.path.exists", side_effect=[True, True, False]):
        assert get_unique_filename("test.txt") == "test_2.txt"

def test_ensure_directory_exists_creates_directory():
    with patch("os.makedirs") as mock_makedirs:
        ensure_directory_exists("path/to/file.txt")
        mock_makedirs.assert_called_once_with("path/to", exist_ok=True)

def test_ensure_directory_exists_handles_no_directory():
    with patch("os.makedirs") as mock_makedirs:
        ensure_directory_exists("file.txt")
        mock_makedirs.assert_not_called()
