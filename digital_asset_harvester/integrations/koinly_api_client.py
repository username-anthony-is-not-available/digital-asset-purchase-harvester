"""Koinly API client for direct transaction upload.

Note: As of 2024, Koinly does not provide a public REST API for uploading transactions.
This client is designed as a placeholder/future-ready implementation that could be
activated if Koinly releases an API in the future.

Current status: Mock implementation that generates appropriate error messages.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore


logger = logging.getLogger(__name__)


@dataclass
class KoinlyTransaction:
    """Represents a transaction in Koinly's expected format."""
    
    date: str  # ISO 8601 format
    sent_amount: Optional[float] = None
    sent_currency: Optional[str] = None
    received_amount: Optional[float] = None
    received_currency: Optional[str] = None
    fee_amount: Optional[float] = None
    fee_currency: Optional[str] = None
    description: Optional[str] = None
    tx_hash: Optional[str] = None
    label: Optional[str] = None


class KoinlyApiError(Exception):
    """Raised when Koinly API operations fail."""
    pass


class KoinlyApiClient:
    """Client for interacting with Koinly's API.
    
    Note: Koinly does not currently offer a public API for uploading transactions.
    This implementation is a placeholder that:
    1. Documents the expected API structure
    2. Provides proper error handling
    3. Can be activated if/when Koinly releases an API
    
    For now, users should use CSV export functionality instead.
    """
    
    def __init__(
        self,
        api_key: str,
        portfolio_id: str,
        base_url: str = "https://api.koinly.io/v1",
        timeout: int = 30,
    ):
        """Initialize the Koinly API client.
        
        Args:
            api_key: Koinly API key for authentication
            portfolio_id: Portfolio/wallet ID in Koinly
            base_url: Base URL for Koinly API
            timeout: Request timeout in seconds
        """
        if not httpx:
            raise ImportError(
                "httpx is required for Koinly API client. "
                "Install it with: pip install httpx"
            )
        
        if not api_key:
            raise ValueError("Koinly API key is required")
        
        if not portfolio_id:
            raise ValueError("Koinly portfolio ID is required")
        
        self.api_key = api_key
        self.portfolio_id = portfolio_id
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
        
        logger.info(
            "Initialized Koinly API client for portfolio %s",
            portfolio_id,
        )
    
    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "digital-asset-purchase-harvester/0.1.0",
                },
            )
        return self._client
    
    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def test_connection(self) -> bool:
        """Test the API connection and authentication.
        
        Returns:
            True if connection is successful, False otherwise
            
        Raises:
            KoinlyApiError: If connection fails
        """
        logger.warning(
            "Koinly does not currently provide a public API. "
            "This is a placeholder implementation."
        )
        
        # Since Koinly doesn't have a public API, return False
        # and guide users to use CSV export instead
        raise KoinlyApiError(
            "Koinly does not currently offer a public API for direct transaction uploads. "
            "Please use the CSV export feature (--output-format koinly) instead. "
            "The CSV file can then be manually uploaded to Koinly's web interface."
        )
    
    def upload_transaction(self, transaction: KoinlyTransaction) -> Dict[str, Any]:
        """Upload a single transaction to Koinly.
        
        Args:
            transaction: Transaction to upload
            
        Returns:
            Response from Koinly API
            
        Raises:
            KoinlyApiError: If upload fails
        """
        logger.warning(
            "Koinly API upload attempted but not available. "
            "Use CSV export instead."
        )
        
        raise KoinlyApiError(
            "Koinly does not currently offer a public API for direct transaction uploads. "
            "Please use the CSV export feature (--output-format koinly) instead."
        )
    
    def upload_transactions(
        self,
        transactions: List[KoinlyTransaction],
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """Upload multiple transactions to Koinly.
        
        Args:
            transactions: List of transactions to upload
            batch_size: Number of transactions per batch request
            
        Returns:
            Upload summary with counts and any errors
            
        Raises:
            KoinlyApiError: If upload fails
        """
        logger.warning(
            "Attempting to upload %d transactions via Koinly API",
            len(transactions),
        )
        
        raise KoinlyApiError(
            "Koinly does not currently offer a public API for direct transaction uploads. "
            "Please use the CSV export feature (--output-format koinly) instead. "
            f"Generated CSV can contain all {len(transactions)} transactions."
        )
    
    def upload_purchases(
        self,
        purchases: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Convert and upload purchase records to Koinly.
        
        Args:
            purchases: List of purchase dictionaries
            
        Returns:
            Upload summary
            
        Raises:
            KoinlyApiError: If upload fails
        """
        # Convert purchases to Koinly transactions
        transactions = []
        for purchase in purchases:
            tx = KoinlyTransaction(
                date=purchase.get("purchase_date", ""),
                sent_amount=purchase.get("total_spent"),
                sent_currency=purchase.get("currency", "USD"),
                received_amount=purchase.get("amount"),
                received_currency=purchase.get("item_name"),
                description=f"{purchase.get('vendor', 'Unknown')} purchase",
                tx_hash=purchase.get("transaction_id"),
                label="purchase",
            )
            transactions.append(tx)
        
        return self.upload_transactions(transactions)
    
    @staticmethod
    def is_available() -> bool:
        """Check if Koinly API is available for use.
        
        Returns:
            False (Koinly API is not currently available)
        """
        return False
    
    @staticmethod
    def get_setup_instructions() -> str:
        """Get instructions for setting up Koinly integration.
        
        Returns:
            Setup instructions string
        """
        return """
Koinly API Setup:

NOTE: Koinly does not currently provide a public API for uploading transactions.

To use Koinly integration:

1. Export your transactions to CSV format:
   digital-asset-harvester --mbox-file emails.mbox \\
       --output-format koinly \\
       --output koinly_transactions.csv

2. Log in to your Koinly account at https://app.koinly.io

3. Navigate to: Wallets > Add Wallet > File Import

4. Upload the generated koinly_transactions.csv file

5. Review and confirm the imported transactions

Alternative: If Koinly releases an API in the future, configure:
   export DAP_ENABLE_KOINLY_API=true
   export DAP_KOINLY_API_KEY=your_api_key
   export DAP_KOINLY_PORTFOLIO_ID=your_portfolio_id
"""
