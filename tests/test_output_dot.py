from pathlib import Path

from depcycle.graph.graph import DependencyGraph
from depcycle.graph.node import ModuleNode, ModuleType
from depcycle.output import DotWriter


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


def test_dot_writer_emits_graphviz_syntax(tmp_path):
    graph = _build_graph()
    output_path = tmp_path / "deps.dot"

    DotWriter().write(graph, output_path)

    contents = output_path.read_text(encoding="utf-8")
    assert "digraph depcycle" in contents
    assert '"app.main"' in contents
    assert '"app.util" -> "os"' in contents or '"os"' in contents
    assert "color=\"#FB8C00\"" in contents or "color=\"#6D6D6D\"" in contents
    assert "graph" in contents.lower()


def test_dot_writer_stdout_mode():
    graph = _build_graph()

    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        DotWriter().write(graph, None)

    content = buf.getvalue()
    assert "digraph depcycle" in content
    assert "requests" in content
