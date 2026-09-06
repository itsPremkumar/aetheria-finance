"""Entity extractor for financial text — 100% offline rule-based."""

from __future__ import annotations

import re
from typing import Any, Optional

from finance_kg.models import EntityType, FinancialEntity

# Ticker pattern: 1-5 uppercase letters in parentheses or standalone
_TICKER_PATTERN = re.compile(
    r"""
    (?:\()(?P<ticker_p>[A-Z]{1,5})(?:\))   # (AAPL)
    |
    (?P<ticker_s>\b[A-Z]{2,5}\b(?=\s+(?:stock|shares|Inc|Corp|Ltd|LLC|Company|Group|Holdings|International|Technologies|Enterprises|Capital|Financial|Pharma|Therapeutics|Bio|Energy|Motors|Industries|Systems|Solutions|Services|Health|Media|Labs|Networks|Securities|Ventures|Partners|Assurance|Re|Insurance|Bank|Trust|Fund|ETF|REIT)))  # Apple Inc
    |
    (?P<ticker_c>[A-Z]{1,5}):[A-Z]+  # NYSE:NASDAQ
    """,
    re.VERBOSE,
)

# Common financial filing keywords
_FILING_TYPES = {
    "10-K": "Annual Report",
    "10-Q": "Quarterly Report",
    "8-K": "Current Report",
    "S-1": "Registration Statement",
    "13F": "Institutional Holdings",
    "4": "Insider Trading",
    "DEF 14A": "Proxy Statement",
    "424B": "Prospectus",
}

