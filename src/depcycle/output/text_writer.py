"""Text output writer for terminal formatting."""

from __future__ import annotations

import json
from pathlib import Path

from ..graph.graph import DependencyGraph
from ..graph.node import ModuleNode
from .base import GraphExport, IOutputWriter


class TextWriter(IOutputWriter):
    """Format and write analysis summary or inspection results to stdout/stderr."""

    def write(
        self,
        export: GraphExport,
        dest: Path | None = None,
    ) -> None:
        """Write summary JSON output or plain text."""
        content = json.dumps(
            {
                "project": export.project,
                "summary": export.summary,
                "cycles": export.cycles,
            },
            indent=2,
        )

        if dest is None:
            print(content)
        else:
            dest.write_text(content, encoding="utf-8")

    @staticmethod
    def format_inspection(
        graph: DependencyGraph,
        cycles: list[list[ModuleNode]],
        module_name: str,
    ) -> dict[str, object]:
        """Format single module inspection details as a dictionary/JSON object."""
        if module_name not in graph.nodes:
            return {"error": f"module not found: {module_name}"}

        node = graph.nodes[module_name]
        deps = sorted(dependency.name for dependency in node.dependencies)
        dependents = sorted(node.name for node in graph.dependents(module_name))
        touching_cycles = [
            [n.name for n in cycle]
            for cycle in cycles
            if any(n.name == module_name for n in cycle)
        ]

        return {
            "module": module_name,
            "type": node.module_type.value,
            "file": str(node.file_path) if node.file_path else None,
            "dependencies_count": len(deps),
            "dependencies": deps,
            "dependents_count": len(dependents),
            "dependents": dependents,
            "reachable_dependents_count": len(graph.reachable_dependents(module_name)),
            "cycles_count": len(touching_cycles),
            "cycles": touching_cycles,
        }

    @staticmethod
    def format_cycles(cycles: list[list[ModuleNode]]) -> dict[str, object]:
        """Format circular dependencies as a dictionary/JSON object."""
        return {
            "cycles": [[node.name for node in cycle] for cycle in cycles],
        }
