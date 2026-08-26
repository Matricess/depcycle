"""DOT output writer for Graphviz-compatible dependency graphs."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..graph.graph import DependencyGraph
from ..graph.node import ModuleType
from .base import IOutputWriter


class DotWriter(IOutputWriter):
    """Serialize a dependency graph to Graphviz DOT syntax."""

    def write(self, graph: DependencyGraph, dest: Optional[Path] = None) -> None:
        text = self._build_dot(graph)

        if dest is None:
            print(text)
            return

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")

    def _build_dot(self, graph: DependencyGraph) -> str:
        lines = [
            "digraph depcycle {",
            "  rankdir=LR;",
            '  node [shape=box style="filled,rounded" fontname="Helvetica"];',
            "",
        ]

        cycle_names = set()
        for cycle in graph.find_cycles():
            for node in cycle:
                cycle_names.add(node.name)

        for node in sorted(graph.nodes.values(), key=lambda n: n.name):
            label = node.name
            escaped = label.replace('"', '\\"')
            color = self._color_for(node.module_type)
            fill = self._fill_for(node.module_type)
            lines.append(f'  "{escaped}" [fillcolor="{fill}" color="{color}" label="{escaped}"];')

        lines.append("")
        for node in sorted(graph.nodes.values(), key=lambda n: n.name):
            for dep in sorted(node.dependencies, key=lambda d: d.name):
                edge_color = "#D32F2F" if node.name in cycle_names or dep.name in cycle_names else "#444444"
                penwidth = "2.5" if edge_color == "#D32F2F" else "1.2"
                lines.append(f'  "{node.name}" -> "{dep.name}" [color="{edge_color}" penwidth={penwidth}];')

        lines.append("}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _color_for(module_type: ModuleType) -> str:
        mapping = {
            ModuleType.LOCAL: "#1E88E5",
            ModuleType.THIRD_PARTY: "#FB8C00",
            ModuleType.STDLIB: "#6D6D6D",
            ModuleType.UNKNOWN: "#7E57C2",
        }
        return mapping.get(module_type, "#444444")

    @staticmethod
    def _fill_for(module_type: ModuleType) -> str:
        mapping = {
            ModuleType.LOCAL: "#BBDEFB",
            ModuleType.THIRD_PARTY: "#FFE0B2",
            ModuleType.STDLIB: "#EEEEEE",
            ModuleType.UNKNOWN: "#EDE7F6",
        }
        return mapping.get(module_type, "#F5F5F5")
