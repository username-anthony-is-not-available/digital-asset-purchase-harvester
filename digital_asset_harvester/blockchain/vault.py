"""Secure vault for managing private keys and wallets."""

import base64
import json
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from mnemonic import Mnemonic
from eth_account import Account

logger = logging.getLogger(__name__)

# Enable HD Wallet features for eth-account
Account.enable_unaudited_hdwallet_features()


class VaultManager:
    """Manages an encrypted vault of private keys and mnemonics using AES-256-GCM."""

    def __init__(self, vault_path: str, salt: bytes = b"default_salt_for_dap"):
        self.vault_path = vault_path
        self.salt = salt
        self._key: Optional[bytes] = None
        self._aesgcm: Optional[AESGCM] = None
        self._unlocked_data: Dict = {}

    def _derive_key(self, passphrase: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return kdf.derive(passphrase.encode())

    def create_vault(self, passphrase: str) -> str:
        """Initialize a new vault with a mnemonic."""
        if os.path.exists(self.vault_path):
            raise FileExistsError("Vault already exists")

        mnemo = Mnemonic("english")
        mnemonic = mnemo.generate(strength=128)

        self._key = self._derive_key(passphrase)
        self._aesgcm = AESGCM(self._key)

        self._unlocked_data = {"mnemonic": mnemonic, "wallets": []}

        self.save()
        return mnemonic

    def unlock(self, passphrase: str):
        """Unlock the vault using the passphrase."""
        if not os.path.exists(self.vault_path):
            raise FileNotFoundError("Vault file not found")

        with open(self.vault_path, "rb") as f:
            raw_data = f.read()

        if len(raw_data) < 13:  # 12 bytes nonce + at least 1 byte ciphertext
            raise ValueError("Corrupted vault file")

        nonce = raw_data[:12]
        encrypted_data = raw_data[12:]

        self._key = self._derive_key(passphrase)
        self._aesgcm = AESGCM(self._key)

        try:
            decrypted_data = self._aesgcm.decrypt(nonce, encrypted_data, None)
            self._unlocked_data = json.loads(decrypted_data.decode())
        except Exception:
            self._key = None
            self._aesgcm = None
            raise ValueError("Invalid passphrase or corrupted vault file")

    def save(self):
        """Encrypt and save the vault data."""
        if self._aesgcm is None:
            raise RuntimeError("Vault is locked")

        data_str = json.dumps(self._unlocked_data)
        nonce = os.urandom(12)
        encrypted_data = self._aesgcm.encrypt(nonce, data_str.encode(), None)

        # Combined nonce + ciphertext
        final_data = nonce + encrypted_data

        # Use atomic write pattern
        temp_path = self.vault_path + ".tmp"
        with open(temp_path, "wb") as f:
            f.write(final_data)
        os.replace(temp_path, self.vault_path)

    def add_wallet(self, asset: str, index: int = 0) -> str:
        """Derive a new wallet from the mnemonic and add it to the vault."""
        if self._aesgcm is None:
            raise RuntimeError("Vault is locked")

        mnemonic = self._unlocked_data["mnemonic"]

        if asset.upper() == "ETH":
            # Standard Ethereum derivation path
            path = f"m/44'/60'/0'/0/{index}"
            account = Account.from_mnemonic(mnemonic, account_path=path)
            address = account.address
        else:
            raise ValueError(f"Unsupported asset type: {asset}")

        # Check if already exists
        for w in self._unlocked_data["wallets"]:
            if w["address"] == address:
                return address

        self._unlocked_data["wallets"].append(
            {"address": address, "asset": asset.upper(), "index": index, "path": path}
        )
        self.save()
        return address

    def get_private_key(self, address: str) -> str:
        """Retrieve the private key for a given address."""
        if self._aesgcm is None:
            raise RuntimeError("Vault is locked")

        mnemonic = self._unlocked_data["mnemonic"]

        for w in self._unlocked_data["wallets"]:
            if w["address"] == address:
                account = Account.from_mnemonic(mnemonic, account_path=w["path"])
                return account.key.hex()

        raise ValueError(f"Address {address} not found in vault")

    def list_wallets(self) -> List[Dict]:
        """List all wallets in the vault (addresses only)."""
        if self._aesgcm is None:
            raise RuntimeError("Vault is locked")

        return [{"address": w["address"], "asset": w["asset"]} for w in self._unlocked_data["wallets"]]

    def get_address_for_asset(self, asset: str) -> Optional[str]:
        """Get the first address for a given asset."""
        if self._aesgcm is None:
            raise RuntimeError("Vault is locked")

        for w in self._unlocked_data["wallets"]:
            if w["asset"] == asset.upper():
                return w["address"]
        return None
