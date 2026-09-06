"""Relation extractor for financial text — 100% offline rule-based."""

from __future__ import annotations

import re
from typing import Any, Optional

from finance_kg.models import FinancialRelation, RelationType, FinancialEntity, EntityType

# Relation pattern definitions: (relation_type, regex_pattern)
# These patterns identify relationship indicators in financial text.
_RELATION_PATTERNS: list[tuple[RelationType, re.Pattern[str]]] = [
    (
        RelationType.ACQUIRED,
        re.compile(
            r"""
            (?P<source>[A-Z][a-zA-Z&\'\-\.]+(?:\s+[A-Z][a-zA-Z&\'\-\.]+){0,5}\s+(?:Inc|Corp|Ltd|LLC|Company|Co|Group|Holdings|International|Technologies|Tech|Enterprises|Capital|Financial|Corporation|Limited|PLC|SE|AG|NV|BV|S\.A|AB)\.?)
            \s+
            (?:acquired|bought|purchased|to acquire|to buy|agreed to acquire|completes acquisition of|finalizes acquisition of|announced acquisition of)
            \s+
            (?P<target>[A-Z][a-zA-Z&\'\-\.]+(?:\s+[A-Z][a-zA-Z&\'\-\.]+){0,5}\s+(?:Inc|Corp|Ltd|LLC|Company|Co|Group|Holdings|International|Technologies|Tech|Enterprises|Capital|Financial|Corporation|Limited|PLC|SE|AG|NV|BV|S\.A|AB)\.?)
            """,
            re.VERBOSE | re.IGNORECASE,
        ),
    ),
    (
        RelationType.MERGED_WITH,
        re.compile(
            r"""
            (?P<source>[A-Z][a-zA-Z&\'\-\.]+(?:\s+[A-Z][a-zA-Z&\'\-\.]+){0,5}\s+(?:Inc|Corp|Ltd|LLC|Company|Co|Group|Holdings|International|Technologies|Tech|Enterprises|Capital|Financial|Corporation|Limited|PLC|SE|AG|NV|BV|S\.A|AB)\.?)
            \s+
            (?:merged with|merger with|combines with|to merge with|completes merger with|announces merger with|enters merger agreement with)
            \s+
            (?P<target>[A-Z][a-zA-Z&\'\-\.]+(?:\s+[A-Z][a-zA-Z&\'\-\.]+){0,5}\s+(?:Inc|Corp|Ltd|LLC|Company|Co|Group|Holdings|International|Technologies|Tech|Enterprises|Capital|Financial|Corporation|Limited|PLC|SE|AG|NV|BV|S\.A|AB)\.?)
            """,
            re.VERBOSE | re.IGNORECASE,
        ),
    ),
    (
        RelationType.INVESTED_IN,
        re.compile(
            r"""
            (?P<source>[A-Z][a-zA-Z&\'\-\.]+(?:\s+[A-Z][a-zA-Z&\'\-\.]+){0,5}\s+(?:Inc|Corp|Ltd|LLC|Company|Co|Group|Holdings|International|Technologies|Tech|Enterprises|Capital|Financial|Corporation|Limited|PLC|SE|AG|NV|BV|S\.A|AB)\.?)
            \s+
            (?:invested in|led (?:a |the )?(?:funding round|series|investment round)|participated in (?:a |the )?(?:funding round|series|investment round)|joins (?:a |the )?funding round|backs|funds|provides funding to|finances|gives funding to)
            \s+
            (?P<target>[A-Z][a-zA-Z&\'\-\.]+(?:\s+[A-Z][a-zA-Z&\'\-\.]+){0,5}\s+(?:Inc|Corp|Ltd|LLC|Company|Co|Group|Holdings|International|Technologies|Tech|Enterprises|Capital|Financial|Corporation|Limited|PLC|SE|AG|NV|BV|S\.A|AB)\.?)
            """,
            re.VERBOSE | re.IGNORECASE,
        ),
    ),
    (
        RelationType.COMPETES_WITH,
        re.compile(
            r"""
            (?P<source>[A-Z][a-zA-Z&\'\-\.]+(?:\s+[A-Z][a-zA-Z&\'\-\.]+){0,5}\s+(?:Inc|Corp|Ltd|LLC|Company|Co|Group|Holdings|International|Technologies|Tech|Enterprises|Capital|Financial|Corporation|Limited|PLC|SE|AG|NV|BV|S\.A|AB)\.?)
            \s+
            (?:competes with|competition from|rival of|versus|vs\.|competing against|faces competition from)
            \s+
            (?P<target>[A-Z][a-zA-Z&\'\-\.]+(?:\s+[A-Z][a-zA-Z&\'\-\.]+){0,5}\s+(?:Inc|Corp|Ltd|LLC|Company|Co|Group|Holdings|International|Technologies|Tech|Enterprises|Capital|Financial|Corporation|Limited|PLC|SE|AG|NV|BV|S\.A|AB)\.?)
            """,
            re.VERBOSE | re.IGNORECASE,
        ),
    ),
]

