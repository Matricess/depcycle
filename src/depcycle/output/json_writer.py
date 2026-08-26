"""JSON output writer for dependency graphs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..graph.graph import DependencyGraph
from ..graph.node import ModuleType
from .base import IOutputWriter


class JsonWriter(IOutputWriter):
    """Serialize a dependency graph to JSON."""

    def write(self, graph: DependencyGraph, dest: Optional[Path] = None) -> None:
        payload = self._build_payload(graph)
        text = json.dumps(payload, indent=2)

        if dest is None:
            print(text)
            return

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")

    def _build_payload(self, graph: DependencyGraph) -> dict:
        nodes = []
        for node in sorted(graph.nodes.values(), key=lambda n: n.name):
            nodes.append({
                "id": node.name,
                "type": node.module_type.value,
                "file": str(node.file_path) if node.file_path else None,
            })

        edges = []
        for node in sorted(graph.nodes.values(), key=lambda n: n.name):
            for dep in sorted(node.dependencies, key=lambda d: d.name):
                edges.append({
                    "from": node.name,
                    "to": dep.name,
                })

        cycles = []
        for cycle in graph.find_cycles():
            cycles.append([node.name for node in cycle])

        summary = {
            "total_modules": len(graph.nodes),
            "local": sum(1 for node in graph.nodes.values() if node.module_type == ModuleType.LOCAL),
            "stdlib": sum(1 for node in graph.nodes.values() if node.module_type == ModuleType.STDLIB),
            "third_party": sum(1 for node in graph.nodes.values() if node.module_type == ModuleType.THIRD_PARTY),
            "unknown": sum(1 for node in graph.nodes.values() if node.module_type == ModuleType.UNKNOWN),
            "cycles_found": len(cycles),
        }

        return {
            "project": str(graph._project_root) if getattr(graph, "_project_root", None) else None,
            "summary": summary,
            "nodes": nodes,
            "edges": edges,
            "cycles": cycles,
        }
