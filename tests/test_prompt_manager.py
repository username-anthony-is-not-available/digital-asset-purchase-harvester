import pytest
from digital_asset_harvester.prompts.manager import PromptManager


def test_prompt_manager_raises_key_error():
    manager = PromptManager()
    with pytest.raises(KeyError):
        manager.get("nonexistent")
