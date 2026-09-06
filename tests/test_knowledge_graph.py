"""Tests for knowledge graph."""

from finance_kg import extract_entities, extract_relations, KnowledgeGraph
from finance_kg.models import EntityType, FinancialEntity, FinancialRelation, RelationType


class TestKnowledgeGraph:
    """Test suite for the knowledge graph."""

    def _build_sample_graph(self) -> KnowledgeGraph:
        """Build a sample graph for testing."""
        graph = KnowledgeGraph()

        apple = FinancialEntity(
            id="ent_001",
            name="Apple Inc.",
            entity_type=EntityType.COMPANY,
        )
        beats = FinancialEntity(
            id="ent_002",
            name="Beats Electronics Inc.",
            entity_type=EntityType.COMPANY,
        )
        acq_relation = FinancialRelation(
            id="rel_001",
            source_id="ent_001",
            target_id="ent_002",
            relation_type=RelationType.ACQUIRED,
            metadata={"source_name": "Apple Inc.", "target_name": "Beats Electronics Inc."},
        )

        graph.add_entity(apple)
        graph.add_entity(beats)
        graph.add_relation(acq_relation)

        return graph

    def test_add_entity(self) -> None:
        """Test adding entities to the graph."""
        graph = KnowledgeGraph()
        entity = FinancialEntity(
            id="ent_001",
            name="Apple Inc.",
            entity_type=EntityType.COMPANY,
        )
        graph.add_entity(entity)
        assert graph.entity_count == 1
        assert graph.get_entity("ent_001") == entity

    def test_add_relation(self) -> None:
        """Test adding relations to the graph."""
        graph = self._build_sample_graph()
        assert graph.relation_count == 1

    def test_find_by_name(self) -> None:
        """Test finding entities by name."""
        graph = self._build_sample_graph()
        results = graph.find_by_name("Apple")
        assert len(results) >= 1
        assert any(e.name == "Apple Inc." for e in results)

    def test_find_by_name_partial(self) -> None:
        """Test partial name matching."""
        graph = self._build_sample_graph()
        results = graph.find_by_name("Beat")
        assert len(results) >= 1

    def test_find_by_type(self) -> None:
        """Test finding entities by type."""
        graph = self._build_sample_graph()
        companies = graph.find_by_type(EntityType.COMPANY)
        assert len(companies) >= 2

    def test_get_relations(self) -> None:
        """Test retrieving relations."""
        graph = self._build_sample_graph()
        relations = graph.get_relations("ent_001")
        assert len(relations) >= 1

    def test_get_relations_by_type(self) -> None:
        """Test filtering relations by type."""
        graph = self._build_sample_graph()
        acq_relations = graph.get_relations("ent_001", RelationType.ACQUIRED)
        assert len(acq_relations) >= 1

    def test_get_neighbors(self) -> None:
        """Test getting neighboring entities."""
        graph = self._build_sample_graph()
        neighbors = graph.get_neighbors("ent_001")
        assert len(neighbors) >= 1
        target_entity, relation = neighbors[0]
        assert target_entity.name == "Beats Electronics Inc."

    def test_search(self) -> None:
        """Test searching the graph."""
        graph = self._build_sample_graph()
        results = graph.search("Apple")
        assert len(results["entities"]) >= 1

    def test_to_dict_and_back(self) -> None:
        """Test serialization roundtrip."""
        graph = self._build_sample_graph()
        data = graph.to_dict()
        restored = KnowledgeGraph.from_dict(data)
        assert restored.entity_count == graph.entity_count
        assert restored.relation_count == graph.relation_count

    def test_to_json_and_back(self) -> None:
        """Test JSON serialization roundtrip."""
        graph = self._build_sample_graph()
        json_str = graph.to_json()
        restored = KnowledgeGraph.from_json(json_str)
        assert restored.entity_count == graph.entity_count

    def test_merge(self) -> None:
        """Test merging two graphs."""
        graph1 = self._build_sample_graph()

        graph2 = KnowledgeGraph()
        entity = FinancialEntity(
            id="ent_003",
            name="Microsoft Corp.",
            entity_type=EntityType.COMPANY,
        )
        graph2.add_entity(entity)

        initial_count = graph1.entity_count
        graph1.merge(graph2)
        assert graph1.entity_count == initial_count + 1

    def test_summary(self) -> None:
        """Test graph summary."""
        graph = self._build_sample_graph()
        summary = graph.summary()
        assert summary["total_entities"] >= 2
        assert summary["total_relations"] >= 1
        assert "entity_types" in summary
        assert "relation_types" in summary

    def test_get_network(self) -> None:
        """Test network view around an entity."""
        graph = self._build_sample_graph()
        network = graph.get_network("ent_001", depth=2)
        assert len(network["nodes"]) >= 1
        assert len(network["edges"]) >= 1

    def test_repr(self) -> None:
        """Test string representation."""
        graph = self._build_sample_graph()
        repr_str = repr(graph)
        assert "KnowledgeGraph" in repr_str
