"""Test CLI integration for blockchain verification."""

from __future__ import annotations

import logging
import os
from unittest.mock import MagicMock, patch

from digital_asset_harvester.cli import run


@patch("digital_asset_harvester.cli.BlockchainVerifier")
@patch("digital_asset_harvester.cli.process_emails")
@patch("digital_asset_harvester.cli.MboxDataExtractor")
@patch("digital_asset_harvester.cli.write_purchase_data_to_csv")
@patch("os.path.exists")
def test_cli_verify_flag_enabled(mock_exists, mock_write_csv, mock_mbox, mock_process, mock_verifier_class, caplog):
    """Test that the --verify flag triggers verification in the CLI."""
    mock_exists.return_value = False
    mock_mbox.return_value.extract_emails.return_value = []
    mock_process.return_value = ([{"item_name": "BTC", "amount": 1.0}], MagicMock())

    mock_verifier = MagicMock()
    mock_verifier_class.return_value = mock_verifier
    mock_verifier.verify.return_value = {
        "success": True,
        "results": {"BTC": {"status": "match", "harvested_total": 1.0, "on_chain_balance": 1.0}},
    }

    with patch("digital_asset_harvester.cli.get_settings") as mock_settings:
        settings = mock_settings.return_value
        settings.blockchain_wallets = "BTC:addr1"
        settings.enable_multiprocessing = False
        settings.log_level = "INFO"
        settings.log_json_output = False
        settings.enable_debug_output = False
        settings.enable_blockchain_verification = False
        settings.vault_path = ".vault.json"

        # Run CLI with --verify flag
        with caplog.at_level(logging.INFO):
            run(["extract", "--mbox-file", "dummy.mbox", "--verify"])

    assert "Verifying harvested totals against on-chain balances..." in caplog.text
    assert "BTC: MATCH" in caplog.text
    mock_verifier.verify.assert_called_once()
