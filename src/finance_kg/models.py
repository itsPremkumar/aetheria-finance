"""Core data models for financial knowledge graph."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EntityType(str, Enum):
    """Types of financial entities."""
    COMPANY = "company"
    TICKER = "ticker"
    AMOUNT = "amount"
    DATE = "date"
    PERSON = "person"
    SECTOR = "sector"
    METRIC = "metric"
    FILING = "filing"


class RelationType(str, Enum):
    """Types of financial relations."""
    ACQUIRED = "acquired"
    MERGED_WITH = "merged_with"
    INVESTED_IN = "invested_in"
    COMPETES_WITH = "competes_with"
    OWNS = "owns"
    REPORTED_REVENUE = "reported_revenue"
    REPORTED_EARNINGS = "reported_earnings"
    SUBSIDIARY_OF = "subsidiary_of"
    PARTNER_WITH = "partner_with"


class MetricType(str, Enum):
    """Types of financial metrics."""
    REVENUE = "revenue"
    EARNINGS = "earnings"
    NET_INCOME = "net_income"
    EBITDA = "ebitda"
    DEBT = "debt"
    ASSETS = "assets"
    MARKET_CAP = "market_cap"
    PE_RATIO = "pe_ratio"
    EPS = "eps"
    DIVIDEND = "dividend"


class PeriodType(str, Enum):
    """Types of financial reporting periods."""
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    TTM = "ttm"  # trailing twelve months


@dataclass
class FinancialEntity:
    """A financial entity extracted from text."""
    id: str
    name: str
    entity_type: EntityType
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_text: str = ""


@dataclass
class FinancialRelation:
    """A relation between financial entities."""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source_text: str = ""
    temporal_context: Optional[str] = None


@dataclass
class FinancialMetric:
    """A financial metric tied to an entity and period."""
    entity_id: str
    metric_type: MetricType
    value: float
    currency: str = "USD"
    period: Optional[str] = None
    period_type: Optional[PeriodType] = None
    source_text: str = ""


@dataclass
class SECFiling:
    """Parsed SEC filing metadata."""
    cik: str
    company_name: str
    form_type: str  # 10-K, 10-Q, 8-K, etc.
    filing_date: str
    period_of_report: Optional[str] = None
    items: dict[str, str] = field(default_factory=dict)
