"""Tests for Graphviz DOT output."""

from pathlib import Path

from depcycle.graph.graph import DependencyGraph
from depcycle.graph.node import ModuleNode, ModuleType
from depcycle.output.base import GraphExport
from depcycle.output.dot_writer import DotWriter
from depcycle.output.model import build_export


def make_export() -> GraphExport:
    """Build a small graph export for writer tests."""
    graph = DependencyGraph()

    source = ModuleNode(
        name="depcycle.cli",
        file_path=Path("/project/src/depcycle/cli.py"),
        module_type=ModuleType.LOCAL,
    )

    dependency = ModuleNode(
        name="pathlib",
        file_path=None,
        module_type=ModuleType.STDLIB,
    )

    source.dependencies = {dependency}

    graph._project_root = Path("/project")

    graph.add_node(source)
    graph.add_node(dependency)

    return build_export(graph)


def test_build_dot_contains_graph_declaration() -> None:
    """Create a valid DOT graph declaration."""
    export = make_export()

    text = DotWriter()._build_dot(export)

    assert text.startswith("digraph depcycle {")
    assert text.endswith("}\n")


def test_build_dot_contains_graph_direction() -> None:
    """Use left-to-right graph direction."""
    export = make_export()

    text = DotWriter()._build_dot(export)

    assert "rankdir=LR;" in text


def test_build_dot_contains_common_node_style() -> None:
    """Include shared Graphviz node styling."""
    export = make_export()

    text = DotWriter()._build_dot(export)

    assert ('node [shape=box style="filled,rounded" fontname="Helvetica"];') in text


def test_build_dot_serializes_nodes() -> None:
    """Serialize exported nodes with their type-specific colors."""
    export = make_export()

    text = DotWriter()._build_dot(export)

    assert (
        '"depcycle.cli" [fillcolor="#BBDEFB" color="#1E88E5" label="depcycle.cli"];'
    ) in text

    assert ('"pathlib" [fillcolor="#EEEEEE" color="#6D6D6D" label="pathlib"];') in text


def test_build_dot_serializes_edges() -> None:
    """Serialize dependency edges."""
    export = make_export()

    text = DotWriter()._build_dot(export)

    assert ('"depcycle.cli" -> "pathlib" [color="#444444" penwidth=1.2];') in text


def test_write_to_stdout(capsys) -> None:
    """Write DOT output to stdout."""
    export = make_export()

    DotWriter().write(export)

    captured = capsys.readouterr()

    assert captured.err == ""
    assert captured.out.startswith("digraph depcycle {")
    assert captured.out.endswith("}\n\n")


def test_write_to_file(tmp_path: Path) -> None:
    """Write DOT output to a file."""
    export = make_export()
    destination = tmp_path / "nested" / "dependencies.dot"

    DotWriter().write(
        export,
        destination,
    )

    assert destination.is_file()

    text = destination.read_text(
        encoding="utf-8",
    )

    assert text.startswith("digraph depcycle {")
    assert '"depcycle.cli" -> "pathlib"' in text


def test_write_creates_parent_directories(
    tmp_path: Path,
) -> None:
    """Create missing parent directories for DOT output."""
    export = make_export()

    destination = tmp_path / "one" / "two" / "dependencies.dot"

    DotWriter().write(
        export,
        destination,
    )

    assert destination.exists()
    assert destination.parent.is_dir()


def test_escape_handles_dot_special_characters() -> None:
    """Escape characters that are special inside DOT strings."""
    writer = DotWriter()

    assert writer._escape('hello "world"') == ('hello \\"world\\"')

    assert writer._escape("line\nbreak") == ("line\\nbreak")

    assert writer._escape("carriage\rreturn") == ("carriage\\rreturn")

    assert writer._escape("back\\slash") == ("back\\\\slash")


def test_escape_combines_multiple_escapes() -> None:
    """Escape multiple DOT-sensitive characters together."""
    writer = DotWriter()

    value = 'a\\b"c\nd\re'

    assert writer._escape(value) == ('a\\\\b\\"c\\nd\\re')


def test_node_attributes_cover_all_types() -> None:
    """Return explicit colors for every supported node type."""
    writer = DotWriter()

    assert writer._node_attributes("local") == (
        "#BBDEFB",
        "#1E88E5",
    )

    assert writer._node_attributes("third_party") == (
        "#FFE0B2",
        "#FB8C00",
    )

    assert writer._node_attributes("stdlib") == (
        "#EEEEEE",
        "#6D6D6D",
    )

    assert writer._node_attributes("unknown") == (
        "#EDE7F6",
        "#7E57C2",
    )


def test_unknown_node_type_uses_fallback_colors() -> None:
    """Use safe fallback colors for unexpected node types."""
    writer = DotWriter()

    assert writer._node_attributes("unexpected") == (
        "#F5F5F5",
        "#444444",
    )


def test_normal_edge_attributes() -> None:
    """Use normal styling for non-cycle edges."""
    writer = DotWriter()

    assert writer._edge_attributes(False) == (
        "#444444",
        "1.2",
    )


def test_cycle_edge_attributes() -> None:
    """Use stronger styling for cycle edges."""
    writer = DotWriter()

    assert writer._edge_attributes(True) == (
        "#D32F2F",
        "2.5",
    )


def test_build_dot_marks_cycle_edges() -> None:
    """Render cycle edges using the cycle styling."""
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

    text = DotWriter()._build_dot(export)

    assert '[color="#D32F2F" penwidth=2.5];' in text


def test_build_dot_marks_cycle_nodes() -> None:
    """
    Keep node type styling independent from cycle edge styling.

    DOT currently highlights cycles through edges. This test documents that
    node declarations remain valid and retain their type colors.
    """
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

    text = DotWriter()._build_dot(export)

    assert ('"a" [fillcolor="#BBDEFB" color="#1E88E5" label="a"];') in text

    assert ('"b" [fillcolor="#BBDEFB" color="#1E88E5" label="b"];') in text


def test_build_dot_ends_with_newline() -> None:
    """Terminate DOT output with a newline."""
    export = make_export()

    text = DotWriter()._build_dot(export)

    assert text.endswith("\n")
