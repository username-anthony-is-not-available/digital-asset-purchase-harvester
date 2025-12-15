"""General filesystem helpers."""

import os
from typing import Final


def get_unique_filename(base_filename: str) -> str:
    directory = os.path.dirname(base_filename)
    filename = os.path.basename(base_filename)

    name, ext = os.path.splitext(filename)

    counter: int = 1
    candidate: str = base_filename
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{name}_{counter}{ext}")
        counter += 1

    return candidate


def ensure_directory_exists(filepath: str) -> None:
    directory: Final[str] = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)
