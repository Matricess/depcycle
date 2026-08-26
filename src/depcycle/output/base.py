"""Base interfaces for output writers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..graph.graph import DependencyGraph


def project_label(graph: DependencyGraph) -> str:
    """Return a portable project label without exposing the local filesystem path."""
    project_root = getattr(graph, "_project_root", None)
    return project_root.name if project_root else "Project"


def relative_file_path(graph: DependencyGraph, file_path: Path | None) -> str:
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
    def write(self, graph: DependencyGraph, dest: Path | None = None) -> None:
        """Serialize the graph to the given destination or stdout."""
        raise NotImplementedError
