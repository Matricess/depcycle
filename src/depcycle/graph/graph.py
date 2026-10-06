"""Graph class representing the core graph data structure and algorithms."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

from .node import Node


def _get_stdlib_names() -> set[str]:
    """Retrieve standard library module names available on the current runtime."""
    stdlib_names = getattr(sys, "stdlib_module_names", None)
    if stdlib_names is not None:
        return set(stdlib_names)

    return {
        "os",
        "sys",
        "pathlib",
        "json",
        "ast",
        "re",
        "math",
        "collections",
        "itertools",
        "functools",
        "typing",
        "dataclasses",
        "enum",
        "logging",
    }


class Graph:
    """
    Central data structure holding the dependency graph and graph analytics.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self._project_root: Path | None = None
        self._known_stdlib: set[str] = _get_stdlib_names()
        self._known_third_party: set[str] = set()

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize package or import name by treating -, _, and . as equivalent."""
        return re.sub(r"[-_.]+", "-", name.strip().lower())

    def add_node(self, node: Node) -> None:
        """Add or update a node in the graph."""
        self.nodes[node.name] = node

    def get_node(self, name: str) -> Node | None:
        """Retrieve a node by its fully qualified name."""
        return self.nodes.get(name)

    def fan_out(self, module_name: str) -> int:
        """Return the count of direct outgoing dependencies."""
        node = self.nodes.get(module_name)
        return len(node.outgoing_edges) if node else 0

    def dependents(self, module_name: str) -> list[Node]:
        """Return all nodes that directly depend on the specified node."""
        return sorted(
            (
                node
                for node in self.nodes.values()
                if any(dep.name == module_name for dep in node.dependencies)
            ),
            key=lambda n: n.name,
        )

    def fan_in(self, module_name: str) -> int:
        """Return the count of incoming dependencies (dependents)."""
        return len(self.dependents(module_name))

    def shortest_path(self, source: str, target: str) -> list[Node] | None:
        """Return the shortest dependency chain from source to target using BFS."""
        if source not in self.nodes or target not in self.nodes:
            return None

        if source == target:
            return [self.nodes[source]]

        visited: set[str] = {source}
        queue: list[list[Node]] = [[self.nodes[source]]]

        while queue:
            path = queue.pop(0)
            current = path[-1]

            for dep in sorted(current.dependencies, key=lambda n: n.name):
                if dep.name == target:
                    return path + [dep]

                if dep.name not in visited:
                    visited.add(dep.name)
                    queue.append(path + [dep])

        return None

    def find_cycles(self) -> list[list[Node]]:
        """Detect circular dependencies using depth-first search (DFS)."""
        cycles: list[list[Node]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[Node] = []

        def dfs(node: Node) -> None:
            visited.add(node.name)
            rec_stack.add(node.name)
            path.append(node)

            for dep in sorted(node.dependencies, key=lambda d: d.name):
                if dep.name not in visited:
                    dfs(dep)
                elif dep.name in rec_stack:
                    cycle_start = next(
                        i for i, p_node in enumerate(path) if p_node.name == dep.name
                    )
                    cycles.append(path[cycle_start:] + [dep])

            rec_stack.remove(node.name)
            path.pop()

        for node in sorted(self.nodes.values(), key=lambda n: n.name):
            if node.name not in visited:
                dfs(node)

        return cycles

    def __repr__(self) -> str:
        return f"Graph(nodes={len(self.nodes)})"

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self) -> Iterator[Node]:
        return iter(self.nodes.values())
