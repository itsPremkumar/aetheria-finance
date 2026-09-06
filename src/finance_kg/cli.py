"""CLI for the Finance Knowledge Graph."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from finance_kg import (
    KnowledgeGraph,
    ReasoningEngine,
    extract_entities,
    extract_relations,
)


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="finance-kg",
        description="Financial Reasoning Knowledge Graph — extract, reason, and analyze financial relationships",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract entities and relations from text")
    extract_parser.add_argument("text", nargs="?", help="Text to analyze (or stdin if not provided)")
    extract_parser.add_argument("--file", "-f", type=Path, help="Read text from file")
    extract_parser.add_argument("--output", "-o", type=Path, help="Output file (default: stdout)")
    extract_parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    # Graph command
    graph_parser = subparsers.add_parser("graph", help="Build and query a knowledge graph")
    graph_parser.add_argument("--input", "-i", type=Path, required=True, help="Input JSON file with extracted data")
    graph_parser.add_argument("--query", "-q", help="Search query for the graph")
    graph_parser.add_argument("--company", "-c", help="Company name to analyze")
    graph_parser.add_argument("--report", action="store_true", help="Generate full report")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze financial text end-to-end")
    analyze_parser.add_argument("text", nargs="?", help="Text to analyze (or stdin if not provided)")
    analyze_parser.add_argument("--file", "-f", type=Path, help="Read text from file")
    analyze_parser.add_argument("--output", "-o", type=Path, help="Output file")
    analyze_parser.add_argument("--format", choices=["json", "text"], default="json")

    # SEC filing command
    sec_parser = subparsers.add_parser("sec", help="Parse an SEC filing")
    sec_parser.add_argument("file", type=Path, help="Path to SEC filing text file")
    sec_parser.add_argument("--output", "-o", type=Path, help="Output file")
    sec_parser.add_argument("--format", choices=["json", "text"], default="json")

    return parser


def _cmd_extract(args: argparse.Namespace) -> int:
    """Handle the extract command."""
    # Get input text
    if args.file:
        text = args.file.read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("Error: No input text provided", file=sys.stderr)
        return 1

    # Extract entities and relations
    entities = extract_entities(text)
    relations = extract_relations(text, entities)

    result = {
        "entities": [
            {
                "id": e.id,
                "name": e.name,
                "type": e.entity_type.value,
                "confidence": e.confidence,
                "metadata": e.metadata,
            }
            for e in entities
        ],
        "relations": [
            {
                "id": r.id,
                "source": r.source_id,
                "target": r.target_id,
                "relation": r.relation_type.value,
                "confidence": r.confidence,
            }
            for r in relations
        ],
    }

    output = json.dumps(result, indent=2, default=str)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)

    return 0


def _cmd_graph(args: argparse.Namespace) -> int:
    """Handle the graph command."""
    from finance_kg.sec_parser import parse_sec_filing

    if not args.input.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        return 1

    data = json.loads(args.input.read_text(encoding="utf-8"))

    # Build graph from data
    graph = KnowledgeGraph()

    # Add entities
    for e_data in data.get("entities", []):
        from finance_kg.models import EntityType, FinancialEntity
        entity = FinancialEntity(
            id=e_data["id"],
            name=e_data["name"],
            entity_type=EntityType(e_data["type"]),
            metadata=e_data.get("metadata", {}),
            confidence=e_data.get("confidence", 1.0),
        )
        graph.add_entity(entity)

    # Add relations
    for r_data in data.get("relations", []):
        from finance_kg.models import FinancialRelation, RelationType
        relation = FinancialRelation(
            id=r_data["id"],
            source_id=r_data["source"],
            target_id=r_data["target"],
            relation_type=RelationType(r_data["relation"]),
            metadata=r_data.get("metadata", {}),
            confidence=r_data.get("confidence", 1.0),
        )
        graph.add_relation(relation)

    engine = ReasoningEngine(graph)

    if args.query:
        results = graph.search(args.query)
        output = {
            "query": args.query,
            "entities": [{"id": e.id, "name": e.name, "type": e.entity_type.value} for e in results["entities"]],
            "relations": [{"id": r.id, "relation": r.relation_type.value} for r in results["relations"]],
        }
    elif args.company:
        overview = engine.get_company_overview(args.company)
        output = {"company": args.company, "found": overview["found"]}
        if overview["found"]:
            output["direct_relations"] = overview["direct_relations"]
    elif args.report:
        output = engine.generate_report()
    else:
        output = graph.summary()

    result_str = json.dumps(output, indent=2, default=str)

    if hasattr(args, 'output') and args.output:
        args.output.write_text(result_str, encoding="utf-8")
    else:
        print(result_str)

    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    """Handle the analyze command (end-to-end analysis)."""
    # Get input text
    if args.file:
        text = args.file.read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("Error: No input text provided", file=sys.stderr)
        return 1

    # Extract and build graph
    entities = extract_entities(text)
    relations = extract_relations(text, entities)

    graph = KnowledgeGraph()
    graph.add_entities(entities)
    graph.add_relations(relations)

    engine = ReasoningEngine(graph)
    report = engine.generate_report()

    result_str = json.dumps(report, indent=2, default=str)

    if args.output:
        args.output.write_text(result_str, encoding="utf-8")
    else:
        print(result_str)

    return 0


def _cmd_sec(args: argparse.Namespace) -> int:
    """Handle the SEC filing command."""
    from finance_kg.sec_parser import parse_sec_filing

    if not args.file.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    text = args.file.read_text(encoding="utf-8")
    filing = parse_sec_filing(text)

    result = {
        "cik": filing.cik,
        "company_name": filing.company_name,
        "form_type": filing.form_type,
        "filing_date": filing.filing_date,
        "period": filing.period_of_report,
        "sections_found": list(filing.items.keys()),
        "section_lengths": {k: len(v) for k, v in filing.items.items()},
    }

    result_str = json.dumps(result, indent=2, default=str)

    if args.output:
        args.output.write_text(result_str, encoding="utf-8")
    else:
        print(result_str)

    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    command_map = {
        "extract": _cmd_extract,
        "graph": _cmd_graph,
        "analyze": _cmd_analyze,
        "sec": _cmd_sec,
    }

    handler = command_map.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
