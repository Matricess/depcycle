"""Tests for the DepCycle command-line interface."""

import json
from pathlib import Path

import pytest

from depcycle.cli import DepCycleCLI


def make_project(tmp_path: Path) -> Path:
    """Create a minimal Python project for CLI tests."""
    package = tmp_path / "example"
    package.mkdir()

    (package / "__init__.py").write_text(
        "from .module import value\n",
        encoding="utf-8",
    )

    (package / "module.py").write_text(
        "import json\nvalue = 1\n",
        encoding="utf-8",
    )

    return tmp_path


def test_create_parser_requires_command() -> None:
    """Require a subcommand (analyze or inspect)."""
    parser = DepCycleCLI._create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_create_parser_accepts_project_path(
    tmp_path: Path,
) -> None:
    """Parse the project path argument for the analyze subcommand."""
    parser = DepCycleCLI._create_parser()

    parsed = parser.parse_args(
        ["analyze", str(tmp_path)],
    )

    assert parsed.command == "analyze"
    assert parsed.project_path == str(tmp_path)


def test_create_parser_accepts_output_options(
    tmp_path: Path,
) -> None:
    """Parse output path and format options."""
    parser = DepCycleCLI._create_parser()

    parsed = parser.parse_args(
        [
            "analyze",
            str(tmp_path),
            "--output",
            "result.json",
            "--format",
            "json",
        ],
    )

    assert parsed.output == "result.json"
    assert parsed.format == "json"


def test_create_parser_accepts_multiple_exclusions(
    tmp_path: Path,
) -> None:
    """Allow multiple exclusion patterns."""
    parser = DepCycleCLI._create_parser()

    parsed = parser.parse_args(
        [
            "analyze",
            str(tmp_path),
            "--exclude",
            "tests",
            "--exclude",
            "*.pyc",
        ],
    )

    assert parsed.exclude == [
        "tests",
        "*.pyc",
    ]


def test_create_parser_accepts_visibility_flags(
    tmp_path: Path,
) -> None:
    """Parse graph visibility and include-all flags."""
    parser = DepCycleCLI._create_parser()

    parsed = parser.parse_args(
        [
            "analyze",
            str(tmp_path),
            "--no-third-party",
            "--no-stdlib",
            "--include-all",
        ],
    )

    assert parsed.no_third_party is True
    assert parsed.no_stdlib is True
    assert parsed.include_all is True


def test_create_parser_accepts_fail_on_cycles_flag(
    tmp_path: Path,
) -> None:
    """Parse fail-on-cycles flag."""
    parser = DepCycleCLI._create_parser()

    parsed = parser.parse_args(
        [
            "analyze",
            str(tmp_path),
            "--fail-on-cycles",
        ],
    )

    assert parsed.fail_on_cycles is True


def test_main_analyze_generates_html_report(
    capsys,
    tmp_path: Path,
) -> None:
    """Execute analysis and write default dependencies.html output."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        ["analyze", str(project)],
    )

    captured = capsys.readouterr()

    assert "Analyzing project:" in captured.err
    assert "Found 3 modules" in captured.err
    assert "No circular dependencies detected" in captured.err
    assert "✓ HTML output saved to: dependencies.html" in captured.err

    output = Path("dependencies.html")
    assert output.is_file()
    output.unlink()


def test_main_analyze_fail_on_cycles(
    capsys,
    tmp_path: Path,
) -> None:
    """Exit with status 1 when --fail-on-cycles is active and cycles exist."""
    project = tmp_path
    package = project / "app"
    package.mkdir()

    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "a.py").write_text("from . import b\n", encoding="utf-8")
    (package / "b.py").write_text("from . import a\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        DepCycleCLI.main(
            ["analyze", str(project), "--fail-on-cycles"],
        )

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "Warning: Found 1 circular dependency cycles!" in captured.err
    assert "Error: Circular dependencies found and --fail-on-cycles is active." in captured.err

    output = Path("dependencies.html")
    if output.is_file():
        output.unlink()


def test_inspect_module_prints_json(
    capsys,
    tmp_path: Path,
) -> None:
    """Print inspection details for a module in JSON format."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        ["inspect", str(project), "example.module"],
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["module"] == "example.module"
    assert payload["type"] == "local"
    assert payload["dependencies_count"] == 1
    assert payload["dependencies"] == ["json"]


def test_inspect_cycles_prints_json(
    capsys,
    tmp_path: Path,
) -> None:
    """Print project circular dependencies in JSON format."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        ["inspect", str(project), "--cycles"],
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload == {"cycles": []}


def test_inspect_reports_missing_module(
    capsys,
    tmp_path: Path,
) -> None:
    """Exit with an error for inspect on an unknown module."""
    project = make_project(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        DepCycleCLI.main(
            ["inspect", str(project), "does.not.exist"],
        )

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {"error": "module not found: does.not.exist"}
