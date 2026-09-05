"""
Reasoning engine for financial knowledge graph.

Supports multi-hop queries, temporal reasoning, and financial analysis.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .entities import EntityType
from .graph import KnowledgeGraph
from .relations import RelationType


@dataclass
class QueryResult:
    query: str
    results: list[dict]
    confidence: float
    reasoning_path: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "results": self.results,
            "confidence": self.confidence,
            "reasoning_path": self.reasoning_path,
        }


class ReasoningEngine:
    """Query and reason over the financial knowledge graph."""

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def query(self, query: str) -> list[QueryResult]:
        """Query the knowledge graph."""
        query_lower = query.lower().strip()

        # Parse query type
        if "who" in query_lower and "acquire" in query_lower:
            return self._query_acquisitions(query)
        elif "who" in query_lower and "merge" in query_lower:
            return self._query_mergers(query)
        elif "who" in query_lower and "invest" in query_lower:
            return self._query_investments(query)
        elif "what" in query_lower and "acquire" in query_lower:
            return self._query_acquired_by(query)
        elif "analyze" in query_lower:
            return [self.analyze_company(query)]
        elif "network" in query_lower:
            return [self._query_network(query)]
        else:
            return self._query_general(query)

    def analyze_company(self, identifier: str) -> QueryResult:
        """Analyze a company by name or ticker."""
        # Find the company entity
        cursor = self.graph._conn.cursor()
        cursor.execute("""
            SELECT * FROM entities
            WHERE LOWER(text) LIKE LOWER(?) OR LOWER(normalized) LIKE LOWER(?)
        """, (f"%{identifier}%", f"%{identifier}%"))
        company_rows = cursor.fetchall()

        if not company_rows:
            return QueryResult(query=f"analyze {identifier}", results=[], confidence=0.0)

        company = dict(company_rows[0])

        # Get all relations involving this company
        relations = self.graph.get_relations(company["id"])

        # Categorize relations
        acquisitions = []
        mergers = []
        investments = []

        for rel in relations:
            if rel["type"] == RelationType.ACQUIRED.value:
                acquisitions.append(rel)
            elif rel["type"] == RelationType.MERGED_WITH.value:
                mergers.append(rel)
            elif rel["type"] == RelationType.INVESTED_IN.value:
                investments.append(rel)

        result = {
            "company": company,
            "acquisitions": acquisitions,
            "mergers": mergers,
            "investments": investments,
            "total_relations": len(relations),
        }

        return QueryResult(
            query=f"analyze {identifier}",
            results=[result],
            confidence=0.85,
            reasoning_path=["found_entity", "categorized_relations"],
        )

    def temporal_query(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[QueryResult]:
        """Query with temporal constraints."""
        results = self.query(query)
        filtered = []

        for result in results:
            filtered_results = []
            for item in result.results:
                # Check date in metadata
                date = item.get("date") or (item.get("metadata", {}) or {}).get("date")
                if date:
                    if start_date and date < start_date:
                        continue
                    if end_date and date > end_date:
                        continue
                filtered_results.append(item)

            if filtered_results:
                filtered.append(QueryResult(
                    query=result.query,
                    results=filtered_results,
                    confidence=result.confidence,
                    reasoning_path=result.reasoning_path + ["temporal_filter"],
                ))

        return filtered

    def _query_acquisitions(self, query: str) -> list[QueryResult]:
        """Query: Who acquired X?"""
        match = re.search(r'who\s+acquired\s+(\w+(?:\s+\w+)*)', query, re.IGNORECASE)
        if not match:
            return []

        target = match.group(1)
        cursor = self.graph._conn.cursor()
        cursor.execute("""
            SELECT e.* FROM entities e
            JOIN relations r ON r.source_id = e.id
            WHERE r.type = ? AND LOWER(e.text) LIKE LOWER(?)
        """, (RelationType.ACQUIRED.value, f"%{target}%"))

        results = [dict(row) for row in cursor.fetchall()]
        return [QueryResult(query=query, results=results, confidence=0.8)]

    def _query_mergers(self, query: str) -> list[QueryResult]:
        """Query: Who merged with X?"""
        match = re.search(r'who\s+merged\s+with\s+(\w+(?:\s+\w+)*)', query, re.IGNORECASE)
        if not match:
            return []

        target = match.group(1)
        cursor = self.graph._conn.cursor()
        cursor.execute("""
            SELECT e.* FROM entities e
            JOIN relations r ON r.source_id = e.id
            WHERE r.type = ? AND LOWER(e.text) LIKE LOWER(?)
        """, (RelationType.MERGED_WITH.value, f"%{target}%"))

        results = [dict(row) for row in cursor.fetchall()]
        return [QueryResult(query=query, results=results, confidence=0.8)]

    def _query_investments(self, query: str) -> list[QueryResult]:
        """Query: Who invested in X?"""
        match = re.search(r'who\s+invested\s+(?:in\s+)?(\w+(?:\s+\w+)*)', query, re.IGNORECASE)
        if not match:
            return []

        target = match.group(1)
        cursor = self.graph._conn.cursor()
        cursor.execute("""
            SELECT e.* FROM entities e
            JOIN relations r ON r.source_id = e.id
            WHERE r.type = ? AND LOWER(e.text) LIKE LOWER(?)
        """, (RelationType.INVESTED_IN.value, f"%{target}%"))

        results = [dict(row) for row in cursor.fetchall()]
        return [QueryResult(query=query, results=results, confidence=0.8)]

    def _query_acquired_by(self, query: str) -> list[QueryResult]:
        """Query: What did X acquire?"""
        match = re.search(r'what\s+did\s+(\w+(?:\s+\w+)*)\s+acquire', query, re.IGNORECASE)
        if not match:
            return []

        source = match.group(1)
        cursor = self.graph._conn.cursor()
        cursor.execute("""
            SELECT e.* FROM entities e
            JOIN relations r ON r.target_id = e.id
            WHERE r.type = ? AND LOWER(e.text) LIKE LOWER(?)
        """, (RelationType.ACQUIRED.value, f"%{source}%"))

        results = [dict(row) for row in cursor.fetchall()]
        return [QueryResult(query=query, results=results, confidence=0.8)]

    def _query_network(self, query: str) -> QueryResult:
        """Query: Show network for X"""
        match = re.search(r'network\s+(?:for\s+)?(\w+(?:\s+\w+)*)', query, re.IGNORECASE)
        if not match:
            return QueryResult(query=query, results=[], confidence=0.0)

        identifier = match.group(1)
        cursor = self.graph._conn.cursor()
        cursor.execute("""
            SELECT id FROM entities WHERE LOWER(text) LIKE LOWER(?)
        """, (f"%{identifier}%",))

        row = cursor.fetchone()
        if not row:
            return QueryResult(query=query, results=[], confidence=0.0)

        network = self.graph.get_network(row["id"], depth=2)
        return QueryResult(
            query=query,
            results=[network],
            confidence=0.85,
            reasoning_path=["found_entity", "traversed_network"],
        )

    def _query_general(self, query: str) -> list[QueryResult]:
        """General query — search across all entities."""
        cursor = self.graph._conn.cursor()
        cursor.execute("""
            SELECT * FROM entities WHERE LOWER(text) LIKE LOWER(?)
        """, (f"%{query}%",))

        results = [dict(row) for row in cursor.fetchall()]
        return [QueryResult(query=query, results=results, confidence=0.6)]
