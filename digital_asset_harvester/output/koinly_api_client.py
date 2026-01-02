"""Koinly API client for direct transaction upload."""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional

import httpx

logger = logging.getLogger(__name__)


class KoinlyApiError(Exception):
    """Base exception for Koinly API errors."""
    pass


class KoinlyAuthenticationError(KoinlyApiError):
    """Exception raised for authentication errors."""
    pass


class KoinlyApiClient:
    """Client for interacting with the Koinly API.
    
    Note: As of January 2026, Koinly does not have a publicly documented API
    for uploading transactions. This implementation provides a structure for
    future API integration when/if it becomes available.
    
    The API endpoints and authentication mechanism may need to be updated
    based on official Koinly API documentation when released.
    """

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.koinly.io/api/v1",
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """Initialize the Koinly API client.
        
        Args:
            api_key: Koinly API key for authentication
            api_url: Base URL for the Koinly API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        if not api_key:
            raise KoinlyAuthenticationError("API key is required")
        
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create an HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "DigitalAssetHarvester/1.0",
                }
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> KoinlyApiClient:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def test_connection(self) -> bool:
        """Test the API connection and authentication.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            client = self._get_client()
            # Try to access a basic endpoint (e.g., account info or wallets)
            # This is a placeholder - actual endpoint may differ
            response = client.get(f"{self.api_url}/account")
            
            if response.status_code == 401:
                raise KoinlyAuthenticationError("Invalid API key")
            
            response.raise_for_status()
            logger.info("Successfully connected to Koinly API")
            return True
            
        except KoinlyAuthenticationError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error testing Koinly connection: {e}")
            return False
        except Exception as e:
            logger.error(f"Error testing Koinly connection: {e}")
            return False

    def upload_transactions(
        self,
        transactions: Iterable[Dict[str, Any]],
        wallet_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload transactions to Koinly.
        
        Args:
            transactions: List of transaction dictionaries to upload
            wallet_id: Optional wallet ID to associate transactions with
            
        Returns:
            API response containing upload status and details
            
        Raises:
            KoinlyApiError: If the upload fails
            KoinlyAuthenticationError: If authentication fails
        """
        transactions_list = list(transactions)
        if not transactions_list:
            logger.warning("No transactions to upload")
            return {"status": "success", "uploaded": 0}

        logger.info(f"Uploading {len(transactions_list)} transactions to Koinly")
        
        try:
            client = self._get_client()
            
            # Convert transactions to Koinly API format
            payload = self._format_transactions_for_api(transactions_list, wallet_id)
            
            # Attempt upload with retries
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    # This endpoint is placeholder - actual endpoint may differ
                    response = client.post(
                        f"{self.api_url}/transactions/import",
                        json=payload,
                    )
                    
                    if response.status_code == 401:
                        raise KoinlyAuthenticationError("Invalid API key")
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    logger.info(
                        f"Successfully uploaded {len(transactions_list)} transactions"
                    )
                    return result
                    
                except httpx.HTTPStatusError as e:
                    last_error = e
                    if e.response.status_code in [500, 502, 503, 504]:
                        # Retry on server errors
                        logger.warning(
                            f"Server error on attempt {attempt + 1}/{self.max_retries}: {e}"
                        )
                        continue
                    else:
                        # Don't retry on client errors
                        raise KoinlyApiError(
                            f"Failed to upload transactions: {e.response.text}"
                        ) from e
                        
            # If we exhausted retries
            raise KoinlyApiError(
                f"Failed to upload after {self.max_retries} attempts"
            ) from last_error
            
        except KoinlyAuthenticationError:
            raise
        except KoinlyApiError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading transactions: {e}")
            raise KoinlyApiError(f"Unexpected error: {e}") from e

    def _format_transactions_for_api(
        self,
        transactions: List[Dict[str, Any]],
        wallet_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Format transactions for the Koinly API.
        
        Args:
            transactions: List of transaction dictionaries
            wallet_id: Optional wallet ID
            
        Returns:
            Formatted payload for API request
        """
        formatted_transactions = []
        
        for txn in transactions:
            # Convert our transaction format to Koinly's expected format
            formatted_txn = {
                "timestamp": txn.get("purchase_date", ""),
                "sent_amount": str(txn.get("total_spent", "")),
                "sent_currency": txn.get("currency", ""),
                "received_amount": str(txn.get("amount", "")),
                "received_currency": txn.get("item_name", ""),
                "label": "buy",
                "description": f"Purchase from {txn.get('vendor', 'Unknown')}",
            }
            
            if wallet_id:
                formatted_txn["wallet_id"] = wallet_id
                
            formatted_transactions.append(formatted_txn)
        
        return {
            "transactions": formatted_transactions,
            "source": "digital-asset-harvester",
        }

    def get_wallets(self) -> List[Dict[str, Any]]:
        """Retrieve list of wallets from Koinly account.
        
        Returns:
            List of wallet dictionaries
            
        Raises:
            KoinlyApiError: If the request fails
        """
        try:
            client = self._get_client()
            response = client.get(f"{self.api_url}/wallets")
            
            if response.status_code == 401:
                raise KoinlyAuthenticationError("Invalid API key")
            
            response.raise_for_status()
            return response.json().get("wallets", [])
            
        except httpx.HTTPStatusError as e:
            raise KoinlyApiError(f"Failed to retrieve wallets: {e}") from e
        except Exception as e:
            raise KoinlyApiError(f"Unexpected error retrieving wallets: {e}") from e
