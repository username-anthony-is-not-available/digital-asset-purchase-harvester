"""Core parsing engine for template-based extraction."""

import re
import logging
from typing import Any, Dict, List, Optional
from .models import ExtractionTemplate, TransactionPattern, SectionConfig

logger = logging.getLogger(__name__)

class TemplateEngine:
    """Engine for extracting data using templates."""

    def __init__(self, template: ExtractionTemplate):
        self.template = template
        self.sender_regexes = [re.compile(p, re.IGNORECASE) for p in template.sender_patterns]
        self.subject_regexes = [re.compile(p, re.IGNORECASE) for p in template.subject_patterns]

    def can_handle(self, subject: str, sender: str) -> bool:
        """Check if this template can handle the email."""
        sender_match = any(r.search(sender) for r in self.sender_regexes)
        subject_match = any(r.search(subject) for r in self.subject_regexes)
        return sender_match and (not self.template.subject_patterns or subject_match)

    def extract(self, subject: str, body: str) -> List[Dict[str, Any]]:
        """Extract all transactions from the email."""
        results = []

        # 1. Sectioned parsing (often contains specific transaction data)
        if self.template.sections:
            results.extend(self._parse_sections(self.template.sections, body))

        # 2. Global patterns (apply to body)
        if not results:
            for pattern in self.template.global_patterns:
                # Only add if it has a transaction type or we can infer one
                if pattern.transaction_type:
                    results.extend(self._apply_pattern(pattern, body))

        # 3. Try subject if nothing found
        if not results:
            for pattern in self.template.global_patterns:
                if pattern.transaction_type:
                    results.extend(self._apply_pattern(pattern, subject))

        # 4. Supplemental data (like fees) from global patterns
        # If we have results, try to find missing fields from global patterns that DON'T have a transaction_type
        if results:
            supplemental_data = {}
            for pattern in self.template.global_patterns:
                if not pattern.transaction_type:
                    matches = self._apply_pattern(pattern, body)
                    if matches:
                        supplemental_data.update(matches[0])

            if supplemental_data:
                for data in results:
                    for k, v in supplemental_data.items():
                        if k not in data or not data[k]:
                            data[k] = v

        # Post-process all results
        return self._post_process(results, body)

    def _apply_pattern(self, pattern: TransactionPattern, text: str) -> List[Dict[str, Any]]:
        """Apply a single TransactionPattern to text and return extracted data."""
        matches = []
        regex = re.compile(pattern.regex, re.IGNORECASE | re.MULTILINE)

        for match in regex.finditer(text):
            data = pattern.defaults.copy()
            if pattern.transaction_type:
                data["transaction_type"] = pattern.transaction_type

            # Map named groups
            group_dict = match.groupdict()
            for group_name, value in group_dict.items():
                if value is not None:
                    field_name = pattern.field_map.get(group_name, group_name)
                    data[field_name] = value.strip()

            if data:
                matches.append(data)

        return matches

    def _parse_sections(self, config: SectionConfig, body: str) -> List[Dict[str, Any]]:
        """Split body into sections and extract one transaction from each."""
        sections = re.split(config.split_by, body)
        results = []

        for section in sections:
            if not section.strip():
                continue

            section_data = {}
            for pattern in config.transaction_patterns:
                matches = self._apply_pattern(pattern, section)
                if matches:
                    # Merge first match info into section_data
                    section_data.update(matches[0])

            if section_data.get("amount") or section_data.get("total_spent"):
                results.append(section_data)

        return results

    def _post_process(self, results: List[Dict[str, Any]], body: str) -> List[Dict[str, Any]]:
        """Clean up and standardize extracted data."""
        final_results = []

        # Extract common fields if missing
        txn_id = self._find_in_text(r"(?:Transaction ID|Reference|Order\s*#|ID|Reference Number|Order Reference):\s*([A-Z0-9#\-]+)", body)

        for data in results:
            # 1. Clean numeric values
            for field in ["amount", "total_spent", "fee_amount"]:
                if field in data and data[field]:
                    data[field] = str(data[field]).replace(",", "")

            # 2. Handle currency symbols
            if "currency_symbol" in data:
                symbol = data.pop("currency_symbol")
                if not data.get("currency") and symbol:
                    data["currency"] = self.template.symbol_map.get(symbol, "USD")

            # 3. Ticker mapping
            if data.get("item_name"):
                ticker = data["item_name"].upper()
                data["item_name"] = self.template.ticker_map.get(ticker, ticker)

            # 4. Default currency
            if not data.get("currency") and data.get("total_spent"):
                data["currency"] = "USD"

            # 5. Vendor
            data["vendor"] = self.template.vendor

            # 6. Transaction ID
            if not data.get("transaction_id"):
                data["transaction_id"] = txn_id

            # 7. Method
            data["extraction_method"] = "regex"

            # 8. Normalize transaction type
            if data.get("transaction_type"):
                ttype = data["transaction_type"].lower()
                if "deposit" in ttype:
                    data["transaction_type"] = "deposit"
                elif "withdrawal" in ttype or "sell" in ttype:
                    data["transaction_type"] = "withdrawal"
                elif "reward" in ttype:
                    data["transaction_type"] = "staking_reward"
                else:
                    data["transaction_type"] = "buy"
            else:
                data["transaction_type"] = "buy"

            # 9. Fee currency defaults to currency
            if data.get("fee_amount") and not data.get("fee_currency"):
                data["fee_currency"] = data.get("currency")

            final_results.append(data)

        return final_results

    def _find_in_text(self, pattern: str, text: str) -> Optional[str]:
        """Helper to find a single match."""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
