"""SEC filing parser — 100% offline pattern-based extraction."""

from __future__ import annotations

import re
from typing import Any, Optional

from finance_kg.models import SECFiling

# SEC form types and their key sections
_FORM_SECTIONS: dict[str, list[str]] = {
    "10-K": [
        "business",
        "risk_factors",
        "properties",
        "legal",
        "market_for_registrants",
        "management_discussion",
        "financial_statements",
        "controls",
    ],
    "10-Q": [
        "financial_statements",
        "management_discussion",
        "controls",
    ],
    "8-K": [
        "entry_into_material_agreement",
        "termination_of_material_agreement",
        "bankruptcy",
        "mine_safety",
        "completion_of_acquisition_or_disposition",
        "results_of_operations",
        "creation_of_direct_obligation",
        "triggering_events",
        "costs_associated_with_exit",
        "material_impairments",
        "changes_in_control",
        "departures_of_directors",
        "amendments_to_articles",
        "fiscal_year_change",
        "trading_symbol_change",
        "director_appointments",
    ],
    "S-1": [
        "business",
        "risk_factors",
        "use_of_proceeds",
        "dividend_policy",
        "capitalization",
        "dilution",
        "management_discussion",
        "principal_stockholders",
        "description_of_capital_stock",
        "shares_eligible_for_future_sale",
        "underwriting",
        "legal_matters",
    ],
}

# CIK pattern: 10-digit zero-padded number
_CIK_PATTERN = re.compile(r"\b0*(\d{10})\b")

# Company name patterns in filings
_COMPANY_NAME_PATTERNS = [
    re.compile(r"(?:company\s+name|exact\s+name\s+of\s+registrant)[^\n]*?:\s*(.+)", re.IGNORECASE),
    re.compile(r"(?:entity\s+name|registrant)[^\n]*?:\s*(.+)", re.IGNORECASE),
]

# Fiscal year / period patterns
_PERIOD_PATTERNS = [
    re.compile(r"(?:fiscal\s+year|period\s+of\s+report|period\s+ended)[^\n]*?:\s*(.+)", re.IGNORECASE),
    re.compile(r"(?:for\s+the\s+(?:fiscal\s+year|period)\s+ended)[^\n]*?:\s*(.+)", re.IGNORECASE),
]

# Filing date patterns
_FILING_DATE_PATTERNS = [
    re.compile(r"(?:filing\s+date|date\s+filed|accepted)[^\n]*?:\s*(.+)", re.IGNORECASE),
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
]

# Form type patterns
_FORM_TYPE_PATTERNS = [
    re.compile(r"\b(10-K|10-K/A|10-K405|10-K405/A)\b"),
    re.compile(r"\b(10-Q|10-Q/A)\b"),
    re.compile(r"\b(8-K|8-K/A)\b"),
    re.compile(r"\b(S-1|S-1/A|S-1MEF)\b"),
    re.compile(r"\b(13F|13F-HR|13F-HR/A)\b"),
    re.compile(r"\b(4|4/A)\b"),
    re.compile(r"\b(DEF 14A|DEF 14C)\b"),
    re.compile(r"\b(424B\d?)\b"),
]


def _extract_cik(text: str) -> Optional[str]:
    """Extract CIK from filing text."""
    match = _CIK_PATTERN.search(text)
    return match.group(1) if match else None


def _extract_company_name(text: str) -> Optional[str]:
    """Extract company name from filing text."""
    for pattern in _COMPANY_NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def _extract_form_type(text: str) -> Optional[str]:
    """Extract form type from filing text."""
    for pattern in _FORM_TYPE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).upper()
    return None


def _extract_period(text: str) -> Optional[str]:
    """Extract fiscal period from filing text."""
    for pattern in _PERIOD_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def _extract_filing_date(text: str) -> Optional[str]:
    """Extract filing date from filing text."""
    for pattern in _FILING_DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def _extract_section(text: str, section_name: str) -> Optional[str]:
    """Extract a specific section from a filing text."""
    # Section headers are typically in uppercase or have specific formatting
    section_header = section_name.upper().replace("_", " ")
    
    # Try to find section start
    pattern = re.compile(
        rf"(?:^|\n)\s*(?:\d+\.?\s*)?{re.escape(section_header)}[\s\.\-]*\n",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(text)
    
    if match:
        start = match.end()
        # Find next section header (typically in all caps)
        next_section = re.search(
            r"\n\s*(?:\d+\.?\s*)?[A-Z][A-Z\s]{3,}[\s\.\-]*\n",
            text[start + 100:],  # Skip some content to avoid false positives
        )
        if next_section:
            end = start + 100 + next_section.start()
            return text[start:end].strip()
        else:
            # Return remaining text
            return text[start:].strip()
    
    return None


def parse_sec_filing(text: str) -> SECFiling:
    """Parse an SEC filing text into structured metadata.

    This is a pattern-based parser that works 100% offline.
    For production use, consider combining with edgar-downloader
    for fetching filings.
    """
    cik = _extract_cik(text) or ""
    company_name = _extract_company_name(text) or "Unknown"
    form_type = _extract_form_type(text) or "Unknown"
    filing_date = _extract_filing_date(text) or ""
    period = _extract_period(text)

    # Extract known sections for this form type
    sections: dict[str, str] = {}
    if form_type in _FORM_SECTIONS:
        for section_name in _FORM_SECTIONS[form_type]:
            section_text = _extract_section(text, section_name)
            if section_text:
                sections[section_name] = section_text[:5000]  # Limit section size

    return SECFiling(
        cik=cik,
        company_name=company_name,
        form_type=form_type,
        filing_date=filing_date,
        period_of_report=period,
        items=sections,
    )


def extract_filing_items(text: str, form_type: str) -> dict[str, str]:
    """Extract specific items from an SEC filing."""
    sections: dict[str, str] = {}
    
    # Common item patterns (e.g., "Item 1.", "ITEM 1.", "1. Business")
    item_pattern = re.compile(
        r"(?:^|\n)\s*(?:Item|ITEM)\s+(\d+[A-Z]?)\.?\s*([^\n]*)\n",
        re.MULTILINE,
    )
    
    matches = list(item_pattern.finditer(text))
    
    for i, match in enumerate(matches):
        item_num = match.group(1)
        item_title = match.group(2).strip()
        
        # Find content until next item
        start = match.end()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
            content = text[start:end].strip()
        else:
            content = text[start:].strip()
        
        sections[f"item_{item_num}"] = content
        sections[f"item_{item_num}_title"] = item_title
    
    return sections
