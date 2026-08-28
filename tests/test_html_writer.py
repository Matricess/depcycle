"""Tests for interactive HTML graph output."""

from pathlib import Path

from depcycle.graph.graph import DependencyGraph
from depcycle.graph.node import ModuleNode, ModuleType
from depcycle.output.base import GraphExport
from depcycle.output.html_writer import HtmlWriter
from depcycle.output.model import build_export


def make_export() -> GraphExport:
    """Build a small graph export for HTML writer tests."""
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


def make_cycle_export() -> GraphExport:
    """Build a graph export containing a dependency cycle."""
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

    return build_export(
        graph,
        cycles=graph.find_cycles(),
    )


def test_template_contains_html_document() -> None:
    """Return a complete HTML document template."""
    html = HtmlWriter._template()

    assert "<!DOCTYPE html>" in html
    assert '<html lang="en">' in html
    assert "</html>" in html


def test_template_contains_asset_placeholders() -> None:
    """Reserve placeholders for bundled JavaScript assets."""
    html = HtmlWriter._template()

    assert "__D3_SOURCE__" in html
    assert "__ELK_SOURCE__" in html


def test_template_contains_data_placeholders() -> None:
    """Reserve placeholders for graph export data."""
    html = HtmlWriter._template()

    assert "__NODE_JSON__" in html
    assert "__EDGE_JSON__" in html
    assert "__CYCLE_JSON__" in html
    assert "__SUMMARY_JSON__" in html
    assert "__PROJECT_JSON__" in html


def test_template_contains_graph_controls() -> None:
    """Include the expected interactive graph controls."""
    html = HtmlWriter._template()

    assert 'id="zoom-in"' in html
    assert 'id="zoom-out"' in html
    assert 'id="zoom-fit"' in html
    assert 'id="panel-toggle"' in html
    assert 'id="graph"' in html


def test_template_contains_node_type_styles() -> None:
    """Include styles for every supported node type."""
    html = HtmlWriter._template()

    assert ".node.local" in html
    assert ".node.third_party" in html
    assert ".node.stdlib" in html
    assert ".node.unknown" in html


def test_template_contains_cycle_styles() -> None:
    """Include styles for cycle nodes and edges."""
    html = HtmlWriter._template()

    assert ".node.cycle" in html
    assert ".edge.cycle" in html


def test_read_asset_loads_d3() -> None:
    """Load the bundled D3 JavaScript asset."""
    source = HtmlWriter._read_asset(
        HtmlWriter._D3_ASSET,
    )

    assert source
    assert "d3" in source.lower()


def test_read_asset_loads_elk() -> None:
    """Load the bundled ELK JavaScript asset."""
    source = HtmlWriter._read_asset(
        HtmlWriter._ELK_ASSET,
    )

    assert source
    assert "ELK" in source


def test_load_javascript_assets_returns_both_assets() -> None:
    """Load both bundled JavaScript libraries."""
    d3_source, elk_source = HtmlWriter._load_javascript_assets()

    assert d3_source
    assert elk_source


def test_read_missing_asset_raises_runtime_error() -> None:
    """Raise a clear error when a required asset is missing."""
    try:
        HtmlWriter._read_asset(
            "assets/does-not-exist.js",
        )
    except RuntimeError as exc:
        assert str(exc) == ("Required HTML asset is missing: assets/does-not-exist.js")
    else:
        raise AssertionError("Expected RuntimeError for missing HTML asset")


def test_json_for_script_serializes_json() -> None:
    """Serialize a value into JavaScript-compatible JSON."""
    text = HtmlWriter._json_for_script(
        {
            "name": "depcycle",
            "count": 2,
        }
    )

    assert text == ('{"name": "depcycle", "count": 2}')


def test_json_for_script_escapes_html_sensitive_characters() -> None:
    """Escape characters that could break an HTML script block."""
    text = HtmlWriter._json_for_script(
        {
            "value": "<script>&",
        }
    )

    assert "\\u003cscript\\u003e\\u0026" in text


def test_json_for_script_escapes_line_separators() -> None:
    """Escape JavaScript line and paragraph separators."""
    text = HtmlWriter._json_for_script(
        {
            "value": "\u2028\u2029",
        }
    )

    assert "\\u2028" in text
    assert "\\u2029" in text


