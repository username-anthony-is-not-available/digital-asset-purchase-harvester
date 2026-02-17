"""Unit tests for the PIIScrubber utility."""

import pytest
from digital_asset_harvester.utils.pii_scrubber import PIIScrubber


def test_scrub_email():
    scrubber = PIIScrubber()
    text = "Contact me at john.doe@example.com for more info."
    expected = "Contact me at [EMAIL] for more info."
    assert scrubber.scrub(text) == expected


def test_scrub_phone():
    scrubber = PIIScrubber()
    text = "My phone number is +1-555-010-9999."
    expected = "My phone number is [PHONE]."
    assert scrubber.scrub(text) == expected


def test_scrub_ip():
    scrubber = PIIScrubber()
    text = "Login from IP 192.168.1.1 detected."
    expected = "Login from IP [IP_ADDRESS] detected."
    assert scrubber.scrub(text) == expected


def test_scrub_credit_card():
    scrubber = PIIScrubber()
    text = "Card number: 1234-5678-9012-3456."
    expected = "Card number: [CREDIT_CARD]."
    assert scrubber.scrub(text) == expected


def test_scrub_address():
    scrubber = PIIScrubber()
    text = "Ship to 123 Main Street, Springfield."
    expected = "Ship to [ADDRESS], Springfield."
    assert scrubber.scrub(text) == expected

    text = "Visit us at 456 Broadway Ave."
    expected = "Visit us at [ADDRESS]."
    assert scrubber.scrub(text) == expected


def test_scrub_name_greeting():
    scrubber = PIIScrubber()
    text = "Hi John Doe,\nYour order is ready."
    expected = "Hi [NAME],\nYour order is ready."
    assert scrubber.scrub(text) == expected

    text = "Dear Alice Smith,\nWelcome back."
    expected = "Dear [NAME],\nWelcome back."
    assert scrubber.scrub(text) == expected


def test_skip_terms():
    # Test that terms in skip_terms are NOT masked
    scrubber = PIIScrubber(skip_terms={"Bitcoin", "Coinbase"})

    # "Bitcoin" shouldn't be masked by name greeting if it happened to match (unlikely but testable)
    text = "Hi Bitcoin,"
    assert scrubber.scrub(text) == "Hi Bitcoin,"

    # "coinbase@example.com" should still be masked if we match the whole email,
    # but let's see how _should_mask works.
    # In my implementation, I pass the whole match to _should_mask.
    text = "Contact support@coinbase.com"
    assert scrubber.scrub(text) == "Contact [EMAIL]"

    # If I add the exact email to skip_terms
    scrubber = PIIScrubber(skip_terms={"support@coinbase.com"})
    assert scrubber.scrub(text) == "Contact support@coinbase.com"


def test_scrub_empty_text():
    scrubber = PIIScrubber()
    assert scrubber.scrub("") == ""
    assert scrubber.scrub(None) is None


def test_multiple_pii():
    scrubber = PIIScrubber()
    text = "Hi John, send $100 to 123 Main St or email me at john@doe.com."
    # Note: 123 Main St matches address heuristic
    # john@doe.com matches email
    # Hi John matches name greeting
    scrubbed = scrubber.scrub(text)
    assert "[NAME]" in scrubbed
    assert "[ADDRESS]" in scrubbed
    assert "[EMAIL]" in scrubbed
    assert "John" not in scrubbed
    assert "123 Main St" not in scrubbed
    assert "john@doe.com" not in scrubbed


def test_scrub_crypto_addresses():
    scrubber = PIIScrubber()

    # BTC
    text = "Send BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    assert "[BTC_ADDRESS]" in scrubber.scrub(text)

    # ETH
    text = "Send ETH to 0x32Be343B94f860124dC4fEe278FDCBD38C102D88"
    assert "[ETH_ADDRESS]" in scrubber.scrub(text)

    # LTC
    text = "Send LTC to LQt98f79NTSX8V3X4RXP3T1P9P9P9P9P9P"
    assert "[LTC_ADDRESS]" in scrubber.scrub(text)

    # ADA
    text = "Send ADA to addr1qxyza123456789012345678901234567890123456789012345678901234567890"
    assert "[ADA_ADDRESS]" in scrubber.scrub(text)

    # XRP
    text = "Send XRP to rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
    assert "[XRP_ADDRESS]" in scrubber.scrub(text)

    # SOL
    text = "Send SOL to 77m76qW5XbT1aY4fX2h8v9j3k4L5m6n7o8p9qAr1s2t"
    assert "[SOL_ADDRESS]" in scrubber.scrub(text)


def test_crypto_address_priority():
    scrubber = PIIScrubber()
    # Test that ADA is caught before it might match something else
    # addr1... followed by many digits might match phone number broad pattern
    text = "Contact addr1qxyza123456789012345678901234567890123456789012345678901234567890"
    scrubbed = scrubber.scrub(text)
    assert "[ADA_ADDRESS]" in scrubbed
    assert "[PHONE]" not in scrubbed
