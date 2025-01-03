import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ollama import Client

from config import LLM_MODEL_NAME

logger = logging.getLogger(__name__)
ollama_client = Client()

@dataclass
class PurchaseInfo:
    total_spent: float
    currency: str
    amount: float
    item_name: str
    vendor: str
    purchase_date: str

@dataclass
class EmailPurchaseExtractor:
    model_name: str = LLM_MODEL_NAME

    def is_crypto_purchase_email(self, email_content: str, max_retries: int = 3) -> bool:
        prompt = f"""Determine if the following email content is related to a cryptocurrency purchase:

        {email_content}

        Return a JSON object with the following structure:
        {{
            "is_crypto_purchase": boolean
        }}
        """

        for attempt in range(max_retries):
            try:
                logger.info("Attempting to categorize email (attempt %d/%d)", attempt + 1, max_retries)
                response = ollama_client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    format="json"
                )

                result = json.loads(response.response)
                return result.get("is_crypto_purchase", False)

            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON response (attempt %d): %s", attempt + 1, e)
            except (ConnectionError, TimeoutError) as e:
                logger.error("Network-related error categorizing email (attempt %d): %s", attempt + 1, e)
            except (RuntimeError, ValueError) as e:
                logger.error("Runtime or value error categorizing email (attempt %d): %s", attempt + 1, e)

        logger.error("Failed to categorize email after %d attempts", max_retries)
        return False

    def extract_purchase_info(self, email_content: str, max_retries: int = 3, default_timezone: str = "UTC") -> Optional[Dict[str, Any]]:
        prompt = f"""Carefully analyze the following email content to extract cryptocurrency purchase information. Take your time to ensure accuracy and completeness.

        {email_content}

        Provide a detailed JSON object with the following structure:
        {{
            "total_spent": float (the total amount spent in fiat currency),
            "currency": string (the fiat currency used, e.g., USD, EUR),
            "amount": float (the amount of cryptocurrency purchased),
            "item_name": string (the name of the cryptocurrency purchased, e.g., Bitcoin, Ethereum),
            "vendor": string (the name of the exchange or platform where the purchase was made),
            "purchase_date": string (the date and time of the purchase in ISO 8601 format with timezone, e.g., "2023-04-15T14:30:00+00:00")
        }}

        If you're unsure about any field, use null instead of guessing. If no purchase information is found, return null for the entire object.

        Ensure all numeric values are precise and the purchase date includes the timezone. If the timezone is not specified in the email, assume {default_timezone}.
        """

        for attempt in range(max_retries):
            try:
                logger.info("Attempting to extract purchase info (attempt %d/%d)", attempt + 1, max_retries)
                response = ollama_client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    format="json"
                )

                purchase_data = json.loads(response.response)

                if purchase_data is None:
                    logger.info("No purchase information found in the email")
                    return None

                # Process the purchase date
                if purchase_data.get("purchase_date"):
                    try:
                        # Parse the date and ensure it's in UTC
                        date = datetime.fromisoformat(purchase_data["purchase_date"])
                        if date.tzinfo is None:
                            date = date.replace(tzinfo=timezone.utc)
                        else:
                            date = date.astimezone(timezone.utc)
                        purchase_data["purchase_date"] = date.strftime("%Y-%m-%d %H:%M:%S %Z")
                    except ValueError:
                        logger.warning("Invalid date format. Using default.")
                        purchase_data["purchase_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
                else:
                    purchase_data["purchase_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")

                return purchase_data

            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON response (attempt %d): %s", attempt + 1, e)
            except (ConnectionError, TimeoutError, RuntimeError, ValueError) as e:
                logger.error("Error extracting purchase info (attempt %d): %s", attempt + 1, e)

        # If we've exhausted all retries, create a default dict with empty values
        logger.warning("Failed to extract complete purchase info after %d attempts. Using default values.", max_retries)
        default_purchase_data = {
            "total_spent": 0.0,
            "currency": "UNKNOWN",
            "amount": 0.0,
            "item_name": "UNKNOWN",
            "vendor": "UNKNOWN",
            "purchase_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        }

        # Try to salvage any information we did manage to extract
        if 'purchase_data' in locals() and isinstance(purchase_data, dict):
            for key in default_purchase_data:
                if key in purchase_data and purchase_data[key] is not None:
                    default_purchase_data[key] = purchase_data[key]

        return default_purchase_data

    def process_email(self, email_content: str) -> Dict[str, any]:
        if self.is_crypto_purchase_email(email_content):
            purchase_info = self.extract_purchase_info(email_content)
            if purchase_info:
                return {
                    "has_purchase": True,
                    "purchase_info": purchase_info
                }

        return {
            "has_purchase": False
        }
