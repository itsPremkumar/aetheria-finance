"""Reasoning engine for financial analysis."""

from __future__ import annotations

from typing import Any, Optional

from finance_kg.knowledge_graph import KnowledgeGraph
from finance_kg.models import (
    EntityType,
    FinancialEntity,
    FinancialRelation,
    RelationType,
)


class ReasoningEngine:
    """Engine for reasoning about financial knowledge graph data.

    Provides analytical methods for financial analysis:
    - Company relationship analysis
    - Investment chain detection
    - Market concentration analysis
    - Temporal trend analysis
    - Sector analysis
    """

    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    def get_company_overview(self, company_name: str) -> dict[str, Any]:
        """Get a comprehensive overview of a company from the graph."""
        entities = self.graph.find_by_name(company_name)
        company_entities = [e for e in entities if e.entity_type == EntityType.COMPANY]

        if not company_entities:
            return {"found": False, "company": company_name}

        company = company_entities[0]
        relations = self.graph.get_relations(company.id)

        return {
            "found": True,
            "company": company,
            "direct_relations": len(relations),
            "outgoing_acquisitions": [
                r for r in self.graph.get_relations(company.id, RelationType.ACQUIRED, "outgoing")
            ],
            "incoming_investments": [
                r for r in self.graph.get_relations(company.id, RelationType.INVESTED_IN, "incoming")
            ],
            "competitors": [
                r for r in self.graph.get_relations(company.id, RelationType.COMPETES_WITH, "both")
            ],
            "partnerships": [
                r for r in self.graph.get_relations(company.id, RelationType.PARTNER_WITH, "both")
            ],
        }

    def find_acquisition_chain(
        self,
        company_name: str,
        max_depth: int = 5,
    ) -> list[dict[str, Any]]:
        """Find the chain of acquisitions starting from a company."""
        entities = self.graph.find_by_name(company_name)
        company_entities = [e for e in entities if e.entity_type == EntityType.COMPANY]

        if not company_entities:
            return []

        company = company_entities[0]
        chain: list[dict[str, Any]] = []
        visited: set[str] = set()

        def _traverse(entity_id: str, depth: int, path: list[str]) -> None:
            if depth > max_depth or entity_id in visited:
                return
            visited.add(entity_id)

            acquisitions = self.graph.get_relations(entity_id, RelationType.ACQUIRED, "outgoing")
            for acq in acquisitions:
                target = self.graph.get_entity(acq.target_id)
                if target:
                    step = {
                        "step": depth,
                        "acquirer": self.graph.get_entity(entity_id),
                        "acquired": target,
                        "relation": acq,
                        "path": path + [target.name],
                    }
                    chain.append(step)
                    _traverse(acq.target_id, depth + 1, path + [target.name])

        _traverse(company.id, 1, [company.name])
        return chain

    def analyze_investment_network(
        self,
        company_name: str,
        depth: int = 3,
    ) -> dict[str, Any]:
        """Analyze the investment network around a company."""
        entities = self.graph.find_by_name(company_name)
        company_entities = [e for e in entities if e.entity_type == EntityType.COMPANY]

        if not company_entities:
            return {"found": False}

        company = company_entities[0]
        network = self.graph.get_network(company.id, depth)

        # Analyze network statistics
        direct_investments = self.graph.get_relations(company.id, RelationType.INVESTED_IN, "outgoing")
        direct_investors = self.graph.get_relations(company.id, RelationType.INVESTED_IN, "incoming")

        return {
            "found": True,
            "company": company,
            "network": network,
            "direct_investments_count": len(direct_investments),
            "direct_investors_count": len(direct_investors),
            "network_size": len(network["nodes"]),
            "total_connections": len(network["edges"]),
        }

    def detect_market_concentration(self, sector: Optional[str] = None) -> dict[str, Any]:
        """Detect market concentration patterns in the graph.

        Analyzes which companies have the most acquisitions/investments,
        indicating potential market concentration.
        """
        company_scores: dict[str, dict[str, int]] = {}

        for entity in self.graph.entities.values():
            if entity.entity_type != EntityType.COMPANY:
                continue

            scores = {"acquisitions": 0, "investments": 0, "total": 0}
            outgoing = self.graph.get_relations(entity.id, direction="outgoing")

            for rel in outgoing:
                if rel.relation_type == RelationType.ACQUIRED:
                    scores["acquisitions"] += 1
                    scores["total"] += 1
                elif rel.relation_type == RelationType.INVESTED_IN:
                    scores["investments"] += 1
                    scores["total"] += 1

            if scores["total"] > 0:
                company_scores[entity.name] = scores

        # Sort by total activity
        sorted_scores = dict(
            sorted(company_scores.items(), key=lambda x: x[1]["total"], reverse=True)
        )

        return {
            "companies_analyzed": len(self.graph.find_by_type(EntityType.COMPANY)),
            "active_companies": len(sorted_scores),
            "top_acquirers": dict(list(sorted_scores.items())[:10]),
            "concentration_ratio": (
                sum(s["total"] for s in list(sorted_scores.values())[:5])
                / max(sum(s["total"] for s in sorted_scores.values()), 1)
            ),
        }

    def analyze_temporal_trends(self) -> dict[str, Any]:
        """Analyze temporal trends in the graph data."""
        period_activity: dict[str, dict[str, int]] = {}

        for relation in self.graph.relations.values():
            temporal = relation.temporal_context
            if not temporal:
                continue

            if temporal not in period_activity:
                period_activity[temporal] = {"acquisitions": 0, "investments": 0, "total": 0}

            if relation.relation_type == RelationType.ACQUIRED:
                period_activity[temporal]["acquisitions"] += 1
                period_activity[temporal]["total"] += 1
            elif relation.relation_type == RelationType.INVESTED_IN:
                period_activity[temporal]["investments"] += 1
                period_activity[temporal]["total"] += 1

        # Sort by period
        sorted_periods = dict(
            sorted(period_activity.items(), key=lambda x: x[0])
        )

        return {
            "periods_analyzed": len(sorted_periods),
            "activity_by_period": sorted_periods,
            "total_temporal_relations": sum(p["total"] for p in sorted_periods.values()),
        }

    def sector_analysis(self) -> dict[str, Any]:
        """Analyze sector composition of the graph."""
        sectors = self.graph.find_by_type(EntityType.SECTOR)
        sector_stats: dict[str, dict[str, Any]] = {}

        for sector in sectors:
            sector_stats[sector.name] = {
                "companies_in_sector": 0,
                "total_investments": 0,
                "total_acquisitions": 0,
            }

            # Find companies mentioned alongside this sector
            neighbors = self.graph.get_neighbors(sector.id, direction="incoming")
            for neighbor, rel in neighbors:
                if neighbor.entity_type == EntityType.COMPANY:
                    sector_stats[sector.name]["companies_in_sector"] += 1

        return {
            "sectors_found": len(sectors),
            "sector_stats": sector_stats,
        }

    def find_connected_companies(
        self,
        company_a: str,
        company_b: str,
        max_depth: int = 4,
    ) -> list[list[str]]:
        """Find paths of connection between two companies."""
        entities_a = self.graph.find_by_name(company_a)
        entities_b = self.graph.find_by_name(company_b)

        company_a_entities = [e for e in entities_a if e.entity_type == EntityType.COMPANY]
        company_b_entities = [e for e in entities_b if e.entity_type == EntityType.COMPANY]

        if not company_a_entities or not company_b_entities:
            return []

        start_id = company_a_entities[0].id
        target_id = company_b_entities[0].id

        paths: list[list[str]] = []
        visited: set[str] = set()

        def _dfs(current_id: str, path: list[str], depth: int) -> None:
            if depth > max_depth:
                return
            if current_id == target_id and len(path) > 1:
                paths.append(path[:])
                return

            visited.add(current_id)

            for relation in self.graph.get_relations(current_id, direction="outgoing"):
                if relation.target_id not in visited:
                    target = self.graph.get_entity(relation.target_id)
                    if target:
                        path.append(target.name)
                        _dfs(relation.target_id, path, depth + 1)
                        path.pop()

            for relation in self.graph.get_relations(current_id, direction="incoming"):
                if relation.source_id not in visited:
                    source = self.graph.get_entity(relation.source_id)
                    if source:
                        path.append(source.name)
                        _dfs(relation.source_id, path, depth + 1)
                        path.pop()

            visited.discard(current_id)

        _dfs(start_id, [company_a_entities[0].name], 0)
        return paths

    def generate_report(self) -> dict[str, Any]:
        """Generate a comprehensive report of the knowledge graph."""
        summary = self.graph.summary()

        report = {
            "summary": summary,
            "top_companies_by_connections": [],
            "sector_breakdown": self.sector_analysis(),
            "temporal_analysis": self.analyze_temporal_trends(),
            "market_concentration": self.detect_market_concentration(),
        }

        # Find most connected companies
        connection_counts: dict[str, int] = {}
        for entity in self.graph.entities.values():
            if entity.entity_type == EntityType.COMPANY:
                relations = self.graph.get_relations(entity.id)
                if relations:
                    connection_counts[entity.name] = len(relations)

        report["top_companies_by_connection"] = dict(
            sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        return report