# Common currency/amount patterns
_AMOUNT_PATTERN = re.compile(
    r"""
    (?P<currency>USD|EUR|GBP|JPY|CNY|₹|\$|€|£|¥)?
    \s*
    (?P<value>(?:\d{1,3}(?:,\d{3})+|\d+)\.?\d*)
    \s*
    (?P<unit>billion|million|trillion|M|B|K|T|bn|mn)?
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Date patterns
_DATE_PATTERNS = [
    # ISO format
    re.compile(r"\b(?P<year>\d{4})[-/](?P<month>\d{2})[-/](?P<day>\d{2})\b"),
    # Month DD, YYYY
    re.compile(
        r"\b(?P<month_name>January|February|March|April|May|June|July|August|September|October|November|December)\s+(?P<day>\d{1,2}),?\s+(?P<year>\d{4})\b",
        re.IGNORECASE,
    ),
    # MM/DD/YYYY
    re.compile(r"\b(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})\b"),
    # Q1/Q2/Q3/Q4 YYYY
    re.compile(r"\b(?P<quarter>Q[1-4])\s*(?P<year>\d{4})\b", re.IGNORECASE),
    # FY2024, FY 2024
    re.compile(r"\bFY\s?(?P<year>\d{4})\b", re.IGNORECASE),
]

# Company suffixes for recognition
_COMPANY_SUFFIXES = [
    "Inc",
    "Corp",
    "Corporation",
    "Ltd",
    "Limited",
    "LLC",
    "Company",
    "Co",
    "Group",
    "Holdings",
    "International",
    "Technologies",
    "Tech",
    "Enterprises",
    "Capital",
    "Financial",
    "Pharma",
    "Therapeutics",
    "Bio",
    "Energy",
    "Motors",
    "Industries",
    "Systems",
    "Solutions",
    "Services",
    "Health",
    "Media",
    "Labs",
    "Networks",
    "Securities",
    "Ventures",
    "Partners",
    "Assurance",
    "Re",
    "Insurance",
    "Bank",
    "Trust",
    "Fund",
    "ETF",
    "REIT",
    "Association",
    "Exchange",
    "Bancorp",
    "Bancshares",
    "Airlines",
    "Airways",
    "Telecom",
    "Mobile",
    "Digital",
    "Cloud",
    "Software",
    "Semiconductor",
    "Electronics",
    "Robotics",
    "Dynamics",
    "Materials",
    "Chemicals",
    "Steel",
    "Pharmaceuticals",
    "Diagnostics",
    "Imaging",
    "Devices",
    "Sciences",
    "Biotech",
    "Genomics",
    "Petroleum",
    "Mining",
    "Materials",
    "Logistics",
    "Transport",
    "Hospitality",
    "Resorts",
    "Casinos",
    "Beverage",
    "Foods",
    "Brands",
    "Retail",
    "Department",
    "Fashion",
    "Apparel",
    "Automotive",
    "Aerospace",
    "Defense",
    "Construction",
    "Real Estate",
    "Property",
    "Properties",
]

# Sector keywords
_SECTOR_KEYWORDS = {
    "technology": EntityType.SECTOR,
    "healthcare": EntityType.SECTOR,
    "financial": EntityType.SECTOR,
    "energy": EntityType.SECTOR,
    "consumer": EntityType.SECTOR,
    "industrial": EntityType.SECTOR,
    "materials": EntityType.SECTOR,
    "utilities": EntityType.SECTOR,
    "real estate": EntityType.SECTOR,
    "telecommunications": EntityType.SECTOR,
}

# Financial metric keywords
_METRIC_KEYWORDS = {
    "revenue": "revenue",
    "earnings": "earnings",
    "net income": "net_income",
    "ebitda": "ebitda",
    "debt": "debt",
    "total assets": "assets",
    "market capitalization": "market_cap",
    "market cap": "market_cap",
    "p/e ratio": "pe_ratio",
    "price-to-earnings": "pe_ratio",
    "eps": "eps",
    "dividend": "dividend",
}

# Known major companies (offline gazetteer)
_KNOWN_COMPANIES = {
    "apple": "Apple Inc.",
    "microsoft": "Microsoft Corporation",
    "google": "Alphabet Inc.",
    "alphabet": "Alphabet Inc.",
    "amazon": "Amazon.com Inc.",
    "tesla": "Tesla Inc.",
    "meta": "Meta Platforms Inc.",
    "nvidia": "NVIDIA Corporation",
    "berkshire": "Berkshire Hathaway Inc.",
    "johnson": "Johnson & Johnson",
    "jpmorgan": "JPMorgan Chase & Co.",
    "visa": "Visa Inc.",
    "walmart": "Walmart Inc.",
    "procter": "Procter & Gamble Co.",
    "unitedhealth": "UnitedHealth Group Inc.",
    "home depot": "The Home Depot Inc.",
    "mastercard": "Mastercard Inc.",
    "exxon": "Exxon Mobil Corporation",
    "chevron": "Chevron Corporation",
    "pfizer": "Pfizer Inc.",
    "coca-cola": "The Coca-Cola Company",
    "pepsico": "PepsiCo Inc.",
    "disney": "The Walt Disney Company",
    "netflix": "Netflix Inc.",
    "adobe": "Adobe Inc.",
    "salesforce": "Salesforce Inc.",
    "oracle": "Oracle Corporation",
    "ibm": "International Business Machines Corp.",
    "intel": "Intel Corporation",
    "amd": "Advanced Micro Devices Inc.",
    "qualcomm": "Qualcomm Inc.",
    "broadcom": "Broadcom Inc.",
    "texas instruments": "Texas Instruments Inc.",
    "cisco": "Cisco Systems Inc.",
    "verizon": "Verizon Communications Inc.",
    "at&t": "AT&T Inc.",
    "t-mobile": "T-Mobile US Inc.",
    "comcast": "Comcast Corporation",
    "boeing": "The Boeing Company",
    "airbus": "Airbus SE",
    "lockheed": "Lockheed Martin Corp.",
    "raytheon": "Raytheon Technologies Corp.",
    "general electric": "General Electric Co.",
    "3m": "3M Company",
    "caterpillar": "Caterpillar Inc.",
    "deere": "Deere & Company",
    "ford": "Ford Motor Company",
    "general motors": "General Motors Company",
    "toyota": "Toyota Motor Corp.",
    "volkswagen": "Volkswagen AG",
    "shell": "Shell plc",
    "bp": "BP plc",
    "total": "TotalEnergies SE",
    "chevron": "Chevron Corp.",
}

# Common ticker to company mapping
_TICKER_MAP = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "GOOG": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "TSLA": "Tesla Inc.",
    "META": "Meta Platforms Inc.",
    "NVDA": "NVIDIA Corporation",
    "BRK.B": "Berkshire Hathaway Inc.",
    "BRK.A": "Berkshire Hathaway Inc.",
    "JNJ": "Johnson & Johnson",
    "JPM": "JPMorgan Chase & Co.",
    "V": "Visa Inc.",
    "WMT": "Walmart Inc.",
    "PG": "Procter & Gamble Co.",
    "UNH": "UnitedHealth Group Inc.",
    "HD": "The Home Depot Inc.",
    "MA": "Mastercard Inc.",
    "XOM": "Exxon Mobil Corporation",
    "CVX": "Chevron Corporation",
    "PFE": "Pfizer Inc.",
    "KO": "The Coca-Cola Company",
    "PEP": "PepsiCo Inc.",
    "DIS": "The Walt Disney Company",
    "NFLX": "Netflix Inc.",
    "ADBE": "Adobe Inc.",
    "CRM": "Salesforce Inc.",
    "ORCL": "Oracle Corporation",
    "IBM": "International Business Machines Corp.",
    "INTC": "Intel Corporation",
    "AMD": "Advanced Micro Devices Inc.",
    "QCOM": "Qualcomm Inc.",
    "AVGO": "Broadcom Inc.",
    "TXN": "Texas Instruments Inc.",
    "CSCO": "Cisco Systems Inc.",
    "VZ": "Verizon Communications Inc.",
    "T": "AT&T Inc.",
    "TMUS": "T-Mobile US Inc.",
    "CMCSA": "Comcast Corporation",
    "BA": "The Boeing Company",
    "LMT": "Lockheed Martin Corp.",
    "GE": "General Electric Co.",
    "MMM": "3M Company",
    "CAT": "Caterpillar Inc.",
    "DE": "Deere & Company",
    "F": "Ford Motor Company",
    "GM": "General Motors Company",
    "TM": "Toyota Motor Corp.",
}


def extract_entities(text: str) -> list[FinancialEntity]:
    """Extract financial entities from text using rule-based patterns.

    This function operates 100% offline using regex patterns and gazetteers.
    No external API calls or LLM inference required.
    """
    entities: list[FinancialEntity] = []
    seen: set[str] = set()
    entity_counter = 0

    def add_entity(name: str, e_type: EntityType, **kwargs: Any) -> Optional[FinancialEntity]:
        nonlocal entity_counter
        key = f"{name.lower()}:{e_type.value}"
        if key in seen:
            return None
        seen.add(key)
        entity_counter += 1
        entity = FinancialEntity(
            id=f"ent_{entity_counter:04d}",
            name=name,
            entity_type=e_type,
            source_text=text[:200],
            **kwargs,
        )
        entities.append(entity)
        return entity

    # Extract ticker symbols
    for match in _TICKER_PATTERN.finditer(text):
        ticker = match.group("ticker_p") or match.group("ticker_s") or match.group("ticker_c")
        if ticker:
            clean_ticker = ticker.split(":")[0] if ":" in ticker else ticker
            add_entity(
                clean_ticker,
                EntityType.TICKER,
                metadata={"canonical_company": _TICKER_MAP.get(clean_ticker, "")},
            )

    # Extract known companies
    text_lower = text.lower()
    for key, company_name in _KNOWN_COMPANIES.items():
        if key in text_lower:
            add_entity(company_name, EntityType.COMPANY, aliases=[key])

    # Extract company names by pattern (e.g., "XYZ Inc.")
    company_pattern = re.compile(
        r"\b([A-Z][a-zA-Z&\'\-\.]+(?:\s+[A-Z][a-zA-Z&\'\-\.]+)*\s+(?:"
        + "|".join(_COMPANY_SUFFIXES)
        + r"))\b"
    )
    for match in company_pattern.finditer(text):
        company = match.group(1).strip()
        if len(company) > 3:  # Filter out short false positives
            add_entity(company, EntityType.COMPANY)

    # Extract amounts
    for match in _AMOUNT_PATTERN.finditer(text):
        value_str = match.group("value", "")
        if value_str:
            try:
                value = float(value_str.replace(",", ""))
                unit = (match.group("unit") or "").lower()
                currency = match.group("currency") or ""
                if value > 0:
                    add_entity(
                        f"{currency}{value_str} {unit}".strip(),
                        EntityType.AMOUNT,
                        metadata={
                            "value": value,
                            "currency": currency,
                            "unit": unit,
                            "raw": match.group(0).strip(),
                        },
                    )
            except ValueError:
                continue

    # Extract dates
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            date_str = match.group(0)
            add_entity(date_str, EntityType.DATE, metadata={"date_str": date_str})

    # Extract sectors
    for keyword, sector_type in _SECTOR_KEYWORDS.items():
        if keyword in text_lower:
            add_entity(keyword.title(), sector_type, metadata={"sector": keyword})

    # Extract filings
    for form_type, description in _FILING_TYPES.items():
        if form_type.lower() in text_lower or form_type in text:
            add_entity(form_type, EntityType.FILING, metadata={"description": description})

    # Extract financial metrics
    for keyword, metric_name in _METRIC_KEYWORDS.items():
        if keyword in text_lower:
            add_entity(
                keyword.title(),
                EntityType.METRIC,
                metadata={"metric_type": metric_name},
            )

    return entities
