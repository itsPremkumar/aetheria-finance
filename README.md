# Finance Reasoning Knowledge Graph

A 100% offline-first knowledge graph for financial entity extraction, relationship mapping, and temporal reasoning. Parses SEC filings, extracts companies/tickers/amounts/dates, and enables financial analysis through a queryable graph.

## Features

- **Entity Extraction**: Companies, tickers, monetary amounts, dates, percentages, financial metrics
- **Relation Extraction**: acquired, merged_with, invested_in, partnered_with, spun_off, filed_for_bankruptcy
- **Knowledge Graph**: SQLite-backed with temporal versioning and confidence scoring
- **Reasoning Engine**: Multi-hop queries, temporal reasoning, financial analysis
- **SEC Filing Patterns**: Pre-trained patterns for 10-K, 10-Q, 8-K, S-1 parsing
- **CLI + API**: Command-line interface and programmatic API
- **100% Offline**: No external API calls required

## Quick Start

```python
from finance_kg import FinanceKG

# Initialize
kg = FinanceKG()

# Extract entities from text
text = "Apple Inc. (AAPL) acquired Beats Electronics for $3.0 billion on May 28, 2014."
entities = kg.extract_entities(text)
# Returns: [Company("Apple Inc.", ticker="AAPL"), Company("Beats Electronics"), Amount("$3.0 billion"), Date("2014-05-28")]

# Extract relations
relations = kg.extract_relations(text, entities)
# Returns: [Relation("acquired", source="Apple Inc.", target="Beats Electronics", amount="$3.0 billion")]

# Add to graph
kg.add_entities(entities)
kg.add_relations(relations)

# Query
results = kg.query("Who did Apple acquire?")
# Returns: [Beats Electronics, ...]

# Temporal reasoning
results = kg.query("What did Apple acquire in 2014?")
# Returns: [Beats Electronics]

# Financial analysis
analysis = kg.analyze_company("AAPL")
# Returns: {acquisitions: [...], investments: [...], metrics: {...}}
```

## CLI Usage

```bash
# Extract from text
python -m finance_kg extract "Apple acquired Beats for $3B"

# Query the graph
python -m finance_kg query "Who did Apple acquire?"

# Analyze a company
python -m finance_kg analyze AAPL

# Load SEC filing
python -m finance_kg load-filing path/to/filing.txt

# Export graph
python -m finance_kg export graph.json
```

## Architecture

```
finance_kg/
├── __init__.py           # Main FinanceKG class
├── entities.py           # Entity extraction (companies, tickers, amounts, dates)
├── relations.py          # Relation extraction (acquired, merged_with, etc.)
├── graph.py              # Knowledge graph (SQLite-backed)
├── reasoning.py          # Reasoning engine (multi-hop, temporal)
├── sec_patterns.py       # SEC filing parsing patterns
├── metrics.py            # Financial metric extraction
├── cli.py                # Command-line interface
├── api.py                # Programmatic API
└── tests/                # 20+ tests
    ├── test_entities.py
    ├── test_relations.py
    ├── test_graph.py
    ├── test_reasoning.py
    ├── test_sec_patterns.py
    └── test_metrics.py
```

## License

MIT License — see LICENSE file for details.
