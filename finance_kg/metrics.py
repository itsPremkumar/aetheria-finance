"""
Financial metric extraction.

Extracts financial metrics like revenue, net income, EPS, P/E ratio,
debt-to-equity, ROE, etc. from text.
"""

from __future__ import annotations
import re
from typing import Any, Optional


class FinancialMetricsExtractor:
    """Extract financial metrics from text."""

    def __init__(self):
        self._patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict:
        """Compile regex patterns for metric extraction."""
        return {
            "revenue": [
                r'revenue[s]?\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)\s*(?:million|billion|trillion|M|B)?',
                r'net\s+revenue[s]?\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
                r'total\s+revenue[s]?\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
            ],
            "net_income": [
                r'net\s+income\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
                r'net\s+earnings\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
                r'net\s+profit\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
            ],
            "eps": [
                r'earnings\s+per\s+share\s*(?:of\s*)?[\$]?([\d.]+)',
                r'eps\s*(?:of\s*)?[\$]?([\d.]+)',
                r'diluted\s+eps\s*(?:of\s*)?[\$]?([\d.]+)',
            ],
            "pe_ratio": [
                r'p/e\s+ratio\s*(?:of\s*)?([\d.]+)',
                r'price[\s-]to[\s-]earnings\s*(?:of\s*)?([\d.]+)',
            ],
            "debt_to_equity": [
                r'debt[\s-]to[\s-]equity\s*(?:of\s*)?([\d.]+)',
                r'd/e\s+ratio\s*(?:of\s*)?([\d.]+)',
            ],
            "roe": [
                r'return\s+on\s+equity\s*(?:of\s*)?([\d.]+)\s*%',
                r'roe\s*(?:of\s*)?([\d.]+)\s*%',
            ],
            "roa": [
                r'return\s+on\s+assets\s*(?:of\s*)?([\d.]+)\s*%',
                r'roa\s*(?:of\s*)?([\d.]+)\s*%',
            ],
            "gross_margin": [
                r'gross\s+margin\s*(?:of\s*)?([\d.]+)\s*%',
                r'gross\s+profit\s+margin\s*(?:of\s*)?([\d.]+)\s*%',
            ],
            "operating_margin": [
                r'operating\s+margin\s*(?:of\s*)?([\d.]+)\s*%',
                r'operating\s+profit\s+margin\s*(?:of\s*)?([\d.]+)\s*%',
            ],
            "ebitda": [
                r'ebitda\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
                r'earnings\s+before\s+interest.*?taxes\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
            ],
            "market_cap": [
                r'market\s+cap\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)\s*(?:million|billion|trillion|M|B)?',
                r'market\s+capitalization\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
            ],
            "enterprise_value": [
                r'enterprise\s+value\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
                r'ev\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
            ],
            "cash_flow": [
                r'operating\s+cash\s+flow\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
                r'free\s+cash\s+flow\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
            ],
        }

    def extract(self, text: str) -> dict[str, str]:
        """Extract all financial metrics from text."""
        metrics = {}

        for metric_name, patterns in self._patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    metrics[metric_name] = match.group(1).replace(",", "")
                    break

        return metrics

    def extract_metric(self, text: str, metric_name: str) -> Optional[str]:
        """Extract a specific metric."""
        patterns = self._patterns.get(metric_name, [])
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(",", "")
        return None

    def get_available_metrics(self) -> list[str]:
        """Get list of available metric names."""
        return list(self._patterns.keys())
