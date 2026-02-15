import os
import json
import tempfile
import pytest
from digital_asset_harvester.utils.sync_state import SyncState


def test_sync_state_persistence():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        state_file = tmp.name

    try:
        sync_state = SyncState(state_file=state_file)

        # Initial state should be 0
        assert sync_state.get_last_uid("imap.example.com", "user@example.com", "INBOX") == 0

        # Set a UID
        sync_state.set_last_uid("imap.example.com", "user@example.com", "INBOX", 123)
        assert sync_state.get_last_uid("imap.example.com", "user@example.com", "INBOX") == 123

        # Verify it's in the file
        with open(state_file, "r") as f:
            data = json.load(f)
            assert data["imap.example.com|user@example.com|INBOX"] == 123

        # Create a new instance and verify it loads the state
        new_sync_state = SyncState(state_file=state_file)
        assert new_sync_state.get_last_uid("imap.example.com", "user@example.com", "INBOX") == 123

    finally:
        if os.path.exists(state_file):
            os.remove(state_file)


def test_sync_state_invalid_json():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        state_file = tmp.name
        tmp.write(b"invalid json")

    try:
        # Should not crash and should return default state
        sync_state = SyncState(state_file=state_file)
        assert sync_state.get_last_uid("any", "any", "any") == 0
    finally:
        if os.path.exists(state_file):
            os.remove(state_file)
