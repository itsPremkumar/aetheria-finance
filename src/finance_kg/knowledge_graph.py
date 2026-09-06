"""Knowledge graph for financial entities and relations."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Optional

from finance_kg.models import (
    EntityType,
    FinancialEntity,
    FinancialRelation,
    RelationType,
)


class KnowledgeGraph:
    """In-memory financial knowledge graph.

    Stores entities and relations extracted from financial text.
    Supports querying, traversal, and export.
    """

    def __init__(self) -> None:
        self.entities: dict[str, FinancialEntity] = {}
        self.relations: dict[str, FinancialRelation] = {}
        self._adjacency: dict[str, list[FinancialRelation]] = defaultdict(list)
        self._reverse_adjacency: dict[str, list[FinancialRelation]] = defaultdict(list)
        self._entity_name_index: dict[str, list[str]] = defaultdict(list)

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def relation_count(self) -> int:
        return len(self.relations)

    def add_entity(self, entity: FinancialEntity) -> None:
        """Add an entity to the graph."""
        self.entities[entity.id] = entity
        self._entity_name_index[entity.name.lower()].append(entity.id)

    def add_relation(self, relation: FinancialRelation) -> None:
        """Add a relation to the graph."""
        self.relations[relation.id] = relation
        self._adjacency[relation.source_id].append(relation)
        self._reverse_adjacency[relation.target_id].append(relation)

    def add_entities(self, entities: list[FinancialEntity]) -> None:
        """Add multiple entities to the graph."""
        for entity in entities:
            self.add_entity(entity)

    def add_relations(self, relations: list[FinancialRelation]) -> None:
        """Add multiple relations to the graph."""
        for relation in relations:
            self.add_relation(relation)

    def get_entity(self, entity_id: str) -> Optional[FinancialEntity]:
        """Get an entity by its ID."""
        return self.entities.get(entity_id)

    def find_by_name(self, name: str) -> list[FinancialEntity]:
        """Find entities by name (exact or partial match)."""
        results: list[FinancialEntity] = []
        name_lower = name.lower()
        for key, ids in self._entity_name_index.items():
            if name_lower in key:
                for eid in ids:
                    if eid in self.entities:
                        results.append(self.entities[eid])
        return results

    def find_by_type(self, entity_type: EntityType) -> list[FinancialEntity]:
        """Find all entities of a given type."""
        return [e for e in self.entities.values() if e.entity_type == entity_type]

    def get_relations(
        self,
        entity_id: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
        direction: str = "both",
    ) -> list[FinancialRelation]:
        """Get relations, optionally filtered by entity, type, and direction."""
        results: list[FinancialRelation] = []

        if entity_id is None:
            # Return all relations (optionally filtered by type)
            for rel in self.relations.values():
                if relation_type is None or rel.relation_type == relation_type:
                    results.append(rel)
            return results

        if direction in ("outgoing", "both"):
            for rel in self._adjacency.get(entity_id, []):
                if relation_type is None or rel.relation_type == relation_type:
                    results.append(rel)

        if direction in ("incoming", "both"):
            for rel in self._reverse_adjacency.get(entity_id, []):
                if relation_type is None or rel.relation_type == relation_type:
                    results.append(rel)

        return results

    def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None,
        direction: str = "both",
    ) -> list[tuple[FinancialEntity, FinancialRelation]]:
        """Get neighboring entities with their relations."""
        relations = self.get_relations(entity_id, relation_type, direction)
        neighbors: list[tuple[FinancialEntity, FinancialRelation]] = []

        for rel in relations:
            if direction in ("outgoing", "both") and rel.source_id == entity_id:
                target = self.entities.get(rel.target_id)
                if target:
                    neighbors.append((target, rel))
            if direction in ("incoming", "both") and rel.target_id == entity_id:
                source = self.entities.get(rel.source_id)
                if source:
                    neighbors.append((source, rel))

        return neighbors

    def get_entity_relations(self, entity_id: str) -> dict[str, list[FinancialRelation]]:
        """Get all relations for an entity, organized by direction."""
        return {
            "outgoing": self._adjacency.get(entity_id, []),
            "incoming": self._reverse_adjacency.get(entity_id, []),
        }

    def get_network(self, entity_id: str, depth: int = 1) -> dict[str, Any]:
        """Get a network view around an entity up to a given depth."""
        visited: set[str] = set()
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        def _traverse(eid: str, current_depth: int) -> None:
            if eid in visited or current_depth > depth:
                return
            visited.add(eid)

            entity = self.entities.get(eid)
            if not entity:
                return

            nodes.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.entity_type.value,
            })

            if current_depth < depth:
                for rel in self._adjacency.get(eid, []):
                    target = self.entities.get(rel.target_id)
                    if target and rel.target_id not in visited:
                        edges.append({
                            "source": rel.source_id,
                            "target": rel.target_id,
                            "relation": rel.relation_type.value,
                        })
                        _traverse(rel.target_id, current_depth + 1)

                for rel in self._reverse_adjacency.get(eid, []):
                    source = self.entities.get(rel.source_id)
                    if source and rel.source_id not in visited:
                        edges.append({
                            "source": rel.source_id,
                            "target": rel.target_id,
                            "relation": rel.relation_type.value,
                        })
                        _traverse(rel.source_id, current_depth + 1)

        _traverse(entity_id, 0)

        return {"nodes": nodes, "edges": edges}

    def search(self, query: str) -> dict[str, list[Any]]:
        """Search the graph for entities and relations matching a query."""
        query_lower = query.lower()

        # Search entities
        matching_entities = [
            e for e in self.entities.values()
            if query_lower in e.name.lower()
            or any(query_lower in a.lower() for a in e.aliases)
        ]

        # Search relations
        matching_relations = [
            r for r in self.relations.values()
            if query_lower in r.metadata.get("source_name", "").lower()
            or query_lower in r.metadata.get("target_name", "").lower()
        ]

        return {"entities": matching_entities, "relations": matching_relations}

    def merge(self, other: "KnowledgeGraph") -> None:
        """Merge another knowledge graph into this one."""
        for entity in other.entities.values():
            if entity.id not in self.entities:
                self.add_entity(entity)

        for relation in other.relations.values():
            if relation.id not in self.relations:
                self.add_relation(relation)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the knowledge graph to a dictionary."""
        return {
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.entity_type.value,
                    "aliases": e.aliases,
                    "metadata": e.metadata,
                    "confidence": e.confidence,
                }
                for e in self.entities.values()
            ],
            "relations": [
                {
                    "id": r.id,
                    "source": r.source_id,
                    "target": r.target_id,
                    "relation": r.relation_type.value,
                    "metadata": r.metadata,
                    "confidence": r.confidence,
                    "temporal_context": r.temporal_context,
                }
                for r in self.relations.values()
            ],
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the knowledge graph to JSON."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeGraph":
        """Deserialize a knowledge graph from a dictionary."""
        graph = cls()
        for e_data in data.get("entities", []):
            entity = FinancialEntity(
                id=e_data["id"],
                name=e_data["name"],
                entity_type=EntityType(e_data["type"]),
                aliases=e_data.get("aliases", []),
                metadata=e_data.get("metadata", {}),
                confidence=e_data.get("confidence", 1.0),
            )
            graph.add_entity(entity)

        for r_data in data.get("relations", []):
            relation = FinancialRelation(
                id=r_data["id"],
                source_id=r_data["source"],
                target_id=r_data["target"],
                relation_type=RelationType(r_data["relation"]),
                metadata=r_data.get("metadata", {}),
                confidence=r_data.get("confidence", 1.0),
                temporal_context=r_data.get("temporal_context"),
            )
            graph.add_relation(relation)

        return graph

    @classmethod
    def from_json(cls, json_str: str) -> "KnowledgeGraph":
        """Deserialize a knowledge graph from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def summary(self) -> dict[str, Any]:
        """Get a summary of the knowledge graph."""
        type_counts: dict[str, int] = defaultdict(int)
        relation_counts: dict[str, int] = defaultdict(int)

        for entity in self.entities.values():
            type_counts[entity.entity_type.value] += 1

        for relation in self.relations.values():
            relation_counts[relation.relation_type.value] += 1

        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "entity_types": dict(type_counts),
            "relation_types": dict(relation_counts),
        }

    def __repr__(self) -> str:
        return f"KnowledgeGraph(entities={len(self.entities)}, relations={len(self.relations)})"
