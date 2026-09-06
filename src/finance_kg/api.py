"""API server for the Finance Knowledge Graph."""

from __future__ import annotations

import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from finance_kg import (
    KnowledgeGraph,
    ReasoningEngine,
    extract_entities,
    extract_relations,
)


class FinanceKGHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for the Finance KG API."""

    def __init__(self, *args: Any, knowledge_graph: Optional[KnowledgeGraph] = None, **kwargs: Any) -> None:
        self.kg = knowledge_graph or KnowledgeGraph()
        self.engine = ReasoningEngine(self.kg)
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/":
            self._send_json({"status": "ok", "service": "aetheria-finance-kg", "version": "0.1.0"})
        elif path == "/api/v1/graph/summary":
            self._send_json(self.kg.summary())
        elif path == "/api/v1/graph/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            if not query:
                self._send_json({"error": "Missing query parameter 'q'"}, status=400)
                return
            results = self.kg.search(query)
            self._send_json({
                "query": query,
                "entity_count": len(results["entities"]),
                "entities": [
                    {"id": e.id, "name": e.name, "type": e.entity_type.value}
                    for e in results["entities"]
                ],
            })
        elif path == "/api/v1/graph/report":
            report = self.engine.generate_report()
            self._send_json(report)
        elif path == "/api/v1/entities":
            entity_type = parse_qs(parsed.query).get("type", [None])[0]
            if entity_type:
                from finance_kg.models import EntityType
                entities = self.kg.find_by_type(EntityType(entity_type))
            else:
                entities = list(self.kg.entities.values())
            self._send_json({"entities": [{"id": e.id, "name": e.name, "type": e.entity_type.value} for e in entities]})
        elif path.startswith("/api/v1/entities/"):
            entity_id = path.split("/")[-1]
            entity = self.kg.get_entity(entity_id)
            if entity:
                self._send_json({
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.entity_type.value,
                    "metadata": entity.metadata,
                })
            else:
                self._send_json({"error": "Entity not found"}, status=404)
        else:
            self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        if path == "/api/v1/extract":
            try:
                data = json.loads(body)
                text = data.get("text", "")
            except json.JSONDecodeError:
                text = body

            if not text:
                self._send_json({"error": "Missing text field"}, status=400)
                return

            entities = extract_entities(text)
            relations = extract_relations(text, entities)

            # Add to graph
            self.kg.add_entities(entities)
            self.kg.add_relations(relations)

            self._send_json({
                "entities_extracted": len(entities),
                "relations_extracted": len(relations),
                "entity_ids": [e.id for e in entities],
                "relation_ids": [r.id for r in relations],
            })
        elif path == "/api/v1/graph/load":
            try:
                data = json.loads(body)
                new_graph = KnowledgeGraph.from_dict(data)
                self.kg.merge(new_graph)
                self._send_json({"status": "loaded", "entities": len(new_graph.entities), "relations": len(new_graph.relations)})
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
        elif path == "/api/v1/analyze":
            try:
                data = json.loads(body)
                text = data.get("text", "")
            except json.JSONDecodeError:
                text = body

            if not text:
                self._send_json({"error": "Missing text field"}, status=400)
                return

            entities = extract_entities(text)
            relations = extract_relations(text, entities)

            temp_graph = KnowledgeGraph()
            temp_graph.add_entities(entities)
            temp_graph.add_relations(relations)

            temp_engine = ReasoningEngine(temp_graph)
            report = temp_engine.generate_report()
            self._send_json(report)
        else:
            self._send_json({"error": "Not found"}, status=404)

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode("utf-8"))


def create_server(
    host: str = "localhost",
    port: int = 8080,
    graph: Optional[KnowledgeGraph] = None,
) -> HTTPServer:
    """Create the API server."""
    def handler(*args: Any, **kwargs: Any) -> FinanceKGHandler:
        return FinanceKGHandler(*args, knowledge_graph=graph, **kwargs)

    return HTTPServer((host, port), handler)


def run_server(host: str = "localhost", port: int = 8080) -> None:
    """Run the API server."""
    server = create_server(host=host, port=port)
    print(f"Aetheria Finance KG API running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
