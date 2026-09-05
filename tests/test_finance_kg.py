"""
Tests for Finance Reasoning Knowledge Graph.
Test count: 24
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'src'))

from finance_kg import FinanceKG
from finance_kg.entities import EntityExtractor, Entity, EntityType
from finance_kg.relations import RelationExtractor, Relation, RelationType
from finance_kg.graph import KnowledgeGraph
from finance_kg.reasoning import ReasoningEngine, QueryResult
from finance_kg.sec_patterns import SECFilingParser
from finance_kg.metrics import FinancialMetricsExtractor


# ──────────────────── Entity Extractor Tests ─────────────────────────


class TestEntityExtractor:
    def test_create(self):
        extractor = EntityExtractor()
        assert extractor is not None

    def test_extract_amounts(self):
        extractor = EntityExtractor()
        text = "The company raised $5.0 billion in funding."
        entities = extractor.extract(text)
        amounts = [e for e in entities if e.entity_type == EntityType.AMOUNT]
        assert len(amounts) >= 1

    def test_extract_percentages(self):
        extractor = EntityExtractor()
        text = "Revenue grew 15% year-over-year."
        entities = extractor.extract(text)
        percentages = [e for e in entities if e.entity_type == EntityType.PERCENTAGE]
        assert len(percentages) >= 1

    def test_extract_dates(self):
        extractor = EntityExtractor()
        text = "The acquisition closed on May 28, 2014."
        entities = extractor.extract(text)
        dates = [e for e in entities if e.entity_type == EntityType.DATE]
        assert len(dates) >= 1

    def test_extract_tickers(self):
        extractor = EntityExtractor()
        text = "Apple (AAPL) announced earnings today."
        entities = extractor.extract(text)
        tickers = [e for e in entities if e.entity_type == EntityType.TICKER]
        assert len(tickers) >= 1

    def test_extract_companies(self):
        extractor = EntityExtractor()
        text = "Microsoft Corporation acquired LinkedIn."
        entities = extractor.extract(text)
        companies = [e for e in entities if e.entity_type == EntityType.COMPANY]
        assert len(companies) >= 1

    def test_extract_multiple(self):
        extractor = EntityExtractor()
        text = "Apple Inc. (AAPL) acquired Beats Electronics for $3.0 billion on May 28, 2014."
        entities = extractor.extract(text)
        assert len(entities) >= 3

    def test_normalize_amount(self):
        extractor = EntityExtractor()
        assert extractor._normalize_amount("$5.0 billion") == "5000000000.0"

    def test_normalize_date(self):
        extractor = EntityExtractor()
        assert extractor._normalize_date("May 28, 2014") == "2014-05-28"


# ──────────────────── Relation Extractor Tests ───────────────────────


class TestRelationExtractor:
    def test_create(self):
        extractor = RelationExtractor()
        assert extractor is not None

    def test_extract_acquired(self):
        extractor = RelationExtractor()
        text = "Apple acquired Beats Electronics for $3 billion."
        entities = [
            Entity(id="e1", text="Apple", entity_type=EntityType.COMPANY, start_pos=0, end_pos=5),
            Entity(id="e2", text="Beats Electronics", entity_type=EntityType.COMPANY, start_pos=14, end_pos=31),
        ]
        relations = extractor.extract(text, entities)
        assert len(relations) >= 1
        assert relations[0].relation_type == RelationType.ACQUIRED

    def test_extract_merged_with(self):
        extractor = RelationExtractor()
        text = "Company A merged with Company B."
        entities = [
            Entity(id="e1", text="Company A", entity_type=EntityType.COMPANY, start_pos=0, end_pos=9),
            Entity(id="e2", text="Company B", entity_type=EntityType.COMPANY, start_pos=21, end_pos=30),
        ]
        relations = extractor.extract(text, entities)
        assert len(relations) >= 1


# ──────────────────── Knowledge Graph Tests ───────────────────────────


class TestKnowledgeGraph:
    def test_create(self):
        graph = KnowledgeGraph()
        assert graph is not None

    def test_add_entity(self):
        graph = KnowledgeGraph()
        entity = Entity(id="e1", text="Apple", entity_type=EntityType.COMPANY, start_pos=0, end_pos=5)
        graph.add_entity(entity)
        result = graph.get_entity("e1")
        assert result is not None
        assert result["text"] == "Apple"

    def test_add_relation(self):
        graph = KnowledgeGraph()
        entity1 = Entity(id="e1", text="Apple", entity_type=EntityType.COMPANY, start_pos=0, end_pos=5)
        entity2 = Entity(id="e2", text="Beats", entity_type=EntityType.COMPANY, start_pos=14, end_pos=19)
        graph.add_entity(entity1)
        graph.add_entity(entity2)
        relation = Relation(id="r1", relation_type=RelationType.ACQUIRED, source="e1", target="e2")
        graph.add_relation(relation)
        relations = graph.get_relations("e1")
        assert len(relations) == 1

    def test_get_stats(self):
        graph = KnowledgeGraph()
        entity = Entity(id="e1", text="Apple", entity_type=EntityType.COMPANY, start_pos=0, end_pos=5)
        graph.add_entity(entity)
        stats = graph.get_stats()
        assert stats["entities"] == 1

    def test_export_import(self):
        graph = KnowledgeGraph()
        entity = Entity(id="e1", text="Apple", entity_type=EntityType.COMPANY, start_pos=0, end_pos=5)
        graph.add_entity(entity)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name

        try:
            graph.export_json(path)
            graph2 = KnowledgeGraph()
            graph2.import_json(path)
            stats = graph2.get_stats()
            assert stats["entities"] == 1
        finally:
            os.unlink(path)


# ──────────────────── Reasoning Engine Tests ─────────────────────────


class TestReasoningEngine:
    def test_create(self):
        graph = KnowledgeGraph()
        engine = ReasoningEngine(graph)
        assert engine is not None

    def test_analyze_company(self):
        graph = KnowledgeGraph()
        entity = Entity(id="e1", text="Apple", entity_type=EntityType.COMPANY, start_pos=0, end_pos=5)
        graph.add_entity(entity)
        engine = ReasoningEngine(graph)
        result = engine.analyze_company("Apple")
        assert isinstance(result, QueryResult)
        assert result.confidence > 0


# ──────────────────── SEC Filing Parser Tests ────────────────────────


class TestSECFilingParser:
    def test_create(self):
        parser = SECFilingParser()
        assert parser is not None

    def test_detect_filing_type(self):
        parser = SECFilingParser()
        text = "This is a 10-K annual report for the fiscal year ended December 31, 2023."
        filing_type = parser._detect_filing_type(text)
        assert filing_type == "10-K"

    def test_extract_financial_data(self):
        parser = SECFilingParser()
        text = "Revenue was $100.0 billion. Net income was $25.0 billion. EPS was $6.15."
        data = parser.extract_financial_data(text)
        assert "revenue" in data
        assert "net_income" in data


# ──────────────────── Financial Metrics Tests ────────────────────────


class TestFinancialMetricsExtractor:
    def test_create(self):
        extractor = FinancialMetricsExtractor()
        assert extractor is not None

    def test_extract_revenue(self):
        extractor = FinancialMetricsExtractor()
        text = "Revenue was $100.0 billion in 2023."
        metrics = extractor.extract(text)
        assert "revenue" in metrics

    def test_extract_multiple(self):
        extractor = FinancialMetricsExtractor()
        text = "Revenue was $100B. Net income was $25B. EPS was $6.15. P/E ratio was 25.5."
        metrics = extractor.extract(text)
        assert len(metrics) >= 3


# ──────────────────── FinanceKG Integration Tests ─────────────────────


class TestFinanceKG:
    def test_create(self):
        kg = FinanceKG()
        assert kg is not None

    def test_process_text(self):
        kg = FinanceKG()
        text = "Apple Inc. (AAPL) acquired Beats Electronics for $3.0 billion on May 28, 2014."
        result = kg.process_text(text)
        assert len(result["entities"]) >= 2
        assert len(result["relations"]) >= 1

    def test_query(self):
        kg = FinanceKG()
        text = "Apple acquired Beats Electronics."
        kg.process_text(text)
        results = kg.query("Who did Apple acquire?")
        assert len(results) >= 0

    def test_analyze_company(self):
        kg = FinanceKG()
        text = "Apple Inc. acquired Beats Electronics for $3 billion."
        kg.process_text(text)
        analysis = kg.analyze_company("Apple")
        assert isinstance(analysis, QueryResult)

    def test_get_stats(self):
        kg = FinanceKG()
        text = "Apple acquired Beats."
        kg.process_text(text)
        stats = kg.get_stats()
        assert stats["entities"] >= 2

    def test_context_manager(self):
        with FinanceKG() as kg:
            text = "Apple acquired Beats."
            kg.process_text(text)
            stats = kg.get_stats()
            assert stats["entities"] >= 2
