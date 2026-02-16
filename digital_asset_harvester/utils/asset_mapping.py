"""Fuzzy mapping service for cryptocurrency assets to CoinGecko IDs."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

# Predefined list of common cryptocurrencies for mapping
# (id, symbol, name)
COMMON_ASSETS: List[Tuple[str, str, str]] = [
    ("bitcoin", "btc", "Bitcoin"),
    ("ethereum", "eth", "Ethereum"),
    ("tether", "usdt", "Tether"),
    ("usd-coin", "usdc", "USD Coin"),
    ("binancecoin", "bnb", "BNB"),
    ("ripple", "xrp", "XRP"),
    ("cardano", "ada", "Cardano"),
    ("solana", "sol", "Solana"),
    ("dogecoin", "doge", "Dogecoin"),
    ("polkadot", "dot", "Polkadot"),
    ("polygon", "matic", "Polygon"),
    ("litecoin", "ltc", "Litecoin"),
    ("chainlink", "link", "Chainlink"),
    ("bitcoin-cash", "bch", "Bitcoin Cash"),
    ("stellar", "xlm", "Stellar"),
    ("monero", "xmr", "Monero"),
    ("ethereum-classic", "etc", "Ethereum Classic"),
    ("avalanche-2", "avax", "Avalanche"),
    ("wrapped-bitcoin", "wbtc", "Wrapped Bitcoin"),
    ("dai", "dai", "Dai"),
    ("uniswap", "uni", "Uniswap"),
    ("cosmos", "atom", "Cosmos"),
    ("shiba-inu", "shib", "Shiba Inu"),
    ("leo-token", "leo", "LEO Token"),
    ("tron", "trx", "TRON"),
    ("toncoin", "ton", "Toncoin"),
    ("near", "near", "NEAR Protocol"),
    ("optimism", "op", "Optimism"),
    ("arbitrum", "arb", "Arbitrum"),
    ("pepe", "pepe", "Pepe"),
    ("kaspa", "kas", "Kaspa"),
    ("aptos", "apt", "Aptos"),
    ("stacks", "stx", "Stacks"),
    ("hedera-hashgraph", "hbar", "Hedera"),
    ("filecoin", "fil", "Filecoin"),
    ("vechain", "vet", "VeChain"),
    ("maker", "mkr", "Maker"),
    ("lido-dao", "ldo", "Lido DAO"),
    ("render-token", "rndr", "Render"),
    ("thorchain", "rune", "THORChain"),
]


class CoinGeckoMapper:
    """Service for mapping asset names or symbols to CoinGecko IDs."""

    def __init__(self, assets: Optional[List[Tuple[str, str, str]]] = None):
        self.assets = assets or COMMON_ASSETS
        # Build lookup tables for exact matches
        self.symbol_to_id = {symbol.lower(): cid for cid, symbol, name in self.assets}
        self.name_to_id = {name.lower(): cid for cid, symbol, name in self.assets}

        # Build list of strings for fuzzy matching (symbols and names)
        self.fuzzy_choices = []
        for cid, symbol, name in self.assets:
            self.fuzzy_choices.append(symbol.lower())
            self.fuzzy_choices.append(name.lower())

    def get_asset_id(self, item_name: str, threshold: int = 80) -> Optional[str]:
        """
        Map an item name (symbol or full name) to a CoinGecko ID.

        Uses exact matching first, then fuzzy matching.
        """
        if not item_name:
            return None

        clean_name = item_name.strip().lower()

        # 1. Try exact symbol match
        if clean_name in self.symbol_to_id:
            return self.symbol_to_id[clean_name]

        # 2. Try exact name match
        if clean_name in self.name_to_id:
            return self.name_to_id[clean_name]

        # 3. Try fuzzy matching
        match = process.extractOne(clean_name, self.fuzzy_choices, scorer=fuzz.WRatio)
        if match and match[1] >= threshold:
            best_string = match[0]
            # Find the ID for this string
            if best_string in self.symbol_to_id:
                return self.symbol_to_id[best_string]
            if best_string in self.name_to_id:
                return self.name_to_id[best_string]

        logger.debug("Could not map asset name '%s' to a CoinGecko ID", item_name)
        return None


# Singleton instance
mapper = CoinGeckoMapper()
