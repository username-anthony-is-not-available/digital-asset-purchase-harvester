"""Mock for blockchain_core library for testing purposes."""


class WalletClient:
    """Mock implementation of the WalletClient from blockchain_core."""

    def __init__(self, balances=None):
        """
        Initialize with optional preset balances.

        balances: Dict mapping (address, asset_symbol) to float balance.
        """
        self.balances = balances or {
            ("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "BTC"): 1.5,
            ("0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe", "ETH"): 10.0,
            ("LR987654321", "LTC"): 5.0,
        }

    def get_balance(self, address: str, asset: str) -> float:
        """
        Mock method to get balance.

        Args:
            address: Wallet address.
            asset: Asset symbol (e.g., 'BTC').

        Returns:
            The balance as a float.
        """
        # Case insensitive match for asset
        key = (address, asset.upper())
        if key in self.balances:
            return self.balances[key]

        # If not found exactly, try finding by address if asset matches
        for (addr, ast), balance in self.balances.items():
            if addr == address and ast == asset.upper():
                return balance

        return 0.0
