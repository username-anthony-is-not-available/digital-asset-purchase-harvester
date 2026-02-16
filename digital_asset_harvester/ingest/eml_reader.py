import os
import email
from typing import Any, Dict, Generator
from pathlib import Path

from .email_parser import message_to_dict


class EmlDataExtractor:
    """Extracts data from a directory of .eml files."""

    def __init__(self, eml_dir: str):
        self.eml_dir = eml_dir

    def extract_emails(self, raw: bool = False) -> Generator[Any, None, None]:
        """
        Walks the directory and extracts emails from .eml files.

        Args:
            raw: If True, yields raw message strings. Otherwise, yields dictionaries.
        """
        eml_path = Path(self.eml_dir)
        if not eml_path.exists() or not eml_path.is_dir():
            return

        for root, _, files in os.walk(self.eml_dir):
            for file in files:
                if file.lower().endswith(".eml"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "rb") as f:
                            msg = email.message_from_binary_file(f)

                        if raw:
                            yield msg.as_string()
                        else:
                            yield message_to_dict(msg)
                    except Exception:
                        # Skip files that can't be parsed
                        continue
