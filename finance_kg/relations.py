"""
Relation extraction for financial text.

Extracts relationships between financial entities:
acquired, merged_with, invested_in, partnered_with, spun_off, filed_for_bankruptcy, etc.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .entities import Entity, EntityType


class RelationType(Enum):
    ACQUIRED = "acquired"
    MERGED_WITH = "merged_with"
    INVESTED_IN = "invested_in"
    PARTNERED_WITH = "partnered_with"
    SPUN_OFF = "spun_off"
    FILED_FOR_BANKRUPTCY = "filed_for_bankruptcy"
    LAWSUIT_AGAINST = "lawsuit_against"
    APPROVED_BY = "approved_by"
    COMPETES_WITH = "competes_with"
    SUPPLIES = "supplies"
    OWNS = "owns"
    INVESTED_BY = "invested_by"


@dataclass
class Relation:
    id: str
    relation_type: RelationType
    source: str  # Entity ID
    target: str  # Entity ID
    confidence: float = 1.0
    amount: Optional[str] = None
    date: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.relation_type.value,
            "source": self.source,
            "target": self.target,
            "confidence": self.confidence,
            "amount": self.amount,
            "date": self.date,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return f"Relation({self.source} -{self.relation_type.value}-> {self.target})"


class RelationExtractor:
    """Extract financial relations from text."""

    def __init__(self):
        self._patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict:
        """Compile regex patterns for relation extraction."""
        return {
            RelationType.ACQUIRED: [
                re.compile(r'(\w+(?:\s+\w+)*)\s+acquired\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
                re.compile(r'(\w+(?:\s+\w+)*)\s+bought\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
                re.compile(r'(\w+(?:\s+\w+)*)\s+purchased\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
            ],
            RelationType.MERGED_WITH: [
                re.compile(r'(\w+(?:\s+\w+)*)\s+merged\s+with\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
                re.compile(r'merger\s+between\s+(\w+(?:\s+\w+)*)\s+and\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
            ],
            RelationType.INVESTED_IN: [
                re.compile(r'(\w+(?:\s+\w+)*)\s+invested\s+(?:in\s+)?(\w+(?:\s+\w+)*)', re.IGNORECASE),
                re.compile(r'(\w+(?:\s+\w+)*)\s+funded\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
            ],
            RelationType.PARTNERED_WITH: [
                re.compile(r'(\w+(?:\s+\w+)*)\s+partnered\s+with\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
                re.compile(r'(\w+(?:\s+\w+)*)\s+teamed\s+up\s+with\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
            ],
            RelationType.FILED_FOR_BANKRUPTCY: [
                re.compile(r'(\w+(?:\s+\w+)*)\s+filed\s+for\s+bankruptcy', re.IGNORECASE),
                re.compile(r'(\w+(?:\s+\w+)*)\s+declared\s+bankruptcy', re.IGNORECASE),
            ],
            RelationType.LAWSUIT_AGAINST: [
                re.compile(r'(\w+(?:\s+\w+)*)\s+sued\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
                re.compile(r'(\w+(?:\s+\w+)*)\s+filed\s+(?:a\s+)?lawsuit\s+against\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
            ],
        }

    def extract(self, text: str, entities: list[Entity]) -> list[Relation]:
        """Extract relations from text given entities."""
        relations = []

        for relation_type, patterns in self._patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    source_text = match.group(1)
                    target_text = match.group(2) if match.lastindex >= 2 else None

                    # Match to entities
                    source_id = self._match_entity(source_text, entities)
                    target_id = self._match_entity(target_text, entities) if target_text else None

                    if source_id:
                        relation = Relation(
                            id=f"{relation_type.value}_{match.start()}",
                            relation_type=relation_type,
                            source=source_id,
                            target=target_id or "unknown",
                            confidence=0.7,
                            metadata={"matched_text": match.group()},
                        )
                        relations.append(relation)

        return relations

    def _match_entity(self, text: str, entities: list[Entity]) -> Optional[str]:
        """Match text to an entity ID."""
        if not text:
            return None

        text_lower = text.lower().strip()

        for entity in entities:
            if (entity.text.lower() in text_lower or
                text_lower in entity.text.lower() or
                entity.normalized and entity.normalized.lower() in text_lower):
                return entity.id

        return None

    def extract_with_amounts(
        self,
        text: str,
        entities: list[Entity],
    ) -> list[Relation]:
        """Extract relations with associated amounts and dates."""
        relations = self.extract(text, entities)

        for relation in relations:
            # Find amounts near the relation
            for entity in entities:
                if entity.entity_type == EntityType.AMOUNT:
                    # Check if amount is near the relation text
                    relation.metadata["amount"] = entity.normalized or entity.text

                if entity.entity_type == EntityType.DATE:
                    relation.metadata["date"] = entity.normalized or entity.text

        return relations
