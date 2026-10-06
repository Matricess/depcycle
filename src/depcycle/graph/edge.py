"""Graph edge model representing a directed dependency relationship between nodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .node import Node


@dataclass(frozen=True)
class Edge:
    """
    Represent a directed edge (dependency relationship) from a source to a target node.

    Frozen to ensure immutability, allowing Edge instances to be stored in sets.
    """

    source: Node
    target: Node

    def __repr__(self) -> str:
        return f"Edge({self.source.name!r} -> {self.target.name!r})"
