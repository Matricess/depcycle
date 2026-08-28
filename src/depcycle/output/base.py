"""Base interfaces and shared helpers for output writers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from ..graph.graph import DependencyGraph


class NodeExport(TypedDict):
    """Serialized representation of a graph node."""

    id: str
    type: str
    file: str
    dependencies: int


class EdgeExport(TypedDict):
    """Serialized representation of a graph edge."""

    source: str
    target: str
    in_cycle: bool


class CycleExport(TypedDict):
    """Serialized representation of a dependency cycle."""

    nodes: list[str]
    edges: list[list[str]]


class SummaryExport(TypedDict):
    """Serialized summary statistics for a dependency graph."""

    total_modules: int
    local: int
    stdlib: int
    third_party: int
    unknown: int
    cycles_found: int


@dataclass(frozen=True)
class GraphExport:
    """Format-agnostic representation of a dependency graph."""

    project: str
    nodes: list[NodeExport]
    edges: list[EdgeExport]
    cycles: list[CycleExport]
    summary: SummaryExport


def project_label(graph: DependencyGraph) -> str:
    """Return a portable project label without exposing the local filesystem path."""
    project_root = getattr(graph, "_project_root", None)

    return project_root.name if project_root else "Project"


def relative_file_path(
    graph: DependencyGraph,
    file_path: Path | None,
) -> str:
    """Return a node file path relative to the analyzed project root."""
    if file_path is None:
        return ""

    project_root = getattr(graph, "_project_root", None)

    if project_root is None:
        return file_path.name

    try:
        return file_path.relative_to(project_root).as_posix()
    except ValueError:
        return file_path.name


class IOutputWriter(ABC):
    """Write a dependency graph to a specific output format."""

    @abstractmethod
    def write(
        self,
        export: GraphExport,
        dest: Path | None = None,
    ) -> None:
        """Serialize the prepared graph export."""
        raise NotImplementedError
