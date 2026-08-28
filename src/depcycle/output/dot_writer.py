"""DOT output writer for Graphviz-compatible dependency graphs."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from .base import GraphExport, IOutputWriter


class DotWriter(IOutputWriter):
    """Serialize a dependency graph to Graphviz DOT syntax."""

    _FILL: ClassVar[dict[str, str]] = {
        "local": "#BBDEFB",
        "third_party": "#FFE0B2",
        "stdlib": "#EEEEEE",
        "unknown": "#EDE7F6",
    }

    _COLOR: ClassVar[dict[str, str]] = {
        "local": "#1E88E5",
        "third_party": "#FB8C00",
        "stdlib": "#6D6D6D",
        "unknown": "#7E57C2",
    }

    @staticmethod
    def _escape(value: str) -> str:
        """
        Escape a string for use inside a DOT quoted identifier or label.

        Args:
            value: String to escape.

        Returns:
            DOT-safe escaped string.
        """
        return (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\r", "\\r")
            .replace("\n", "\\n")
        )

    def _node_attributes(self, node_type: str) -> tuple[str, str]:
        """Return fill and border colors for a node type."""
        fill = self._FILL.get(node_type, "#F5F5F5")
        color = self._COLOR.get(node_type, "#444444")

        return fill, color

    @staticmethod
    def _edge_attributes(in_cycle: bool) -> tuple[str, str]:
        """Return color and pen width for an edge."""
        if in_cycle:
            return "#D32F2F", "2.5"

        return "#444444", "1.2"

    def _build_dot(self, export: GraphExport) -> str:
        """Build Graphviz DOT text from the canonical graph export."""
        lines = [
            "digraph depcycle {",
            "  rankdir=LR;",
            '  node [shape=box style="filled,rounded" fontname="Helvetica"];',
            "",
        ]

        for node in export.nodes:
            name = self._escape(node["id"])
            fill, color = self._node_attributes(node["type"])

            lines.append(
                f'  "{name}" [fillcolor="{fill}" color="{color}" label="{name}"];'
            )

        lines.append("")

        for edge in export.edges:
            source = self._escape(edge["source"])
            target = self._escape(edge["target"])

            edge_color, penwidth = self._edge_attributes(edge["in_cycle"])

            lines.append(
                f'  "{source}" -> "{target}" '
                f'[color="{edge_color}" penwidth={penwidth}];'
            )

        lines.append("}")

        return "\n".join(lines) + "\n"

    def write(
        self,
        export: GraphExport,
        dest: Path | None = None,
    ) -> None:
        """Write the DOT representation to stdout or a file."""
        text = self._build_dot(export)

        if dest is None:
            print(text)
            return

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
