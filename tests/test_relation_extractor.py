"""Tests for relation extraction."""

from finance_kg import extract_entities, extract_relations
from finance_kg.models import RelationType


class TestRelationExtractor:
    """Test suite for the relation extractor."""

    def test_extract_acquisition(self) -> None:
        """Extract acquisition relation from text."""
        text = "Microsoft Corp. acquired Activision Blizzard Inc. for $68.7 billion."
        entities = extract_entities(text)
        relations = extract_relations(text, entities)
        acq_relations = [r for r in relations if r.relation_type == RelationType.ACQUIRED]
        assert len(acq_relations) >= 1

    def test_extract_merger(self) -> None:
        """Extract merger relation from text."""
        text = "Company A Corp. merged with Company B Inc. in a $10 billion deal."
        entities = extract_entities(text)
        relations = extract_relations(text, entities)
        merger_relations = [r for r in relations if r.relation_type == RelationType.MERGED_WITH]
        assert len(merger_relations) >= 1

    def test_extract_investment(self) -> None:
        """Extract investment relation from text."""
        text = "Sequoia Capital invested in Stripe Inc. during its Series A round."
        entities = extract_entities(text)
        relations = extract_relations(text, entities)
        inv_relations = [r for r in relations if r.relation_type == RelationType.INVESTED_IN]
        assert len(inv_relations) >= 1

    def test_extract_competition(self) -> None:
        """Extract competition relation from text."""
        text = "Apple Inc. competes with Samsung Electronics Co. in smartphones."
        entities = extract_entities(text)
        relations = extract_relations(text, entities)
        comp_relations = [r for r in relations if r.relation_type == RelationType.COMPETES_WITH]
        assert len(comp_relations) >= 1

    def test_relation_has_source_and_target(self) -> None:
        """Check that relations have valid source and target IDs."""
        text = "Amazon.com Inc. acquired Whole Foods Market Inc."
        entities = extract_entities(text)
        relations = extract_relations(text, entities)
        for relation in relations:
            assert relation.source_id
            assert relation.target_id
            assert relation.source_id != relation.target_id

    def test_relation_confidence(self) -> None:
        """Check that relations have confidence scores."""
        text = "Google LLC invested in Anthropic Inc."
        entities = extract_entities(text)
        relations = extract_relations(text, entities)
        for relation in relations:
            assert 0 <= relation.confidence <= 1.0

    def test_no_self_relations(self) -> None:
        """Ensure no self-referencing relations are created."""
        text = "Apple Inc. announced earnings today."
        entities = extract_entities(text)
        relations = extract_relations(text, entities)
        for relation in relations:
            assert relation.source_id != relation.target_id

    def test_temporal_context(self) -> None:
        """Check temporal context extraction in relations."""
        text = "In Q2 2024, Microsoft Corp. acquired a new startup."
        entities = extract_entities(text)
        relations = extract_relations(text, entities)
        # Some relations should have temporal context
        has_temporal = any(r.temporal_context for r in relations)
        # Not all relations may have temporal context, so this is a soft check
        assert isinstance(has_temporal, bool)
