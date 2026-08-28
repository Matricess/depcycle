"""Tests for JSON graph output."""

import json
from pathlib import Path

from depcycle.graph.graph import DependencyGraph
from depcycle.graph.node import ModuleNode, ModuleType
from depcycle.output.base import GraphExport
from depcycle.output.json_writer import JsonWriter
from depcycle.output.model import build_export


def make_export() -> GraphExport:
    """Build a small graph export for writer tests."""
    graph = DependencyGraph()

    source = ModuleNode(
        name="depcycle",
        file_path=Path("/project/depcycle/__init__.py"),
        module_type=ModuleType.LOCAL,
    )

    dependency = ModuleNode(
        name="json",
        file_path=None,
        module_type=ModuleType.STDLIB,
    )

    source.dependencies = {dependency}

    graph._project_root = Path("/project")

    graph.add_node(source)
    graph.add_node(dependency)

    return build_export(graph)


def test_write_to_stdout(capsys) -> None:
    """Write valid JSON to stdout when no destination is provided."""
    export = make_export()

    JsonWriter().write(export)

    captured = capsys.readouterr()

    payload = json.loads(captured.out)

    assert payload["schema_version"] == 1
    assert payload["project"] == "project"
    assert payload["summary"]["total_modules"] == 2
    assert payload["summary"]["local"] == 1
    assert payload["summary"]["stdlib"] == 1
    assert payload["summary"]["third_party"] == 0
    assert payload["summary"]["unknown"] == 0
    assert payload["summary"]["cycles_found"] == 0


def test_write_to_file(tmp_path: Path) -> None:
    """Write valid JSON to a destination file."""
    export = make_export()
    destination = tmp_path / "nested" / "dependencies.json"

    JsonWriter().write(
        export,
        destination,
    )

    assert destination.is_file()

    payload = json.loads(
        destination.read_text(
            encoding="utf-8",
        )
    )

    assert payload["schema_version"] == 1
    assert payload["project"] == "project"


def test_json_contains_expected_top_level_fields(
    tmp_path: Path,
) -> None:
    """Include the complete canonical JSON structure."""
    export = make_export()
    destination = tmp_path / "dependencies.json"

    JsonWriter().write(
        export,
        destination,
    )

    payload = json.loads(
        destination.read_text(
            encoding="utf-8",
        )
    )

    assert set(payload) == {
        "schema_version",
        "project",
        "summary",
        "nodes",
        "edges",
        "cycles",
    }


def test_nodes_are_serialized() -> None:
    """Serialize node export data without changing its values."""
    export = make_export()

    assert export.nodes == [
        {
            "id": "depcycle",
            "type": "local",
            "file": "depcycle/__init__.py",
            "dependencies": 1,
        },
        {
            "id": "json",
            "type": "stdlib",
            "file": "",
            "dependencies": 0,
        },
    ]


def test_edges_are_serialized() -> None:
    """Serialize dependency edge data."""
    export = make_export()

    assert export.edges == [
        {
            "source": "depcycle",
            "target": "json",
            "in_cycle": False,
        }
    ]


def test_cycles_are_serialized() -> None:
    """Serialize cycle information."""
    graph = DependencyGraph()

    first = ModuleNode(
        name="a",
        file_path=Path("/project/a.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="b",
        file_path=Path("/project/b.py"),
        module_type=ModuleType.LOCAL,
    )

    first.dependencies = {second}
    second.dependencies = {first}

    graph._project_root = Path("/project")
    graph.add_node(first)
    graph.add_node(second)

    export = build_export(
        graph,
        cycles=graph.find_cycles(),
    )

    JsonWriter().write(export)

    assert len(export.cycles) == 1
    assert len(export.cycles[0]["nodes"]) == 3
    assert len(export.cycles[0]["edges"]) == 2


def test_write_creates_parent_directories(
    tmp_path: Path,
) -> None:
    """Create missing parent directories for file output."""
    export = make_export()
    destination = tmp_path / "one" / "two" / "dependencies.json"

    JsonWriter().write(
        export,
        destination,
    )

    assert destination.exists()
    assert destination.parent.is_dir()


def test_write_preserves_unicode(
    tmp_path: Path,
) -> None:
    """Preserve Unicode project and module names."""
    graph = DependencyGraph()

    node = ModuleNode(
        name="café",
        file_path=None,
        module_type=ModuleType.UNKNOWN,
    )

    graph._project_root = Path("/project")
    graph.add_node(node)

    export = build_export(graph)
    destination = tmp_path / "unicode.json"

    JsonWriter().write(
        export,
        destination,
    )

    payload = json.loads(
        destination.read_text(
            encoding="utf-8",
        )
    )

    assert payload["nodes"][0]["id"] == "café"


def test_stdout_output_has_no_extra_prefix(
    capsys,
) -> None:
    """Emit JSON itself rather than a status message."""
    export = make_export()

    JsonWriter().write(export)

    captured = capsys.readouterr()

    assert captured.out.lstrip().startswith("{")
    assert captured.err == ""
