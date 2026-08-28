"""Tests for the canonical graph export model."""

from pathlib import Path

from depcycle.graph.graph import DependencyGraph
from depcycle.graph.node import ModuleNode, ModuleType
from depcycle.output.model import build_export


def make_node(
    name: str,
    module_type: ModuleType,
    file_path: Path | None = None,
) -> ModuleNode:
    """Create a graph node for tests."""
    return ModuleNode(
        name=name,
        file_path=file_path,
        module_type=module_type,
    )


def test_build_export_empty_graph() -> None:
    """Export an empty graph correctly."""
    graph = DependencyGraph()

    export = build_export(graph)

    assert export.project == "Project"
    assert export.nodes == []
    assert export.edges == []
    assert export.cycles == []
    assert export.summary == {
        "total_modules": 0,
        "local": 0,
        "stdlib": 0,
        "third_party": 0,
        "unknown": 0,
        "cycles_found": 0,
    }


def test_build_export_includes_sorted_nodes() -> None:
    """Export nodes in deterministic name order."""
    graph = DependencyGraph()

    z_node = make_node(
        "zeta",
        ModuleType.LOCAL,
        Path("/project/zeta.py"),
    )
    a_node = make_node(
        "alpha",
        ModuleType.LOCAL,
        Path("/project/alpha.py"),
    )

    graph.add_node(z_node)
    graph.add_node(a_node)

    export = build_export(graph)

    assert [node["id"] for node in export.nodes] == [
        "alpha",
        "zeta",
    ]


def test_build_export_uses_relative_file_path() -> None:
    """Export local file paths relative to the project root."""
    graph = DependencyGraph()
    graph._project_root = Path("/project")

    node = make_node(
        "depcycle.cli",
        ModuleType.LOCAL,
        Path("/project/src/depcycle/cli.py"),
    )

    graph.add_node(node)

    export = build_export(graph)

    assert export.nodes == [
        {
            "id": "depcycle.cli",
            "type": "local",
            "file": "src/depcycle/cli.py",
            "dependencies": 0,
        }
    ]


def test_build_export_uses_external_empty_file_path() -> None:
    """Use an empty file path for non-local nodes."""
    graph = DependencyGraph()

    node = make_node(
        "requests",
        ModuleType.THIRD_PARTY,
    )

    graph.add_node(node)

    export = build_export(graph)

    assert export.nodes == [
        {
            "id": "requests",
            "type": "third_party",
            "file": "",
            "dependencies": 0,
        }
    ]


def test_build_export_counts_node_types() -> None:
    """Calculate summary counts for every module category."""
    graph = DependencyGraph()

    nodes = [
        make_node(
            "local",
            ModuleType.LOCAL,
            Path("/project/local.py"),
        ),
        make_node(
            "json",
            ModuleType.STDLIB,
        ),
        make_node(
            "requests",
            ModuleType.THIRD_PARTY,
        ),
        make_node(
            "mystery",
            ModuleType.UNKNOWN,
        ),
    ]

    for node in nodes:
        graph.add_node(node)

    export = build_export(graph)

    assert export.summary == {
        "total_modules": 4,
        "local": 1,
        "stdlib": 1,
        "third_party": 1,
        "unknown": 1,
        "cycles_found": 0,
    }


def test_build_export_emits_sorted_edges() -> None:
    """Export dependency edges in deterministic order."""
    graph = DependencyGraph()

    source = make_node(
        "depcycle",
        ModuleType.LOCAL,
        Path("/project/__init__.py"),
    )
    first = make_node(
        "depcycle.zeta",
        ModuleType.LOCAL,
        Path("/project/zeta.py"),
    )
    second = make_node(
        "depcycle.alpha",
        ModuleType.LOCAL,
        Path("/project/alpha.py"),
    )

    source.dependencies = {
        first,
        second,
    }

    for node in (source, first, second):
        graph.add_node(node)

    export = build_export(graph)

    assert export.edges == [
        {
            "source": "depcycle",
            "target": "depcycle.alpha",
            "in_cycle": False,
        },
        {
            "source": "depcycle",
            "target": "depcycle.zeta",
            "in_cycle": False,
        },
    ]


def test_build_export_records_dependency_count() -> None:
    """Store the number of direct dependencies for each node."""
    graph = DependencyGraph()

    source = make_node(
        "source",
        ModuleType.LOCAL,
        Path("/project/source.py"),
    )
    first = make_node(
        "first",
        ModuleType.LOCAL,
        Path("/project/first.py"),
    )
    second = make_node(
        "second",
        ModuleType.LOCAL,
        Path("/project/second.py"),
    )

    source.dependencies = {
        first,
        second,
    }

    for node in (source, first, second):
        graph.add_node(node)

    export = build_export(graph)

    source_export = next(node for node in export.nodes if node["id"] == "source")

    assert source_export["dependencies"] == 2


