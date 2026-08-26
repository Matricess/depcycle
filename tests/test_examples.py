import json
from pathlib import Path

from depcycle.cli import DepCycleCLI

EXAMPLES_ROOT = Path(__file__).resolve().parents[1] / "examples"


def _analyze_example(example_name: str, tmp_path: Path) -> dict:
    output_path = tmp_path / f"{example_name}.json"
    DepCycleCLI.main([
        str(EXAMPLES_ROOT / example_name),
        "--format",
        "json",
        "--output",
        str(output_path),
    ])
    return json.loads(output_path.read_text(encoding="utf-8"))


def test_clean_ecommerce_example_has_no_cycles(tmp_path, capsys):
    result = _analyze_example("clean_project", tmp_path)

    capsys.readouterr()
    assert result["summary"]["cycles_found"] == 0
    assert result["summary"]["local"] >= 10


def test_pipeline_example_has_no_cycles(tmp_path, capsys):
    result = _analyze_example("pipeline_project", tmp_path)

    capsys.readouterr()
    assert result["summary"]["cycles_found"] == 0
    assert {"pipeline.ingest", "pipeline.transform", "pipeline.storage"} <= {
        node["id"] for node in result["nodes"]
    }


def test_messy_checkout_example_reports_cycles(tmp_path, capsys):
    result = _analyze_example("messy_project", tmp_path)

    capsys.readouterr()
    assert result["summary"]["cycles_found"] >= 1
    assert {"app.models", "app.events", "app.repositories"} <= {
        node["id"] for node in result["nodes"]
    }
