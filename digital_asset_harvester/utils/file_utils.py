"""File system utilities."""

import os
import time


def ensure_directory_exists(filepath: str):
    """
    Ensures that the directory for the given filepath exists.

    Args:
        filepath (str): The path to the file.
    """
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_unique_filename(directory: str, filename: str) -> str:
    """
    Generates a unique filename by appending a timestamp if the file already exists.

    Args:
        directory (str): The directory where the file will be saved.
        filename (str): The desired filename.

    Returns:
        str: A unique filepath.
    """
    base, ext = os.path.splitext(filename)
    filepath = os.path.join(directory, filename)
    if os.path.exists(filepath):
        timestamp = int(time.time())
        filepath = os.path.join(directory, f"{base}_{timestamp}{ext}")
    return filepath
