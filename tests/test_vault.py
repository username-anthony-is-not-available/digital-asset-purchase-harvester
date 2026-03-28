import os
import pytest
from digital_asset_harvester.blockchain.vault import VaultManager

@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / ".vault.json")

def test_create_vault(vault_path):
    vm = VaultManager(vault_path)
    mnemonic = vm.create_vault("password123")

    assert os.path.exists(vault_path)
    assert len(mnemonic.split()) == 12
    assert vm.list_wallets() == []

def test_unlock_vault(vault_path):
    vm = VaultManager(vault_path)
    vm.create_vault("password123")

    vm2 = VaultManager(vault_path)
    vm2.unlock("password123")
    assert len(vm2._unlocked_data["mnemonic"].split()) == 12

def test_unlock_invalid_passphrase(vault_path):
    vm = VaultManager(vault_path)
    vm.create_vault("password123")

    vm2 = VaultManager(vault_path)
    with pytest.raises(ValueError, match="Invalid passphrase"):
        vm2.unlock("wrongpassword")

def test_add_wallet(vault_path):
    vm = VaultManager(vault_path)
    vm.create_vault("password123")

    address = vm.add_wallet("ETH", index=0)
    assert address.startswith("0x")

    wallets = vm.list_wallets()
    assert len(wallets) == 1
    assert wallets[0]["address"] == address
    assert wallets[0]["asset"] == "ETH"

def test_get_private_key(vault_path):
    vm = VaultManager(vault_path)
    vm.create_vault("password123")
    address = vm.add_wallet("ETH", index=0)

    private_key = vm.get_private_key(address)
    assert len(private_key) == 64 or len(private_key) == 66 # hex string

    # Verify same address can be derived from private key
    from eth_account import Account
    acc = Account.from_key(private_key)
    assert acc.address == address

def test_persistent_storage(vault_path):
    vm = VaultManager(vault_path)
    vm.create_vault("password123")
    address = vm.add_wallet("ETH", index=5)

    vm2 = VaultManager(vault_path)
    vm2.unlock("password123")
    wallets = vm2.list_wallets()
    assert len(wallets) == 1
    assert wallets[0]["address"] == address

def test_get_address_for_asset(vault_path):
    vm = VaultManager(vault_path)
    vm.create_vault("password123")
    address = vm.add_wallet("ETH")

    assert vm.get_address_for_asset("ETH") == address
    assert vm.get_address_for_asset("BTC") is None

def test_integrity_lock(vault_path):
    vm = VaultManager(vault_path)
    vm.create_vault("password123")

    # Tamper with file
    with open(vault_path, "wb") as f:
        f.write(b"corrupted data")

    vm2 = VaultManager(vault_path)
    with pytest.raises(ValueError, match="corrupted vault file"):
        vm2.unlock("password123")
