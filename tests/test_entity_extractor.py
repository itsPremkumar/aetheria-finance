"""Tests for entity extraction."""

from finance_kg import extract_entities
from finance_kg.models import EntityType, FinancialEntity


class TestEntityExtractor:
    """Test suite for the entity extractor."""

    def test_extract_company_by_suffix(self) -> None:
        """Extract a company name with common suffix."""
        text = "Apple Inc. announced record revenue today."
        entities = extract_entities(text)
        company_entities = [e for e in entities if e.entity_type == EntityType.COMPANY]
        assert len(company_entities) >= 1
        assert any("Apple" in e.name for e in company_entities)

    def test_extract_known_company(self) -> None:
        """Extract a known company from the gazetteer."""
        text = "Microsoft reported strong earnings in Q4 2024."
        entities = extract_entities(text)
        company_names = [e.name for e in entities if e.entity_type == EntityType.COMPANY]
        assert any("Microsoft" in name for name in company_names)

    def test_extract_ticker(self) -> None:
        """Extract a ticker symbol from text."""
        text = "AAPL shares rose 3% today after the announcement."
        entities = extract_entities(text)
        ticker_entities = [e for e in entities if e.entity_type == EntityType.TICKER]
        assert any(e.name == "AAPL" for e in ticker_entities)

    def test_extract_ticker_in_parens(self) -> None:
        """Extract ticker symbol from parentheses notation."""
        text = "Apple (AAPL) announced its quarterly earnings."
        entities = extract_entities(text)
        ticker_entities = [e for e in entities if e.entity_type == EntityType.TICKER]
        assert any(e.name == "AAPL" for e in ticker_entities)

    def test_extract_amount(self) -> None:
        """Extract monetary amounts from text."""
        text = "The company reported revenue of $365.8 billion for FY2023."
        entities = extract_entities(text)
        amount_entities = [e for e in entities if e.entity_type == EntityType.AMOUNT]
        assert len(amount_entities) >= 1

    def test_extract_date(self) -> None:
        """Extract date references from text."""
        text = "The filing covers the period ended 2024-01-15."
        entities = extract_entities(text)
        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        assert len(date_entities) >= 1

    def test_extract_quarter(self) -> None:
        """Extract fiscal quarter references."""
        text = "Q4 2024 earnings exceeded analyst expectations."
        entities = extract_entities(text)
        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        assert any("Q4" in e.name for e in date_entities)

    def test_extract_fiscal_year(self) -> None:
        """Extract fiscal year references."""
        text = "The company's FY2024 revenue grew 10% year-over-year."
        entities = extract_entities(text)
        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        assert any("2024" in e.name for e in date_entities)

    def test_extract_sector(self) -> None:
        """Extract sector keywords."""
        text = "The technology sector showed strong growth in Q1."
        entities = extract_entities(text)
        sector_entities = [e for e in entities if e.entity_type == EntityType.SECTOR]
        assert any(e.name == "Technology" for e in sector_entities)

    def test_extract_filing_type(self) -> None:
        """Extract SEC filing type references."""
        text = "The company filed its 10-K annual report with the SEC."
        entities = extract_entities(text)
        filing_entities = [e for e in entities if e.entity_type == EntityType.FILING]
        assert any(e.name == "10-K" for e in filing_entities)

    def test_extract_multiple_entity_types(self) -> None:
        """Extract multiple different entity types from the same text."""
        text = """
        Apple Inc. (AAPL) reported Q4 2024 revenue of $89.5 billion.
        The technology sector continues to show strong growth.
        """
        entities = extract_entities(text)
        types_found = {e.entity_type for e in entities}
        assert EntityType.COMPANY in types_found
        assert EntityType.TICKER in types_found
        assert EntityType.DATE in types_found

    def test_confidence_scores(self) -> None:
        """Check that entities have confidence scores."""
        text = "Tesla Inc. announced a $5 billion investment."
        entities = extract_entities(text)
        for entity in entities:
            assert 0 <= entity.confidence <= 1.0
