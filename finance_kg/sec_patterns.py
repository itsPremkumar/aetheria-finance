"""
SEC filing parsing patterns.

Pre-trained patterns for parsing 10-K, 10-Q, 8-K, S-1 filings.
Extracts structured data from unstructured SEC filing text.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class FilingSection:
    section_type: str
    text: str
    metadata: dict = field(default_factory=dict)


class SECFilingParser:
    """Parse SEC filings using regex patterns."""

    def __init__(self):
        self._patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict:
        """Compile SEC filing section patterns."""
        return {
            "10-K": {
                "business": re.compile(r'(?:item\s*1[\.\s]*business|business\s*overview)', re.IGNORECASE),
                "risk_factors": re.compile(r'(?:item\s*1a[\.\s]*risk\s*factors|risk\s*factors)', re.IGNORECASE),
                "properties": re.compile(r'(?:item\s*2[\.\s]*properties|properties)', re.IGNORECASE),
            },
            "10-Q": {
                "financial_statements": re.compile(r'(?:financial\s*statements|condensed\s*consolidated)', re.IGNORECASE),
                "md_and_a": re.compile(r'(?:management.*discussion|md\s*&\s*a)', re.IGNORECASE),
            },
            "8-K": {
                "entry_into_material_agreement": re.compile(r'(?:entry\s*into.*material\s*agreement|item\s*1\.01)', re.IGNORECASE),
                "completion_of_acquisition": re.compile(r'(?:completion\s*of\s*acquisition|item\s*2\.01)', re.IGNORECASE),
                "results_of_operations": re.compile(r'(?:results\s*of\s*operations|item\s*2\.02)', re.IGNORECASE),
            },
            "S-1": {
                "prospectus_summary": re.compile(r'(?:prospectus\s*summary|summary)', re.IGNORECASE),
                "use_of_proceeds": re.compile(r'(?:use\s*of\s*proceeds)', re.IGNORECASE),
                "risk_factors": re.compile(r'(?:risk\s*factors)', re.IGNORECASE),
            },
        }

    def parse(self, filing_path: str) -> list[FilingSection]:
        """Parse an SEC filing into sections."""
        path = Path(filing_path)
        if not path.exists():
            raise FileNotFoundError(f"Filing not found: {filing_path}")

        text = path.read_text()

        # Detect filing type
        filing_type = self._detect_filing_type(text)
        if not filing_type:
            return [FilingSection(section_type="unknown", text=text)]

        # Split into sections
        sections = self._split_sections(text, filing_type)
        return sections

    def _detect_filing_type(self, text: str) -> Optional[str]:
        """Detect the type of SEC filing."""
        indicators = {
            "10-K": [r'10-k', r'annual\s*report', r'fiscal\s*year\s*ended'],
            "10-Q": [r'10-q', r'quarterly\s*report', r'quarter\s*ended'],
            "8-K": [r'8-k', r'current\s*report'],
            "S-1": [r's-1', r'registration\s*statement', r'prospectus'],
        }

        for filing_type, patterns in indicators.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return filing_type

        return None

    def _split_sections(self, text: str, filing_type: str) -> list[FilingSection]:
        """Split filing text into sections."""
        patterns = self._patterns.get(filing_type, {})
        sections = []

        # Find section boundaries
        section_starts = []
        for section_type, pattern in patterns.items():
            for match in pattern.finditer(text):
                section_starts.append((match.start(), section_type))

        # Sort by position
        section_starts.sort()

        # Extract sections
        for i, (start, section_type) in enumerate(section_starts):
            end = section_starts[i + 1][0] if i + 1 < len(section_starts) else len(text)
            section_text = text[start:end].strip()

            sections.append(FilingSection(
                section_type=section_type,
                text=section_text,
                metadata={"filing_type": filing_type, "start_pos": start},
            ))

        return sections

    def extract_financial_data(self, text: str) -> dict[str, Any]:
        """Extract financial data from filing text."""
        data = {}

        # Revenue patterns
        revenue_patterns = [
            r'revenue[s]?\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)\s*(?:million|billion)?',
            r'net\s+revenue[s]?\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
            r'total\s+revenue[s]?\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
        ]

        for pattern in revenue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data["revenue"] = match.group(1)
                break

        # Net income patterns
        income_patterns = [
            r'net\s+income\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
            r'net\s+earnings\s*(?:of\s*)?[\$]?([\d,]+(?:\.\d+)?)',
        ]

        for pattern in income_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data["net_income"] = match.group(1)
                break

        # EPS patterns
        eps_patterns = [
            r'earnings\s+per\s+share\s*(?:of\s*)?[\$]?([\d.]+)',
            r'eps\s*(?:of\s*)?[\$]?([\d.]+)',
        ]

        for pattern in eps_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data["eps"] = match.group(1)
                break

        return data
