"""Tests for reasoning engine."""

from finance_kg import KnowledgeGraph, ReasoningEngine
from finance_kg.models import (
    EntityType,
    FinancialEntity,
    FinancialRelation,
    RelationType,
)


class TestReasoningEngine:
    """Test suite for the reasoning engine."""

    def _build_complex_graph(self) -> KnowledgeGraph:
        """Build a complex sample graph for testing."""
        graph = KnowledgeGraph()

        companies = [
            ("ent_001", "Apple Inc."),
            ("ent_002", "Beats Electronics Inc."),
            ("ent_003", "Microsoft Corp."),
            ("ent_004", "Activision Blizzard Inc."),
            ("ent_005", "NVIDIA Corporation"),
            ("ent_006", "ARM Holdings PLC"),
            ("ent_007", "Samsung Electronics Co."),
        ]

        for cid, name in companies:
            graph.add_entity(
                FinancialEntity(id=cid, name=name, entity_type=EntityType.COMPANY)
            )

        relations = [
            ("rel_001", "ent_001", "ent_002", RelationType.ACQUIRED),
            ("rel_002", "ent_003", "ent_004", RelationType.ACQUIRED),
            ("rel_003", "ent_005", "ent_006", RelationType.ACQUIRED),
            ("rel_004", "ent_001", "ent_007", RelationType.COMPETES_WITH),
            ("rel_005", "ent_001", "ent_003", RelationType.INVESTED_IN),
        ]

        for rid, src, tgt, rtype in relations:
            graph.add_relation(
                FinancialRelation(
                    id=rid,
                    source_id=src,
                    target_id=tgt,
                    relation_type=rtype,
                    metadata={"source_name": companies[int(src[-1]) - 1][1],
                              "target_name": companies[int(tgt[-1]) - 1][1]},
                )
            )

        return graph

    def test_get_company_overview(self) -> None:
        """Test company overview generation."""
        graph = self._build_complex_graph()
        engine = ReasoningEngine(graph)
        overview = engine.get_company_overview("Apple Inc.")
        assert overview["found"] is True
        assert overview["company"].name == "Apple Inc."

    def test_company_not_found(self) -> None:
        """Test overview for non-existent company."""
        graph = self._build_complex_graph()
        engine = ReasoningEngine(graph)
        overview = engine.get_company_overview("Nonexistent Corp.")
        assert overview["found"] is False

    def test_find_acquisition_chain(self) -> None:
        """Test acquisition chain detection."""
        graph = self._build_complex_graph()
        engine = ReasoningEngine(graph)
        chain = engine.find_acquisition_chain("Apple Inc.")
        assert len(chain) >= 1
        assert chain[0]["acquired"].name == "Beats Electronics Inc."

    def test_analyze_investment_network(self) -> None:
        """Test investment network analysis."""
        graph = self._build_complex_graph()
        engine = ReasoningEngine(graph)
        result = engine.analyze_investment_network("Apple Inc.")
        assert result["found"] is True
        assert "network" in result

    def test_detect_market_concentration(self) -> None:
        """Test market concentration analysis."""
        graph = self._build_complex_graph()
        engine = ReasoningEngine(graph)
        result = engine.detect_market_concentration()
        assert "top_acquirers" in result
        assert "concentration_ratio" in result

    def test_analyze_temporal_trends(self) -> None:
        """Test temporal trend analysis."""
        graph = self._build_complex_graph()
        engine = ReasoningEngine(graph)
        result = engine.analyze_temporal_trends()
        assert "periods_analyzed" in result
        assert "activity_by_period" in result

    def test_sector_analysis(self) -> None:
        """Test sector analysis."""
        graph = self._build_complex_graph()
        engine = ReasoningEngine(graph)
        result = engine.sector_analysis()
        assert "sectors_found" in result

    def test_find_connected_companies(self) -> None:
        """Test finding connection paths between companies."""
        graph = self._build_complex_graph()
        engine = ReasoningEngine(graph)
        paths = engine.find_connected_companies("Apple Inc.", "Beats Electronics Inc.")
        # Should find at least one path
        assert isinstance(paths, list)

    def test_generate_report(self) -> None:
        """Test comprehensive report generation."""
        graph = self._build_complex_graph()
        engine = ReasoningEngine(graph)
        report = engine.generate_report()
        assert "summary" in report
        assert "top_companies_by_connections" in report
        assert "sector_breakdown" in report
        assert "temporal_analysis" in report
        assert "market_concentration" in report

    def test_empty_graph(self) -> None:
        """Test engine with empty graph."""
        graph = KnowledgeGraph()
        engine = ReasoningEngine(graph)
        report = engine.generate_report()
        assert report["summary"]["total_entities"] == 0
