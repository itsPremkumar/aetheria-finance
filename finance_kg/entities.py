"""
Entity extraction for financial text.

Extracts companies, tickers, monetary amounts, dates, percentages,
and financial metrics from unstructured text.
"""

from __future__ import annotations
import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class EntityType(Enum):
    COMPANY = "company"
    TICKER = "ticker"
    AMOUNT = "amount"
    DATE = "date"
    PERCENTAGE = "percentage"
    METRIC = "metric"
    PERSON = "person"


@dataclass
class Entity:
    id: str
    text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float = 1.0
    normalized: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "type": self.entity_type.value,
            "start": self.start_pos,
            "end": self.end_pos,
            "confidence": self.confidence,
            "normalized": self.normalized,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return f"Entity({self.text}, {self.entity_type.value})"


class EntityExtractor:
    """Extract financial entities from text using regex patterns."""

    def __init__(self):
        self._patterns = self._compile_patterns()
        self._company_suffixes = self._load_company_suffixes()
        self._ticker_cache: dict[str, str] = {}

    def _compile_patterns(self) -> dict:
        """Compile regex patterns for entity extraction."""
        return {
            EntityType.AMOUNT: re.compile(
                r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|trillion|M|B|K))?'
                r'|[\d,]+(?:\.\d+)?\s*(?:million|billion|trillion)\s*(?:dollars|USD)?',
                re.IGNORECASE,
            ),
            EntityType.PERCENTAGE: re.compile(
                r'\d+(?:\.\d+)?%'
                r'|\d+(?:\.\d+)?\s*percent',
                re.IGNORECASE,
            ),
            EntityType.DATE: re.compile(
                r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
                r'|\d{1,2}/\d{1,2}/\d{2,4}'
                r'|\d{4}-\d{2}-\d{2}'
                r'|Q[1-4]\s+\d{4}'
                r'|FY\d{2,4}',
                re.IGNORECASE,
            ),
            EntityType.TICKER: re.compile(
                r'\b([A-Z]{2,5})\b(?=\s*(?:\(|,|\.|\s|$))',
            ),
        }

    def _load_company_suffixes(self) -> set:
        """Load common company name suffixes."""
        return {
            "Inc.", "Inc", "Corp.", "Corp", "Corporation",
            "Ltd.", "Ltd", "Limited", "LLC", "L.L.C.",
            "Co.", "Co", "Company", "Holdings", "Group",
            "International", "Intl", "Technologies", "Tech",
            "Solutions", "Services", "Systems", "Enterprises",
            "Partners", "Capital", "Ventures", "Securities",
            "Financial", "Bank", "Trust", "Investments",
        }

    def extract(self, text: str) -> list[Entity]:
        """Extract all entities from text."""
        entities = []

        # Extract amounts
        entities.extend(self._extract_with_pattern(text, EntityType.AMOUNT))

        # Extract percentages
        entities.extend(self._extract_with_pattern(text, EntityType.PERCENTAGE))

        # Extract dates
        entities.extend(self._extract_with_pattern(text, EntityType.DATE))

        # Extract tickers (with context validation)
        entities.extend(self._extract_tickers(text))

        # Extract companies
        entities.extend(self._extract_companies(text))

        # Deduplicate and sort
        entities = self._deduplicate(entities)
        entities.sort(key=lambda e: e.start_pos)

        return entities

    def _extract_with_pattern(
        self,
        text: str,
        entity_type: EntityType,
    ) -> list[Entity]:
        """Extract entities using a compiled pattern."""
        pattern = self._patterns.get(entity_type)
        if not pattern:
            return []

        entities = []
        for match in pattern.finditer(text):
            entity = Entity(
                id=f"{entity_type.value}_{match.start()}",
                text=match.group(),
                entity_type=entity_type,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.9,
                normalized=self._normalize(entity_type, match.group()),
            )
            entities.append(entity)

        return entities

    def _extract_tickers(self, text: str) -> list[Entity]:
        """Extract stock tickers with context validation."""
        entities = []
        pattern = self._patterns[EntityType.TICKER]

        for match in pattern.finditer(text):
            ticker = match.group(1)
            # Validate: must be near company-related context
            if self._is_likely_ticker(ticker, text, match.start()):
                entity = Entity(
                    id=f"ticker_{match.start()}",
                    text=ticker,
                    entity_type=EntityType.TICKER,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.7,
                    normalized=ticker.upper(),
                    metadata={"context": self._get_context(text, match.start(), match.end())},
                )
                entities.append(entity)

        return entities

    def _extract_companies(self, text: str) -> list[Entity]:
        """Extract company names."""
        entities = []

        # Pattern: Company name with suffix
        company_pattern = re.compile(
            r'\b([A-Z][a-zA-Z&\'\-\s]+(?:' + '|'.join(re.escape(s) for s in self._company_suffixes) + r'))\b'
        )

        for match in company_pattern.finditer(text):
            entity = Entity(
                id=f"company_{match.start()}",
                text=match.group(1).strip(),
                entity_type=EntityType.COMPANY,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.8,
                normalized=self._normalize_company(match.group(1)),
            )
            entities.append(entity)

        return entities

    def _is_likely_ticker(self, ticker: str, text: str, pos: int) -> bool:
        """Check if a ticker is likely a real stock ticker."""
        # Skip common words that look like tickers
        common_words = {
            "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN",
            "HER", "WAS", "ONE", "OUR", "OUT", "HAS", "HIS", "HOW", "ITS",
            "MAY", "NEW", "NOW", "OLD", "SEE", "WAY", "WHO", "BOY", "DID",
            "GET", "HIM", "HIT", "LET", "SAY", "SHE", "TOO", "USE", "SEC",
            "CEO", "CFO", "COO", "IPO", "EPS", "P/E", "GDP", "Fed", "NY",
            "US", "UK", "EU", "GDP", "FDA", "FCC", "FAA", "IRS", "FBI",
            "CIA", "NBA", "NFL", "MLB", "NHL", "NCAA", "FIFA", "NASA",
            "NOAA", "USDA", "VA", "OK", "TV", "PC", "AI", "IT", "HR",
        }
        if ticker.upper() in common_words:
            return False

        # Check context for financial keywords
        context = self._get_context(text, pos, pos + len(ticker))
        financial_keywords = [
            "stock", "shares", "trading", "market", "exchange", "nasdaq", "nyse",
            "price", "ticker", "listed", "public", "company", "corporation",
            "inc", "corp", "ltd", "earnings", "revenue", "profit", "loss",
        ]
        return any(kw in context.lower() for kw in financial_keywords)

    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get surrounding context for a position."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end]

    def _normalize(self, entity_type: EntityType, text: str) -> str:
        """Normalize entity text."""
        if entity_type == EntityType.AMOUNT:
            return self._normalize_amount(text)
        elif entity_type == EntityType.DATE:
            return self._normalize_date(text)
        elif entity_type == EntityType.PERCENTAGE:
            return text.replace("%", "").strip()
        return text

    def _normalize_amount(self, text: str) -> str:
        """Normalize monetary amounts."""
        # Remove $ and commas
        cleaned = text.replace("$", "").replace(",", "").strip()

        # Convert words to numbers
        multipliers = {
            "million": 1_000_000,
            "billion": 1_000_000_000,
            "trillion": 1_000_000_000_000,
            "M": 1_000_000,
            "B": 1_000_000_000,
            "K": 1_000,
        }

        for word, mult in multipliers.items():
            if word.lower() in cleaned.lower():
                num_part = re.search(r'[\d.]+', cleaned)
                if num_part:
                    return str(float(num_part.group()) * mult)

        # Plain number
        num_part = re.search(r'[\d.]+', cleaned)
        if num_part:
            return num_part.group()

        return cleaned

    def _normalize_date(self, text: str) -> str:
        """Normalize dates to ISO format."""
        # Try various formats
        formats = [
            "%B %d, %Y",
            "%B %d %Y",
            "%m/%d/%Y",
            "%m/%d/%y",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(text.strip(), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Handle quarters
        quarter_match = re.match(r'Q(\d)\s+(\d{4})', text, re.IGNORECASE)
        if quarter_match:
            quarter = int(quarter_match.group(1))
            year = quarter_match.group(2)
            month = (quarter - 1) * 3 + 1
            return f"{year}-{month:02d}-01"

        # Handle fiscal years
        fy_match = re.match(r'FY(\d{2,4})', text, re.IGNORECASE)
        if fy_match:
            year = int(fy_match.group(1))
            if year < 100:
                year += 2000
            return str(year)

        return text

    def _normalize_company(self, text: str) -> str:
        """Normalize company name."""
        # Remove extra whitespace
        cleaned = " ".join(text.split())
        # Title case
        cleaned = cleaned.title()
        return cleaned

    def _deduplicate(self, entities: list[Entity]) -> list[Entity]:
        """Remove overlapping entities, keeping highest confidence."""
        if not entities:
            return []

        # Sort by confidence (descending)
        entities.sort(key=lambda e: -e.confidence)

        result = []
        seen_positions = set()

        for entity in entities:
            # Check for overlap
            overlap = False
            for start, end in seen_positions:
                if (entity.start_pos < end and entity.end_pos > start):
                    overlap = True
                    break

            if not overlap:
                result.append(entity)
                seen_positions.add((entity.start_pos, entity.end_pos))

        return result

    def extract_with_context(
        self,
        text: str,
        context_window: int = 100,
    ) -> list[dict]:
        """Extract entities with surrounding context."""
        entities = self.extract(text)
        results = []

        for entity in entities:
            ctx_start = max(0, entity.start_pos - context_window)
            ctx_end = min(len(text), entity.end_pos + context_window)

            results.append({
                "entity": entity.to_dict(),
                "context": text[ctx_start:ctx_end],
            })

        return results
