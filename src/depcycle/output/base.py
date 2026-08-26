"""Base interfaces for output writers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ..graph.graph import DependencyGraph


class IOutputWriter(ABC):
    """Write a dependency graph to a specific output format."""

    @abstractmethod
    def write(self, graph: DependencyGraph, dest: Optional[Path] = None) -> None:
        """Serialize the graph to the given destination or stdout."""
        raise NotImplementedError
