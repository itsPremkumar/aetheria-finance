"""Tests for SEC filing parser."""

from finance_kg.sec_parser import (
    parse_sec_filing,
    _extract_cik,
    _extract_company_name,
    _extract_form_type,
    _extract_filing_date,
    _extract_period,
)


class TestSECParser:
    """Test suite for the SEC filing parser."""

    def _get_sample_10k(self) -> str:
        """Get sample 10-K text for testing."""
        return """
UNITED STATES
SECURITIES AND EXCHANGE COMMISSION
Washington, D.C. 20544

FORM 10-K

Company name: Apple Inc.
CIK: 0000320193
Filing date: 2024-01-28

Fiscal year ended: September 30, 2024

Item 1. Business

Apple Inc. designs, manufactures, and markets smartphones, personal computers,
tablets, wearables, and accessories worldwide. The Company offers iPhone, Mac,
iPad, and wearables, home and accessories.

Item 1A. Risk Factors

The Company's business, reputation, results of operations, financial condition,
and stock price can be affected by a number of factors, whether currently known
or unknown.

Item 7. Management's Discussion and Analysis of Financial Condition

The Company's total net sales were $383.3 billion and net income was $97.0 billion
during fiscal 2024.

Item 8. Financial Statements

The Company's consolidated financial statements are included in this report.
        """

    def _get_sample_10q(self) -> str:
        """Get sample 10-Q text for testing."""
        return """
UNITED STATES
SECURITIES AND EXCHANGE COMMISSION

FORM 10-Q

Company name: Microsoft Corporation
CIK: 0000789019
Filing date: 2024-01-24

Period of report: December 31, 2023

Part I. Financial Information

Item 1. Financial Statements

Microsoft Corporation reported revenue of $62.0 billion for the quarter
ended December 31, 2023.

Item 2. Management's Discussion and Analysis

The Company's revenue increased 18% year-over-year.
        """

    def _get_sample_8k(self) -> str:
        """Get sample 8-K text for testing."""
        return """
UNITED STATES
SECURITIES AND EXCHANGE COMMISSION

FORM 8-K

Company name: Tesla Inc.
CIK: 0001318605
Filing date: 2024-01-15

Item 1.01 Entry into a Material Definitive Agreement

On January 10, 2024, Tesla Inc. entered into a new supply agreement with
Panasonic Corporation for battery cells.
        """

    def test_extract_cik(self) -> None:
        """Test CIK extraction."""
        text = "CIK: 0000320193"
        cik = _extract_cik(text)
        assert cik == "320193"

    def test_extract_company_name(self) -> None:
        """Test company name extraction."""
        text = "Company name: Apple Inc."
        name = _extract_company_name(text)
        assert name == "Apple Inc."

    def test_extract_form_type_10k(self) -> None:
        """Test form type extraction for 10-K."""
        text = "FORM 10-K"
        form_type = _extract_form_type(text)
        assert form_type == "10-K"

    def test_extract_form_type_10q(self) -> None:
        """Test form type extraction for 10-Q."""
        text = "FORM 10-Q"
        form_type = _extract_form_type(text)
        assert form_type == "10-Q"

    def test_extract_form_type_8k(self) -> None:
        """Test form type extraction for 8-K."""
        text = "FORM 8-K"
        form_type = _extract_form_type(text)
        assert form_type == "8-K"

    def test_parse_10k_filing(self) -> None:
        """Test parsing a full 10-K filing."""
        text = self._get_sample_10k()
        filing = parse_sec_filing(text)
        assert filing.form_type == "10-K"
        assert filing.company_name == "Apple Inc."
        assert filing.cik == "320193"
        assert filing.filing_date == "2024-01-28"

    def test_parse_10q_filing(self) -> None:
        """Test parsing a 10-Q filing."""
        text = self._get_sample_10q()
        filing = parse_sec_filing(text)
        assert filing.form_type == "10-Q"
        assert filing.company_name == "Microsoft Corporation"

    def test_parse_8k_filing(self) -> None:
        """Test parsing an 8-K filing."""
        text = self._get_sample_8k()
        filing = parse_sec_filing(text)
        assert filing.form_type == "8-K"
        assert filing.company_name == "Tesla Inc."

    def test_extract_period(self) -> None:
        """Test period extraction."""
        text = "Period of report: December 31, 2023"
        period = _extract_period(text)
        assert period == "December 31, 2023"

    def test_extract_filing_date(self) -> None:
        """Test filing date extraction."""
        text = "Filing date: 2024-01-28"
        date = _extract_filing_date(text)
        assert date == "2024-01-28"

    def test_section_extraction(self) -> None:
        """Test section extraction from filing."""
        text = self._get_sample_10k()
        filing = parse_sec_filing(text)
        # 10-K should have some sections
        assert isinstance(filing.items, dict)

    def test_minimal_filing(self) -> None:
        """Test parsing a minimal filing."""
        text = """
        FORM 10-K
        Company name: Test Corp.
        CIK: 0000000001
        """
        filing = parse_sec_filing(text)
        assert filing.form_type == "10-K"
        assert filing.company_name == "Test Corp."
