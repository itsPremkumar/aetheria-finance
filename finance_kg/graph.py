"""
Knowledge graph for financial entities and relationships.

SQLite-backed with temporal versioning and confidence scoring.
"""

from __future__ import annotations
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .entities import Entity, EntityType
from .relations import Relation, RelationType


@dataclass
class GraphConfig:
    db_path: str = ":memory:"
    enable_wal: bool = True
    cache_size: int = 1000


class KnowledgeGraph:
    """SQLite-backed knowledge graph for financial data."""

    def __init__(self, db_path: str = ":memory:", config: Optional[GraphConfig] = None):
        self.config = config or GraphConfig(db_path=db_path)
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables."""
        cursor = self._conn.cursor()

        # Entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                type TEXT NOT NULL,
                normalized TEXT,
                confidence REAL DEFAULT 1.0,
                metadata TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)

        # Relations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                amount TEXT,
                date TEXT,
                metadata TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (source_id) REFERENCES entities(id),
                FOREIGN KEY (target_id) REFERENCES entities(id)
            )
        """)

        # Temporal snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id TEXT PRIMARY KEY,
                entity_id TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                valid_from REAL NOT NULL,
                valid_to REAL,
                FOREIGN KEY (entity_id) REFERENCES entities(id)
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_normalized ON entities(normalized)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_entity ON snapshots(entity_id)")

        self._conn.commit()

    def add_entity(self, entity: Entity):
        """Add an entity to the graph."""
        now = time.time()
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO entities (id, text, type, normalized, confidence, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entity.id,
            entity.text,
            entity.entity_type.value,
            entity.normalized,
            entity.confidence,
            json.dumps(entity.metadata),
            now,
            now,
        ))
        self._conn.commit()

    def add_entities(self, entities: list[Entity]):
        """Add multiple entities."""
        for entity in entities:
            self.add_entity(entity)

    def add_relation(self, relation: Relation):
        """Add a relation to the graph."""
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO relations (id, type, source_id, target_id, confidence, amount, date, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            relation.id,
            relation.relation_type.value,
            relation.source,
            relation.target,
            relation.confidence,
            relation.amount,
            relation.date,
            json.dumps(relation.metadata),
            time.time(),
        ))
        self._conn.commit()

    def add_relations(self, relations: list[Relation]):
        """Add multiple relations."""
        for relation in relations:
            self.add_relation(relation)

    def get_entity(self, entity_id: str) -> Optional[dict]:
        """Get an entity by ID."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_entities_by_type(self, entity_type: EntityType) -> list[dict]:
        """Get all entities of a type."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM entities WHERE type = ?", (entity_type.value,))
        return [dict(row) for row in cursor.fetchall()]

    def get_relations(self, entity_id: str) -> list[dict]:
        """Get all relations for an entity."""
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM relations WHERE source_id = ? OR target_id = ?
        """, (entity_id, entity_id))
        return [dict(row) for row in cursor.fetchall()]

    def query_relations(
        self,
        entity_id: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
    ) -> list[dict]:
        """Query relations with filters."""
        cursor = self._conn.cursor()
        query = "SELECT * FROM relations WHERE 1=1"
        params = []

        if entity_id:
            query += " AND (source_id = ? OR target_id = ?)"
            params.extend([entity_id, entity_id])

        if relation_type:
            query += " AND type = ?"
            params.append(relation_type.value)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_network(self, entity_id: str, depth: int = 2) -> dict[str, Any]:
        """Get the relationship network for an entity."""
        visited = set()
        network = {"nodes": [], "edges": []}

        def _explore(current_id: str, current_depth: int):
            if current_depth > depth or current_id in visited:
                return

            visited.add(current_id)

            # Add node
            entity = self.get_entity(current_id)
            if entity:
                network["nodes"].append(entity)

            # Add edges
            relations = self.get_relations(current_id)
            for rel in relations:
                network["edges"].append(rel)

                # Follow the other end
                next_id = rel["target_id"] if rel["source_id"] == current_id else rel["source_id"]
                _explore(next_id, current_depth + 1)

        _explore(entity_id, 0)
        return network

    def get_stats(self) -> dict[str, int]:
        """Get graph statistics."""
        cursor = self._conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM entities")
        entity_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM relations")
        relation_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT type) FROM entities")
        entity_types = cursor.fetchone()[0]

        return {
            "entities": entity_count,
            "relations": relation_count,
            "entity_types": entity_types,
        }

    def export_json(self, output_path: str):
        """Export the graph to JSON."""
        cursor = self._conn.cursor()

        cursor.execute("SELECT * FROM entities")
        entities = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM relations")
        relations = [dict(row) for row in cursor.fetchall()]

        data = {
            "entities": entities,
            "relations": relations,
            "exported_at": time.time(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def import_json(self, input_path: str):
        """Import a graph from JSON."""
        with open(input_path) as f:
            data = json.load(f)

        for entity_data in data.get("entities", []):
            entity = Entity(
                id=entity_data["id"],
                text=entity_data["text"],
                entity_type=EntityType(entity_data["type"]),
                start_pos=0,
                end_pos=0,
                confidence=entity_data.get("confidence", 1.0),
                normalized=entity_data.get("normalized"),
                metadata=json.loads(entity_data.get("metadata", "{}")),
            )
            self.add_entity(entity)

        for relation_data in data.get("relations", []):
            relation = Relation(
                id=relation_data["id"],
                relation_type=RelationType(relation_data["type"]),
                source=relation_data["source_id"],
                target=relation_data["target_id"],
                confidence=relation_data.get("confidence", 1.0),
                amount=relation_data.get("amount"),
                date=relation_data.get("date"),
                metadata=json.loads(relation_data.get("metadata", "{}")),
            )
            self.add_relation(relation)

    def close(self):
        """Close the database connection."""
        self._conn.close()
