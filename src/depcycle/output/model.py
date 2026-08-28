"""Build the canonical graph export shared by all output writers."""

from __future__ import annotations

from itertools import pairwise

from ..graph.graph import DependencyGraph
from ..graph.node import ModuleNode
from .base import (
    CycleExport,
    EdgeExport,
    GraphExport,
    NodeExport,
    SummaryExport,
    project_label,
    relative_file_path,
)


def build_export(
    graph: DependencyGraph,
    cycles: list[list[ModuleNode]] | None = None,
) -> GraphExport:
    """
    Build the canonical export model once.

    If cycles are provided, reuse them instead of calling
    graph.find_cycles() again.
    """
    raw_cycles = graph.find_cycles() if cycles is None else cycles

    cycle_exports: list[CycleExport] = []
    cycle_edges: set[tuple[str, str]] = set()

    for cycle in raw_cycles:
        names = [node.name for node in cycle]

        if not names:
            continue

        if names[0] != names[-1]:
            names.append(names[0])

        pairs = list(pairwise(names))

        cycle_edges.update(pairs)

        cycle_exports.append(
            {
                "nodes": names,
                "edges": [list(pair) for pair in pairs],
            }
        )

    sorted_nodes = sorted(
        graph.nodes.values(),
        key=lambda node: node.name,
    )

    node_exports: list[NodeExport] = [
        {
            "id": node.name,
            "type": node.module_type.value,
            "file": relative_file_path(
                graph,
                node.file_path,
            ),
            "dependencies": len(node.dependencies),
        }
        for node in sorted_nodes
    ]

    edge_exports: list[EdgeExport] = []

    counts = {
        "local": 0,
        "stdlib": 0,
        "third_party": 0,
        "unknown": 0,
    }

    for node in sorted_nodes:
        counts[node.module_type.value] += 1

        for dependency in sorted(
            node.dependencies,
            key=lambda dep: dep.name,
        ):
            edge_exports.append(
                {
                    "source": node.name,
                    "target": dependency.name,
                    "in_cycle": (
                        node.name,
                        dependency.name,
                    )
                    in cycle_edges,
                }
            )

    summary: SummaryExport = {
        "total_modules": len(sorted_nodes),
        "local": counts["local"],
        "stdlib": counts["stdlib"],
        "third_party": counts["third_party"],
        "unknown": counts["unknown"],
        "cycles_found": len(cycle_exports),
    }

    return GraphExport(
        project=project_label(graph),
        nodes=node_exports,
        edges=edge_exports,
        cycles=cycle_exports,
        summary=summary,
    )
