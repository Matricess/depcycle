"""Graph node models for DepCycle using modern Python data classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .edge import Edge


class NodeType(Enum):
    """Categorize a node as local, third-party, stdlib, or unknown."""

    LOCAL = "local"
    THIRD_PARTY = "third_party"
    STDLIB = "stdlib"
    UNKNOWN = "unknown"


@dataclass(eq=False)
class Node:
    """
    Represent a Python module or package node in the dependency graph.

    A node's fully qualified name serves as its unique graph identity.
    """

    name: str
    file_path: Path | None = None
    node_type: NodeType = NodeType.UNKNOWN
    raw_imports: set[str] = field(default_factory=set)
    outgoing_edges: set[Edge] = field(default_factory=set)

    @property
    def dependencies(self) -> set[Node]:
        """Convenience property returning target nodes directly from outgoing edges."""
        return {edge.target for edge in self.outgoing_edges}

    def add_dependency(self, target: Node) -> Edge:
        """Create and add an outgoing edge to a target node."""
        edge = Edge(source=self, target=target)
        self.outgoing_edges.add(edge)
        return edge

    def __eq__(self, other: object) -> bool:
        """Node name is the sole identity for graph node equality."""
        if not isinstance(other, Node):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        """Hash based uniquely on the qualified node name."""
        return hash(self.name)

    def __repr__(self) -> str:
        return (
            f"Node("
            f"name={self.name!r}, "
            f"type={self.node_type.name}, "
            f"edges={len(self.outgoing_edges)}"
            f")"
        )
