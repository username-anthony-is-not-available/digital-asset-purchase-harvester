import pytest
from digital_asset_harvester.utils.asset_mapping import CoinGeckoMapper


def test_asset_mapping_initialization():
    mapper = CoinGeckoMapper([("test-id", "tst", "Test Coin")])
    assert mapper.symbol_to_id["tst"] == "test-id"
    assert mapper.name_to_id["test coin"] == "test-id"


def test_get_asset_id_exact_matches():
    mapper = CoinGeckoMapper([("bitcoin", "btc", "Bitcoin"), ("ethereum", "eth", "Ethereum")])

    assert mapper.get_asset_id("btc") == "bitcoin"
    assert mapper.get_asset_id("Bitcoin") == "bitcoin"
    assert mapper.get_asset_id("ETH") == "ethereum"
    assert mapper.get_asset_id("ethereum") == "ethereum"


def test_get_asset_id_fuzzy_matches():
    mapper = CoinGeckoMapper([("bitcoin", "btc", "Bitcoin"), ("ethereum", "eth", "Ethereum")])

    # Fuzzy match for "Bitcoi"
    assert mapper.get_asset_id("Bitcoi") == "bitcoin"
    # Fuzzy match for "Ether"
    assert mapper.get_asset_id("Ether") == "ethereum"


def test_get_asset_id_no_match():
    mapper = CoinGeckoMapper([("bitcoin", "btc", "Bitcoin")])
    assert mapper.get_asset_id("UnknownCoin") is None
    assert mapper.get_asset_id("") is None
    assert mapper.get_asset_id(None) is None


def test_get_asset_id_low_confidence():
    mapper = CoinGeckoMapper([("bitcoin", "btc", "Bitcoin")])
    # "Bit" might be too short for 80 threshold
    assert mapper.get_asset_id("Bit", threshold=95) is None
