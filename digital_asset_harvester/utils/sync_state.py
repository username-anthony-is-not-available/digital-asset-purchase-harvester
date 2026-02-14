import json
import os
from typing import Dict, Any

class SyncState:
    """Manages persistent sync state for IMAP accounts."""

    def __init__(self, state_file: str = ".sync_state.json") -> None:
        self.state_file = state_file
        self.state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Loads the state from the JSON file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_state(self) -> None:
        """Saves the current state to the JSON file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except IOError:
            pass

    def _get_key(self, server: str, user: str, folder: str) -> str:
        """Generates a unique key for the given account and folder."""
        return f"{server}|{user}|{folder}"

    def get_last_uid(self, server: str, user: str, folder: str) -> int:
        """Retrieves the last processed UID for the given account and folder."""
        key = self._get_key(server, user, folder)
        return self.state.get(key, 0)

    def set_last_uid(self, server: str, user: str, folder: str, uid: int) -> None:
        """Sets the last processed UID for the given account and folder."""
        key = self._get_key(server, user, folder)
        self.state[key] = uid
        self._save_state()
