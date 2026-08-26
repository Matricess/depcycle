from pathlib import Path

from depcycle.graph.graph import DependencyGraph
from depcycle.graph.node import ModuleNode, ModuleType
from depcycle.output import HtmlWriter


def _build_graph() -> DependencyGraph:
    graph = DependencyGraph()
    graph._project_root = Path("/tmp/project")

    main = ModuleNode("app.main", Path("/tmp/project/app/main.py"), ModuleType.LOCAL)
    util = ModuleNode("app.util", Path("/tmp/project/app/util.py"), ModuleType.LOCAL)
    stdlib = ModuleNode("os", None, ModuleType.STDLIB)
    third_party = ModuleNode("requests", None, ModuleType.THIRD_PARTY)

    main.dependencies = {util, stdlib}
    util.dependencies = {third_party}

    graph.nodes = {
        "app.main": main,
        "app.util": util,
        "os": stdlib,
        "requests": third_party,
    }
    return graph


def test_html_writer_creates_self_contained_document(tmp_path):
    graph = _build_graph()
    output_path = tmp_path / "deps.html"

    HtmlWriter().write(graph, output_path)

    html = output_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in html
    assert "depcycle" in html.lower()
    assert "d3" in html.lower()
    assert "app.main" in html
    assert "requests" in html


def test_html_writer_stdout_mode():
    import io
    from contextlib import redirect_stdout

    graph = _build_graph()
    buf = io.StringIO()
    with redirect_stdout(buf):
        HtmlWriter().write(graph, None)

    content = buf.getvalue()
    assert "<!DOCTYPE html>" in content
    assert "depcycle" in content.lower()
