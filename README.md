# Aetheria Finance KG — Financial Reasoning Knowledge Graph

**Vertical AI project for finance: extract structured data from reports, filings, and news for reasoning about market conditions.**

## Features

- **Entity Extractor**: Identifies companies, tickers, amounts, dates, sectors, and financial metrics from text
- **Relation Extractor**: Detects acquisitions, mergers, investments, competition, and partnerships
- **Knowledge Graph**: In-memory graph with adjacency indexes, search, and network traversal
- **Reasoning Engine**: Company overviews, acquisition chains, investment networks, market concentration analysis
- **SEC Filing Parser**: Pattern-based parsing of 10-K, 10-Q, 8-K, S-1 filings
- **CLI**: Command-line interface for extraction, analysis, and reporting
- **API Server**: HTTP API for remote access and integration

## Design Principles

- **100% offline-first**: No external API calls, no cloud dependencies
- **Rule-based extraction**: Regex patterns and gazetteers for reliability
- **Zero LLM required**: Runs without any language model inference
- **MIT Licensed**: Open source for enterprise use

## Installation

```bash
pip install aetheria-finance-kg
```

## Quick Start

### CLI Usage

```bash
# Extract entities and relations from text
finance-kg extract "Apple Inc. acquired Beats Electronics for $3 billion in Q2 2014."

# Analyze financial text end-to-end
finance-kg analyze "Microsoft Corp. invested in OpenAI during FY2023."

# Parse an SEC filing
finance-kg sec path/to/filing.txt

# Query a knowledge graph
finance-kg graph -i extracted_data.json --company "Apple Inc."
```

### Python API

```python
from finance_kg import extract_entities, extract_relations, KnowledgeGraph, ReasoningEngine

text = """
Microsoft Corp. announced today that it has acquired Activision Blizzard Inc.
for $68.7 billion. The acquisition, completed in Q4 2023, strengthens
Microsoft's position in the gaming sector against Sony Group Corp.
"""

# Extract entities and relations
entities = extract_entities(text)
relations = extract_relations(text, entities)

# Build knowledge graph
graph = KnowledgeGraph()
graph.add_entities(entities)
graph.add_relations(relations)

# Reason about the data
engine = ReasoningEngine(graph)
report = engine.generate_report()
print(report)
```

### HTTP API

```bash
# Start the server
python -m finance_kg.api

# Extract entities
curl -X POST http://localhost:8080/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Apple Inc. acquired Beats Electronics for $3 billion"}'

# Get graph summary
curl http://localhost:8080/api/v1/graph/summary

# Search the graph
curl "http://localhost:8080/api/v1/graph/search?q=Apple"

# Generate report
curl http://localhost:8080/api/v1/graph/report
```

## Entity Types

| Type | Description | Examples |
|------|-------------|----------|
| `company` | Business entities | Apple Inc., Microsoft Corp. |
| `ticker` | Stock ticker symbols | AAPL, MSFT |
| `amount` | Monetary values | $3 billion, 68.7B |
| `date` | Temporal references | Q2 2014, FY2023 |
| `person` | Named individuals | Tim Cook |
| `sector` | Industry sectors | Technology, Healthcare |
| `metric` | Financial metrics | Revenue, EBITDA |

## Relation Types

| Type | Description | Example |
|------|-------------|---------|
| `acquired` | Company acquisition | Apple acquired Beats |
| `merged_with` | Merger activity | Company A merged with Company B |
| `invested_in` | Investment/funding | VC firm invested in startup |
| `competes_with` | Market competition | Apple competes with Microsoft |
| `subsidiary_of` | Parent-subsidiary | Beats is subsidiary of Apple |
| `partner_with` | Strategic partnership | Company A partners with Company B |

## SEC Filing Support

The SEC filing parser handles common form types:
- **10-K**: Annual reports with business overview, risk factors, financials
- **10-Q**: Quarterly reports with updated financials
- **8-K**: Current reports for material events
- **S-1**: Registration statements for IPOs
- **13F**: Institutional investment manager holdings
- **DEF 14A**: Proxy statements

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=finance_kg --cov-report=term-missing

# Lint
ruff check src/ tests/
```

## Project Structure

```
src/finance_kg/
├── __init__.py          # Package exports
├── models.py            # Data models (entities, relations, metrics)
├── entity_extractor.py  # Rule-based entity extraction
├── relation_extractor.py # Rule-based relation extraction
├── knowledge_graph.py   # In-memory knowledge graph
├── reasoning_engine.py  # Financial analysis engine
├── sec_parser.py        # SEC filing parser
├── cli.py               # Command-line interface
└── api.py               # HTTP API server

tests/                   # Test suite (20+ tests)
```

## License

MIT License — see LICENSE file for details.
