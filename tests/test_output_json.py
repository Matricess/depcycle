import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from depcycle.graph.graph import DependencyGraph
from depcycle.graph.node import ModuleNode, ModuleType
from depcycle.output import JsonWriter


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


def test_json_writer_writes_expected_structure(tmp_path):
    graph = _build_graph()
    output_path = tmp_path / "deps.json"

    JsonWriter().write(graph, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert list(payload.keys()) == ["project", "summary", "nodes", "edges", "cycles"]
    assert payload["summary"]["total_modules"] == 4
    assert payload["summary"]["local"] == 2
    assert payload["summary"]["stdlib"] == 1
    assert payload["summary"]["third_party"] == 1
    assert payload["summary"]["unknown"] == 0
    assert len(payload["edges"]) == 3
    assert payload["nodes"][0]["id"]


def test_json_writer_writes_to_stdout_when_dest_is_none():
    graph = _build_graph()
    buffer = io.StringIO()

    with redirect_stdout(buffer):
        JsonWriter().write(graph, None)

    payload = json.loads(buffer.getvalue())
    assert payload["summary"]["total_modules"] == 4
    assert payload["edges"]
