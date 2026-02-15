"""Tests for blockchain verification integration."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from digital_asset_harvester.integrations.blockchain_verifier import BlockchainVerifier
from tests.mock_blockchain_core import WalletClient


def test_parse_wallets():
    """Verify that the wallet configuration string is parsed correctly."""
    config = "BTC:addr1,ETH:addr2, LTC : addr3 "
    verifier = BlockchainVerifier(config)
    assert verifier.wallets == {
        "BTC": "addr1",
        "ETH": "addr2",
        "LTC": "addr3",
    }


def test_parse_wallets_empty():
    """Verify handling of empty wallet configuration."""
    verifier = BlockchainVerifier("")
    assert verifier.wallets == {}


@patch("digital_asset_harvester.integrations.blockchain_verifier.WalletClient", WalletClient)
def test_verify_match():
    """Verify successful matching of harvested totals and on-chain balances."""
    # Mock balance for BTC at this address is 1.5
    config = "BTC:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    verifier = BlockchainVerifier(config)

    purchases = [
        {"item_name": "BTC", "amount": 1.0},
        {"item_name": "BTC", "amount": 0.5},
    ]

    report = verifier.verify(purchases)

    assert report["success"] is True
    assert "BTC" in report["results"]
    assert report["results"]["BTC"]["status"] == "match"
    assert report["results"]["BTC"]["harvested_total"] == 1.5
    assert report["results"]["BTC"]["on_chain_balance"] == 1.5
    assert abs(report["results"]["BTC"].get("difference", 0)) < 0.00000001


@patch("digital_asset_harvester.integrations.blockchain_verifier.WalletClient", WalletClient)
def test_verify_discrepancy():
    """Verify detection of discrepancies between harvested and on-chain data."""
    # Mock balance for ETH at this address is 10.0
    config = "ETH:0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"
    verifier = BlockchainVerifier(config)

    purchases = [
        {"item_name": "ETH", "amount": 7.5},
    ]

    report = verifier.verify(purchases)

    assert report["success"] is True
    assert report["results"]["ETH"]["status"] == "discrepancy"
    assert report["results"]["ETH"]["harvested_total"] == 7.5
    assert report["results"]["ETH"]["on_chain_balance"] == 10.0
    assert report["results"]["ETH"]["difference"] == 2.5


@patch("digital_asset_harvester.integrations.blockchain_verifier.WalletClient", WalletClient)
def test_verify_no_wallet_configured():
    """Verify handling of assets without configured wallets."""
    config = "BTC:addr1"
    verifier = BlockchainVerifier(config)

    purchases = [
        {"item_name": "ETH", "amount": 1.0},
    ]

    report = verifier.verify(purchases)

    assert report["success"] is True
    assert report["results"]["ETH"]["status"] == "no_wallet_configured"
    assert report["results"]["ETH"]["on_chain_balance"] is None


@patch("digital_asset_harvester.integrations.blockchain_verifier.WalletClient", None)
def test_verify_library_not_installed():
    """Verify behavior when blockchain-core is not installed."""
    verifier = BlockchainVerifier("BTC:addr1")
    report = verifier.verify([])

    assert report["success"] is False
    assert "not installed" in report["error"]


@patch("digital_asset_harvester.integrations.blockchain_verifier.WalletClient", WalletClient)
def test_verify_with_error():
    """Verify handling of errors during balance fetching."""
    config = "BTC:addr1"
    verifier = BlockchainVerifier(config)

    # Force an error in the mock client
    verifier.client.get_balance = MagicMock(side_effect=Exception("API Timeout"))

    purchases = [
        {"item_name": "BTC", "amount": 1.0},
    ]

    report = verifier.verify(purchases)

    assert report["success"] is True
    assert report["results"]["BTC"]["status"] == "error"
    assert "API Timeout" in report["results"]["BTC"]["error_message"]
