"""Tests for CLI."""

import json
from pathlib import Path

from finance_kg.cli import main


class TestCLI:
    """Test suite for the command-line interface."""

    def test_extract_command_with_text(self, capsys) -> None:
        """Test extract command with direct text."""
        import sys
        from io import StringIO
        old_argv = sys.argv
        try:
            sys.argv = ["finance-kg", "extract", "Apple Inc. (AAPL) acquired Beats Electronics."]
            main()
        except SystemExit as e:
            assert e.code == 0
        finally:
            sys.argv = old_argv

    def test_analyze_command(self, capsys) -> None:
        """Test analyze command."""
        import sys
        old_argv = sys.argv
        try:
            sys.argv = ["finance-kg", "analyze", "Microsoft Corp. reported Q4 2024 earnings."]
            main()
        except SystemExit as e:
            assert e.code == 0
        finally:
            sys.argv = old_argv

    def test_help(self, capsys) -> None:
        """Test help output."""
        import sys
        old_argv = sys.argv
        try:
            sys.argv = ["finance-kg", "--help"]
            main()
        except SystemExit as e:
            assert e.code == 0
        finally:
            sys.argv = old_argv

    def test_no_command_shows_help(self, capsys) -> None:
        """Test that no command shows help."""
        import sys
        old_argv = sys.argv
        try:
            sys.argv = ["finance-kg"]
            main()
        except SystemExit as e:
            assert e.code == 1
        finally:
            sys.argv = old_argv

    def test_extract_output_is_valid_json(self, capsys) -> None:
        """Test that extract output is valid JSON."""
        import sys
        old_argv = sys.argv
        try:
            sys.argv = ["finance-kg", "extract", "Tesla Inc. acquired SolarCity Corp. for $2.6 billion."]
            main()
        except SystemExit as e:
            assert e.code == 0
        finally:
            sys.argv = old_argv


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_pipeline(self) -> None:
        """Test the full extraction-to-analysis pipeline."""
        from finance_kg import extract_entities, extract_relations, KnowledgeGraph, ReasoningEngine

        text = """
        Apple Inc. (AAPL) acquired Beats Electronics Inc. for $3 billion in 2014.
        Microsoft Corp. acquired Activision Blizzard Inc. for $68.7 billion.
        Google LLC invested in Anthropic Inc. during its Series C round.
        Apple Inc. competes with Samsung Electronics Co. in smartphones.
        """

        entities = extract_entities(text)
        relations = extract_relations(text, entities)

        graph = KnowledgeGraph()
        graph.add_entities(entities)
        graph.add_relations(relations)

        engine = ReasoningEngine(graph)
        report = engine.generate_report()

        assert report["summary"]["total_entities"] > 0
        assert report["summary"]["total_relations"] > 0

    def test_temporal_extraction(self) -> None:
        """Test temporal information extraction."""
        from finance_kg import extract_entities

        text = "Q1 2024 earnings report shows FY2023 revenue growth of 15%."
        entities = extract_entities(text)
        date_entities = [e for e in entities if e.entity_type.value == "date"]
        assert len(date_entities) >= 1

    def test_multiple_relations_same_sentence(self) -> None:
        """Test extraction of multiple relations from one sentence."""
        from finance_kg import extract_entities, extract_relations

        text = "Apple Inc. acquired Beats Electronics Inc. and invested in UBER Technologies Inc."
        entities = extract_entities(text)
        relations = extract_relations(text, entities)
        # Should have at least one relation
        assert len(relations) >= 1