# Temporal context patterns
_TEMPORAL_PATTERNS = [
    (re.compile(r"\b(Q[1-4])\s*(\d{4})\b", re.IGNORECASE), "quarterly"),
    (re.compile(r"\bFY\s?(\d{4})\b", re.IGNORECASE), "yearly"),
    (re.compile(r"\b(\d{4})\b"), "year"),
    (re.compile(r"\b(today|yesterday|last (?:week|month|quarter|year)|next (?:week|month|quarter|year))\b", re.IGNORECASE), "relative"),
]


def _find_entity_by_name(entities: list[FinancialEntity], name: str) -> Optional[FinancialEntity]:
    """Find an entity in the list by name (fuzzy match)."""
    name_lower = name.lower().strip()
    # Try exact match first
    for entity in entities:
        if entity.name.lower() == name_lower:
            return entity
        if name_lower in [a.lower() for a in entity.aliases]:
            return entity
    # Try partial match
    for entity in entities:
        if entity.name.lower().startswith(name_lower) or name_lower.startswith(entity.name.lower()):
            return entity
    # Try suffix-based match (remove common suffixes)
    clean_name = re.sub(
        r"\s+(?:Inc|Corp|Ltd|LLC|Company|Co|Group|Holdings|International|Technologies|Tech|Enterprises|Capital|Financial|Corporation|Limited|PLC|SE|AG|NV|BV|S\.A|AB)\.?$",
        "",
        name_lower,
        flags=re.IGNORECASE,
    ).strip()
    for entity in entities:
        clean_entity = re.sub(
            r"\s+(?:Inc|Corp|Ltd|LLC|Company|Co|Group|Holdings|International|Technologies|Tech|Enterprises|Capital|Financial|Corporation|Limited|PLC|SE|AG|NV|BV|S\.A|AB)\.?$",
            "",
            entity.name.lower(),
            flags=re.IGNORECASE,
        ).strip()
        if clean_entity == clean_name:
            return entity
        if clean_name in clean_entity or clean_entity in clean_name:
            return entity
    return None


def _extract_temporal_context(text: str) -> Optional[str]:
    """Extract temporal context from text near a relation."""
    for pattern, period_type in _TEMPORAL_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def extract_relations(
    text: str,
    entities: Optional[list[FinancialEntity]] = None,
) -> list[FinancialRelation]:
    """Extract financial relations from text using rule-based patterns.

    This function operates 100% offline using regex patterns.
    No external API calls or LLM inference required.
    """
    relations: list[FinancialRelation] = []
    relation_counter = 0

    # If entities not provided, we'll create placeholder references
    if entities is None:
        entities = []

    def find_or_create_entity_ref(name: str) -> tuple[str, Optional[FinancialEntity]]:
        """Find existing entity by name or return name for later resolution."""
        entity = _find_entity_by_name(entities, name)
        if entity:
            return entity.id, entity
        return name, None

    for relation_type, pattern in _RELATION_PATTERNS:
        for match in pattern.finditer(text):
            source_name = match.group("source").strip()
            target_name = match.group("target").strip()

            source_id, source_entity = find_or_create_entity_ref(source_name)
            target_id, target_entity = find_or_create_entity_ref(target_name)

            # Skip self-relations
            if source_id == target_id:
                continue

            relation_counter += 1
            temporal_context = _extract_temporal_context(text[max(0, match.start() - 50):match.end() + 50])

            relation = FinancialRelation(
                id=f"rel_{relation_counter:04d}",
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type,
                metadata={
                    "source_name": source_name,
                    "target_name": target_name,
                    "matched_text": match.group(0),
                },
                confidence=0.85,
                source_text=text[max(0, match.start() - 30):match.end() + 30],
                temporal_context=temporal_context,
            )
            relations.append(relation)

    return relations


def extract_relations_with_metrics(
    text: str,
    entities: list[FinancialEntity],
) -> list[FinancialRelation]:
    """Extract relations including metric-based relations (revenue, earnings, etc.)."""
    relations = extract_relations(text, entities)

    # Add metric-based relations
    metric_entities = [e for e in entities if e.entity_type == EntityType.METRIC]
    company_entities = [e for e in entities if e.entity_type == EntityType.COMPANY]

    relation_counter = len(relations)
    for metric in metric_entities:
        for company in company_entities:
            # Check if metric and company appear close together in text
            metric_pos = text.lower().find(metric.name.lower())
            company_pos = text.lower().find(company.name.lower())
            if metric_pos >= 0 and company_pos >= 0:
                distance = abs(metric_pos - company_pos)
                if distance < 200:  # Within 200 chars
                    relation_counter += 1
                    relations.append(
                        FinancialRelation(
                            id=f"rel_{relation_counter:04d}",
                            source_id=company.id,
                            target_id=metric.id,
                            relation_type=RelationType.REPORTED_REVENUE,
                            metadata={
                                "metric_type": metric.metadata.get("metric_type", "unknown"),
                                "source_name": company.name,
                                "target_name": metric.name,
                            },
                            confidence=0.75,
                            source_text=text,
                        )
                    )

    return relations
