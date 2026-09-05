"""
Command-line interface for the Finance Reasoning Knowledge Graph.
"""

from __future__ import annotations
import argparse
import json
import sys
from typing import Optional

from . import FinanceKG


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Finance Reasoning Knowledge Graph CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract entities from text")
    extract_parser.add_argument("text", help="Text to extract from")
    extract_parser.add_argument("--format", choices=["json", "text"], default="text")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the knowledge graph")
    query_parser.add_argument("query", help="Query string")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a company")
    analyze_parser.add_argument("identifier", help="Company name or ticker")

    # Load filing command
    filing_parser = subparsers.add_parser("load-filing", help="Load SEC filing")
    filing_parser.add_argument("path", help="Path to filing")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export graph")
    export_parser.add_argument("output", help="Output path")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import graph")
    import_parser.add_argument("input", help="Input path")

    # Stats command
    subparsers.add_parser("stats", help="Show graph statistics")

    return parser


def main(argv: Optional[list] = None):
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    kg = FinanceKG()

    if args.command == "extract":
        entities = kg.extract_entities(args.text)
        if args.format == "json":
            print(json.dumps([e.to_dict() for e in entities], indent=2))
        else:
            for entity in entities:
                print(f"  {entity.text} ({entity.entity_type.value})")

    elif args.command == "query":
        results = kg.query(args.query)
        for result in results:
            print(f"Query: {result.query}")
            print(f"Confidence: {result.confidence}")
            for r in result.results:
                print(f"  {r}")

    elif args.command == "analyze":
        analysis = kg.analyze_company(args.identifier)
        print(json.dumps(analysis, indent=2, default=str))

    elif args.command == "load-filing":
        result = kg.load_filing(args.path)
        print(f"Extracted {len(result['entities'])} entities, {len(result['relations'])} relations")

    elif args.command == "export":
        kg.export_graph(args.output)
        print(f"Exported to {args.output}")

    elif args.command == "import":
        kg.import_graph(args.input)
        print(f"Imported from {args.input}")

    elif args.command == "stats":
        stats = kg.get_stats()
        print(json.dumps(stats, indent=2))

    else:
        parser.print_help()

    kg.close()


if __name__ == "__main__":
    main()