def test_render_html_embeds_d3_source() -> None:
    """Embed the bundled D3 source into the generated document."""
    export = make_export()

    html = HtmlWriter()._render_html(export)

    assert "__D3_SOURCE__" not in html
    assert "d3" in html.lower()


def test_render_html_embeds_elk_source() -> None:
    """Embed the bundled ELK source into the generated document."""
    export = make_export()

    html = HtmlWriter()._render_html(export)

    assert "__ELK_SOURCE__" not in html
    assert "ELK" in html


def test_render_html_embeds_graph_data() -> None:
    """Embed graph export data into the generated document."""
    export = make_export()

    html = HtmlWriter()._render_html(export)

    assert "__NODE_JSON__" not in html
    assert "__EDGE_JSON__" not in html
    assert "__CYCLE_JSON__" not in html
    assert "__SUMMARY_JSON__" not in html
    assert "__PROJECT_JSON__" not in html

    assert '"depcycle.cli"' in html
    assert '"pathlib"' in html
    assert '"project"' in html


def test_render_html_contains_expected_runtime_code() -> None:
    """Include the JavaScript needed to render and interact with the graph."""
    export = make_export()

    html = HtmlWriter()._render_html(export)

    assert "new ELK()" in html
    assert "d3.zoom()" in html
    assert "elk.layout" in html
    assert "fitGraph" in html
    assert "panel-toggle" in html


def test_render_html_contains_cycle_data() -> None:
    """Embed cycle information into the generated document."""
    export = make_cycle_export()

    html = HtmlWriter()._render_html(export)

    assert '"a"' in html
    assert '"b"' in html
    assert '"in_cycle": true' in html


def test_render_html_contains_cycle_edge_support() -> None:
    """Include the runtime logic for cycle edge styling."""
    export = make_cycle_export()

    html = HtmlWriter()._render_html(export)

    assert "edge.in_cycle" in html
    assert ".edge.cycle" in html


def test_render_html_produces_complete_document() -> None:
    """Generate a complete self-contained HTML document."""
    export = make_export()

    html = HtmlWriter()._render_html(export)

    assert html.startswith("<!DOCTYPE html>")
    assert "<head>" in html
    assert "<body>" in html
    assert "</body>" in html
    assert html.endswith("</html>\n")


def test_write_to_stdout(capsys) -> None:
    """Write generated HTML to stdout."""
    export = make_export()

    HtmlWriter().write(export)

    captured = capsys.readouterr()

    assert captured.err == ""
    assert captured.out.startswith("<!DOCTYPE html>")
    assert "</html>" in captured.out


def test_write_to_file(tmp_path: Path) -> None:
    """Write generated HTML to a destination file."""
    export = make_export()
    destination = tmp_path / "nested" / "dependencies.html"

    HtmlWriter().write(
        export,
        destination,
    )

    assert destination.is_file()

    html = destination.read_text(
        encoding="utf-8",
    )

    assert html.startswith("<!DOCTYPE html>")
    assert '"depcycle.cli"' in html
    assert '"pathlib"' in html


def test_write_creates_parent_directories(
    tmp_path: Path,
) -> None:
    """Create missing parent directories for HTML output."""
    export = make_export()

    destination = tmp_path / "one" / "two" / "dependencies.html"

    HtmlWriter().write(
        export,
        destination,
    )

    assert destination.exists()
    assert destination.parent.is_dir()


def test_render_html_does_not_use_cdn_urls() -> None:
    """Keep generated HTML independent of external JavaScript CDNs."""
    export = make_export()

    html = HtmlWriter()._render_html(export)

    assert "cdn.jsdelivr.net" not in html


def test_render_html_preserves_unicode_data() -> None:
    """Preserve Unicode graph data in the generated HTML."""
    graph = DependencyGraph()

    node = ModuleNode(
        name="café",
        file_path=None,
        module_type=ModuleType.UNKNOWN,
    )

    graph._project_root = Path("/project")
    graph.add_node(node)

    export = build_export(graph)
    html = HtmlWriter()._render_html(export)

    assert "café" in html
