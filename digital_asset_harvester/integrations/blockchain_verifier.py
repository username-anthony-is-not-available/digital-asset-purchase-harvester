"""Integration for verifying harvested purchases against blockchain balances."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

try:
    from blockchain_core import WalletClient
except ImportError:
    # Fallback or mock for environments where it's not installed
    WalletClient = None

logger = logging.getLogger(__name__)


class BlockchainVerifier:
    """Verifies harvested digital asset totals against on-chain wallet balances."""

    def __init__(self, wallets_config: str):
        """
        Initialize the verifier with a configuration string.

        Args:
            wallets_config: Comma-separated list of ASSET:ADDRESS pairs.
                           Example: "BTC:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa,ETH:0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"
        """
        self.wallets = self._parse_wallets(wallets_config)
        self.client = WalletClient() if WalletClient else None

    def _parse_wallets(self, config: str) -> Dict[str, str]:
        """Parse the wallet configuration string into a dictionary."""
        wallets = {}
        if not config:
            return wallets

        for item in config.split(","):
            if ":" in item:
                parts = item.split(":", 1)
                if len(parts) == 2:
                    asset, address = parts
                    wallets[asset.strip().upper()] = address.strip()
        return wallets

    def verify(self, purchases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare harvested totals with on-chain balances.

        Args:
            purchases: List of harvested purchase records (as dictionaries).

        Returns:
            A dictionary containing the verification report.
        """
        if not self.client:
            logger.warning("blockchain-core (WalletClient) is not available. Verification skipped.")
            return {
                "success": False,
                "error": "blockchain-core library not installed or WalletClient not found",
            }

        # Aggregate harvested totals by asset
        harvested_totals: Dict[str, Decimal] = {}
        for p in purchases:
            # Use item_name for matching with wallet config
            asset = p.get("item_name", "").upper()
            if not asset:
                continue

            try:
                amount = Decimal(str(p.get("amount", "0")))
                harvested_totals[asset] = harvested_totals.get(asset, Decimal("0")) + amount
            except (ValueError, TypeError, Decimal.InvalidOperation):
                logger.warning("Invalid amount for purchase: %s", p)
                continue

        results = {}
        for asset, harvested_total in harvested_totals.items():
            address = self.wallets.get(asset)
            if not address:
                results[asset] = {
                    "harvested_total": float(harvested_total),
                    "on_chain_balance": None,
                    "status": "no_wallet_configured",
                }
                continue

            try:
                # Fetch balance from blockchain-core
                on_chain_balance_raw = self.client.get_balance(address, asset)
                on_chain_balance = Decimal(str(on_chain_balance_raw))

                diff = on_chain_balance - harvested_total

                # Small threshold for floating point comparison if needed,
                # but we use Decimal for precision.
                status = "match" if abs(diff) < Decimal("0.00000001") else "discrepancy"

                results[asset] = {
                    "harvested_total": float(harvested_total),
                    "on_chain_balance": float(on_chain_balance),
                    "difference": float(diff),
                    "status": status,
                }
            except Exception as e:
                logger.error("Error fetching balance for %s (%s): %s", asset, address, e)
                results[asset] = {
                    "harvested_total": float(harvested_total),
                    "on_chain_balance": None,
                    "status": "error",
                    "error_message": str(e),
                }

        return {
            "success": True,
            "results": results,
            "wallet_count": len(self.wallets),
            "verified_assets": list(results.keys()),
        }