def test_build_export_marks_cycle_edges() -> None:
    """Mark edges belonging to detected cycles."""
    graph = DependencyGraph()

    first = make_node(
        "a",
        ModuleType.LOCAL,
        Path("/project/a.py"),
    )
    second = make_node(
        "b",
        ModuleType.LOCAL,
        Path("/project/b.py"),
    )

    first.dependencies = {second}
    second.dependencies = {first}

    graph.add_node(first)
    graph.add_node(second)

    cycles = graph.find_cycles()
    export = build_export(
        graph,
        cycles=cycles,
    )

    assert len(export.cycles) == 1

    assert all(edge["in_cycle"] for edge in export.edges)


def test_build_export_cycle_contains_closed_path() -> None:
    """Represent cycles as closed node paths."""
    graph = DependencyGraph()

    first = make_node(
        "a",
        ModuleType.LOCAL,
        Path("/project/a.py"),
    )
    second = make_node(
        "b",
        ModuleType.LOCAL,
        Path("/project/b.py"),
    )
    third = make_node(
        "c",
        ModuleType.LOCAL,
        Path("/project/c.py"),
    )

    first.dependencies = {second}
    second.dependencies = {third}
    third.dependencies = {first}

    for node in (first, second, third):
        graph.add_node(node)

    export = build_export(
        graph,
        cycles=graph.find_cycles(),
    )

    assert len(export.cycles) == 1

    cycle_nodes = export.cycles[0]["nodes"]

    assert cycle_nodes[0] == cycle_nodes[-1]
    assert set(cycle_nodes[:-1]) == {
        "a",
        "b",
        "c",
    }


def test_build_export_cycle_edges_are_pairs() -> None:
    """Represent cycle edges as source-target pairs."""
    graph = DependencyGraph()

    first = make_node(
        "a",
        ModuleType.LOCAL,
        Path("/project/a.py"),
    )
    second = make_node(
        "b",
        ModuleType.LOCAL,
        Path("/project/b.py"),
    )

    first.dependencies = {second}
    second.dependencies = {first}

    graph.add_node(first)
    graph.add_node(second)

    export = build_export(
        graph,
        cycles=graph.find_cycles(),
    )

    cycle_edges = export.cycles[0]["edges"]

    assert cycle_edges == [
        ["a", "b"],
        ["b", "a"],
    ] or cycle_edges == [
        ["b", "a"],
        ["a", "b"],
    ]


def test_build_export_uses_provided_cycles() -> None:
    """Use supplied cycles rather than recalculating them."""
    graph = DependencyGraph()

    node = make_node(
        "a",
        ModuleType.LOCAL,
        Path("/project/a.py"),
    )

    graph.add_node(node)

    provided_cycles = [
        [node, node],
    ]

    export = build_export(
        graph,
        cycles=provided_cycles,
    )

    assert export.summary["cycles_found"] == 1
    assert export.cycles == [
        {
            "nodes": ["a", "a"],
            "edges": [["a", "a"]],
        }
    ]


def test_build_export_project_label() -> None:
    """Use the project root directory name as the export label."""
    graph = DependencyGraph()
    graph._project_root = Path("/Users/example/my-project")

    export = build_export(graph)

    assert export.project == "my-project"


def test_build_export_does_not_expose_project_path() -> None:
    """Keep absolute local filesystem paths out of the project label."""
    graph = DependencyGraph()
    graph._project_root = Path("/Users/example/private/project")

    export = build_export(graph)

    assert export.project == "project"
    assert "/Users/example/private/project" not in export.project


def test_build_export_summary_matches_nodes_and_edges() -> None:
    """Keep summary values consistent with exported graph data."""
    graph = DependencyGraph()

    local = make_node(
        "local",
        ModuleType.LOCAL,
        Path("/project/local.py"),
    )
    stdlib = make_node(
        "json",
        ModuleType.STDLIB,
    )
    third_party = make_node(
        "requests",
        ModuleType.THIRD_PARTY,
    )

    local.dependencies = {
        stdlib,
        third_party,
    }

    for node in (local, stdlib, third_party):
        graph.add_node(node)

    export = build_export(graph)

    assert export.summary["total_modules"] == len(export.nodes)
    assert export.summary["cycles_found"] == len(export.cycles)
    assert len(export.edges) == 2
    assert export.summary["local"] == 1
    assert export.summary["stdlib"] == 1
    assert export.summary["third_party"] == 1
    assert export.summary["unknown"] == 0
