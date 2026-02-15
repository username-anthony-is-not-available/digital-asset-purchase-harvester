import json
import pytest
from unittest.mock import MagicMock
from digital_asset_harvester import (
    EmailPurchaseExtractor,
    MboxDataExtractor,
    get_settings_with_overrides,
)
from digital_asset_harvester.llm.provider import LLMResult


@pytest.fixture
def golden_expected():
    with open("tests/fixtures/golden_expected.json", "r") as f:
        return json.load(f)


@pytest.fixture
def mock_llm_client():
    client = MagicMock()

    def side_effect(prompt, retries=3):
        prompt_lower = prompt.lower()
        # Find the email content part of the prompt
        email_content = ""
        if "email content:" in prompt_lower:
            # Split by common markers to isolate the email content
            parts = prompt_lower.split("email content:")
            if len(parts) > 1:
                content_part = parts[1]
                for marker in ["analysis criteria:", "extraction instructions:"]:
                    if marker in content_part:
                        content_part = content_part.split(marker)[0]
                email_content = content_part

        is_extraction = "return json with this exact structure" in prompt_lower and "transactions" in prompt_lower

        email_id = None
        if "generic_llm_purchase" in email_content or "someexchange" in email_content:
            email_id = "generic_llm_purchase"
        elif "newsletter" in email_content or "bullish" in email_content:
            email_id = "newsletter"
        elif "security" in email_content or "login" in email_content:
            email_id = "security_alert"
        elif "coinbase" in email_content:
            if "staking reward" in email_content:
                email_id = "coinbase_staking"
            else:
                email_id = "coinbase_purchase"
        elif "binance" in email_content:
            if "pair: btc/usdt" in email_content:
                email_id = "binance_multi"
            else:
                email_id = "binance_purchase"
        elif "kraken" in email_content:
            email_id = "kraken_purchase"
        elif "gemini" in email_content:
            email_id = "gemini_purchase"
        elif "crypto.com" in email_content or "2.5 sol" in email_content:
            email_id = "cryptocom_purchase"
        elif "ftx" in email_content or "matic" in email_content:
            email_id = "ftx_purchase"
        elif "coinspot" in email_content or "50 ada" in email_content:
            email_id = "coinspot_purchase"

        if not is_extraction:
            # Classification
            is_purchase = email_id not in ["newsletter", "security_alert", None]
            return LLMResult(
                data={"is_crypto_purchase": is_purchase, "confidence": 0.99, "reasoning": f"Identified as {email_id}"},
                raw_text="{}",
            )
        else:
            # Extraction
            if email_id == "generic_llm_purchase":
                return LLMResult(
                    data={
                        "transactions": [
                            {
                                "transaction_type": "buy",
                                "amount": 1000.0,
                                "item_name": "DOGE",
                                "total_spent": 0.1,
                                "currency": "ETH",
                                "vendor": "SomeExchange",
                                "purchase_date": "2024-01-10 19:00:00",
                                "confidence": 0.95,
                                "extraction_notes": "Extracted from body",
                            }
                        ]
                    },
                    raw_text="{}",
                )

            # Others should be handled by regex and not even reach here if regex is enabled
            return LLMResult(data={"transactions": []}, raw_text="{}")

    client.generate_json.side_effect = side_effect
    return client


@pytest.mark.integration
def test_golden_mbox_extraction(golden_expected, mock_llm_client):
    """Verify extraction consistency against the golden mbox."""
    mbox_path = "tests/fixtures/golden.mbox"
    mbox_reader = MboxDataExtractor(mbox_path)

    settings = get_settings_with_overrides(
        enable_regex_extractors=True,
        enable_preprocessing=True,
        strict_validation=False,
    )

    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)

    emails = list(mbox_reader.extract_emails())
    assert len(emails) == len(golden_expected)

    for email in emails:
        # Get ID from Message-ID header
        msg_id = email.get("message_id", "")
        email_id = msg_id.strip("<>").split("@")[0]

        assert email_id in golden_expected, f"Email ID {email_id} not in expected results"
        expected_purchases = golden_expected[email_id]

        # Process the email
        email_content = (
            f"From: {email.get('sender', '')}\n"
            f"Subject: {email.get('subject', '')}\n"
            f"Date: {email.get('date', '')}\n\n"
            f"{email.get('body', '')}"
        )

        result = extractor.process_email(email_content)

        actual_purchases = result.get("purchases", [])

        assert len(actual_purchases) == len(
            expected_purchases
        ), f"Mismatch in number of purchases for {email_id}. Expected {len(expected_purchases)}, got {len(actual_purchases)}"

        for i, expected in enumerate(expected_purchases):
            actual = actual_purchases[i]

            assert actual["item_name"].upper() == expected["item_name"].upper(), f"{email_id} asset mismatch"
            assert float(actual["amount"]) == pytest.approx(float(expected["amount"])), f"{email_id} amount mismatch"

            if "total_spent" in expected and expected["total_spent"] is not None:
                assert float(actual["total_spent"]) == pytest.approx(
                    float(expected["total_spent"])
                ), f"{email_id} total_spent mismatch"

            if "currency" in expected and expected["currency"] is not None:
                assert actual["currency"] == expected["currency"], f"{email_id} currency mismatch"

            assert actual["vendor"].lower() == expected["vendor"].lower(), f"{email_id} vendor mismatch"

            if "transaction_id" in expected:
                assert actual["transaction_id"] == expected["transaction_id"], f"{email_id} transaction_id mismatch"

            if "transaction_type" in expected:
                assert (
                    actual["transaction_type"] == expected["transaction_type"]
                ), f"{email_id} transaction_type mismatch"

            assert (
                actual["extraction_method"] == expected["extraction_method"]
            ), f"{email_id} extraction_method mismatch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
