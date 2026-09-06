"""Aetheria Finance KG — Financial Reasoning Knowledge Graph."""

from finance_kg.entity_extractor import extract_entities, FinancialEntity
from finance_kg.relation_extractor import extract_relations, FinancialRelation
from finance_kg.knowledge_graph import KnowledgeGraph
from finance_kg.reasoning_engine import ReasoningEngine

__version__ = "0.1.0"

__all__ = [
    "extract_entities",
    "FinancialEntity",
    "extract_relations",
    "FinancialRelation",
    "KnowledgeGraph",
    "ReasoningEngine",
]
