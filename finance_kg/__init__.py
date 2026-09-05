"""
Finance Reasoning Knowledge Graph

Main entry point for the finance KG system.
Provides high-level API for entity extraction, relation extraction,
knowledge graph operations, and financial reasoning.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Optional

from .entities import EntityExtractor, Entity, EntityType
from .relations import RelationExtractor, Relation, RelationType
from .graph import KnowledgeGraph, GraphConfig
from .reasoning import ReasoningEngine, QueryResult
from .sec_patterns import SECFilingParser
from .metrics import FinancialMetricsExtractor


class FinanceKG:
    """Main class for the Finance Reasoning Knowledge Graph."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        config: Optional[dict] = None,
    ):
        """Initialize the Finance KG.

        Args:
            db_path: Path to SQLite database. If None, uses in-memory.
            config: Optional configuration dict.
        """
        self.config = config or {}
        self.db_path = db_path or ":memory:"

        # Initialize components
        self.entity_extractor = EntityExtractor()
        self.relation_extractor = RelationExtractor()
        self.graph = KnowledgeGraph(db_path=self.db_path)
        self.reasoning = ReasoningEngine(self.graph)
        self.sec_parser = SECFilingParser()
        self.metrics_extractor = FinancialMetricsExtractor()

    def extract_entities(self, text: str) -> list[Entity]:
        """Extract financial entities from text."""
        return self.entity_extractor.extract(text)

    def extract_relations(
        self,
        text: str,
        entities: Optional[list[Entity]] = None,
    ) -> list[Relation]:
        """Extract relations from text."""
        if entities is None:
            entities = self.extract_entities(text)
        return self.relation_extractor.extract(text, entities)

    def add_entities(self, entities: list[Entity]):
        """Add entities to the knowledge graph."""
        self.graph.add_entities(entities)

    def add_relations(self, relations: list[Relation]):
        """Add relations to the knowledge graph."""
        self.graph.add_relations(relations)

    def process_text(self, text: str) -> dict[str, list]:
        """Process text: extract entities, relations, and add to graph."""
        entities = self.extract_entities(text)
        relations = self.extract_relations(text, entities)
        self.add_entities(entities)
        self.add_relations(relations)
        return {"entities": entities, "relations": relations}

    def query(self, query: str) -> list[QueryResult]:
        """Query the knowledge graph."""
        return self.reasoning.query(query)

    def analyze_company(self, identifier: str) -> dict[str, Any]:
        """Analyze a company by name or ticker."""
        return self.reasoning.analyze_company(identifier)

    def load_filing(self, filing_path: str) -> dict[str, list]:
        """Load and process an SEC filing."""
        filings = self.sec_parser.parse(filing_path)
        all_entities = []
        all_relations = []
        for section in filings:
            result = self.process_text(section["text"])
            all_entities.extend(result["entities"])
            all_relations.extend(result["relations"])
        return {"entities": all_entities, "relations": all_relations}

    def get_company_network(
        self,
        identifier: str,
        depth: int = 2,
    ) -> dict[str, Any]:
        """Get the relationship network for a company."""
        return self.graph.get_network(identifier, depth)

    def temporal_query(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[QueryResult]:
        """Query with temporal constraints."""
        return self.reasoning.temporal_query(query, start_date, end_date)

    def get_stats(self) -> dict[str, int]:
        """Get knowledge graph statistics."""
        return self.graph.get_stats()

    def export_graph(self, output_path: str):
        """Export the knowledge graph to JSON."""
        self.graph.export_json(output_path)

    def import_graph(self, input_path: str):
        """Import a knowledge graph from JSON."""
        self.graph.import_json(input_path)

    def close(self):
        """Close the database connection."""
        self.graph.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
