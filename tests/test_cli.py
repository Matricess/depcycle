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
    """Require a subcommand (analyze or query)."""
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


def test_create_parser_accepts_target_flag(
    tmp_path: Path,
) -> None:
    """Parse one or more --target values."""
    parser = DepCycleCLI._create_parser()

    parsed = parser.parse_args(
        [
            "analyze",
            str(tmp_path),
            "--target",
            "app.models",
            "--target",
            "app.service",
        ],
    )

    assert parsed.target == [
        "app.models",
        "app.service",
    ]


def test_create_parser_accepts_impact_flag(
    tmp_path: Path,
) -> None:
    """Parse one or more --impact values."""
    parser = DepCycleCLI._create_parser()

    parsed = parser.parse_args(
        [
            "analyze",
            str(tmp_path),
            "--impact",
            "app.models",
        ],
    )

    assert parsed.impact == ["app.models"]


def test_create_parser_accepts_path_flag(
    tmp_path: Path,
) -> None:
    """Parse --path source and target values."""
    parser = DepCycleCLI._create_parser()

    parsed = parser.parse_args(
        [
            "analyze",
            str(tmp_path),
            "--path",
            "app.api",
            "app.repository",
        ],
    )

    assert parsed.path == ["app.api", "app.repository"]


def test_main_rejects_missing_project_path(
    capsys,
    tmp_path: Path,
) -> None:
    """Exit with status one for a missing project path."""
    missing = tmp_path / "missing"

    with pytest.raises(SystemExit) as exc_info:
        DepCycleCLI.main(
            ["analyze", str(missing)],
        )

    assert exc_info.value.code == 1

    captured = capsys.readouterr()

    assert f"Error: Project path does not exist: {missing}" in captured.err


def test_main_rejects_file_as_project_path(
    capsys,
    tmp_path: Path,
) -> None:
    """Exit with status one when the project path is a file."""
    project_file = tmp_path / "project.py"
    project_file.write_text(
        "",
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exc_info:
        DepCycleCLI.main(
            ["analyze", str(project_file)],
        )

    assert exc_info.value.code == 1

    captured = capsys.readouterr()

    assert f"Error: Project path is not a directory: {project_file}" in captured.err


def test_main_defaults_to_html_output(
    tmp_path: Path,
) -> None:
    """Generate dependencies.html when no output is specified."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        ["analyze", str(project)],
    )

    output = Path.cwd() / "dependencies.html"

    try:
        assert output.is_file()

        html = output.read_text(
            encoding="utf-8",
        )

        assert html.startswith("<!DOCTYPE html>")
        assert "DepCycle" in html
    finally:
        output.unlink(missing_ok=True)


def test_main_infers_json_format_from_output_suffix(
    tmp_path: Path,
) -> None:
    """Infer JSON output from a .json destination."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.json"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--output",
            str(destination),
        ],
    )

    assert destination.is_file()

    text = destination.read_text(
        encoding="utf-8",
    )

    assert '"schema_version": 2' in text


def test_main_infers_dot_format_from_output_suffix(
    tmp_path: Path,
) -> None:
    """Infer DOT output from a .dot destination."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.dot"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--output",
            str(destination),
        ],
    )

    assert destination.is_file()

    text = destination.read_text(
        encoding="utf-8",
    )

    assert text.startswith("digraph depcycle {")


def test_main_defaults_to_html_for_unknown_output_suffix(
    tmp_path: Path,
) -> None:
    """Use HTML when an output extension does not identify a format."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.data"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--output",
            str(destination),
        ],
    )

    assert destination.is_file()

    text = destination.read_text(
        encoding="utf-8",
    )

    assert text.startswith("<!DOCTYPE html>")


def test_main_explicit_format_overrides_output_suffix(
    tmp_path: Path,
) -> None:
    """Honor an explicitly supplied output format."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.data"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--output",
            str(destination),
            "--format",
            "json",
        ],
    )

    assert destination.is_file()

    text = destination.read_text(
        encoding="utf-8",
    )

    assert '"schema_version": 2' in text


def test_main_can_write_json_to_stdout(
    capsys,
    tmp_path: Path,
) -> None:
    """Write clean JSON to stdout when output is '-', with no progress noise."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--format",
            "json",
            "--output",
            "-",
        ],
    )

    captured = capsys.readouterr()

    # stdout must contain only valid JSON — no progress lines mixed in.
    parsed = json.loads(captured.out)
    assert parsed["schema_version"] == 2
    assert "project" in parsed

    # Progress must have gone to stderr.
    assert "Analyzing project:" in captured.err


def test_main_uses_exclusion_patterns(
    tmp_path: Path,
) -> None:
    """Apply user-supplied exclusion patterns during analysis."""
    project = make_project(tmp_path)

    tests_dir = project / "tests"
    tests_dir.mkdir()

    (tests_dir / "test_extra.py").write_text(
        "import sys\n",
        encoding="utf-8",
    )

    destination = tmp_path / "result.json"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--exclude",
            "tests",
            "--format",
            "json",
            "--output",
            str(destination),
        ],
    )

    text = destination.read_text(
        encoding="utf-8",
    )

    assert "test_extra" not in text
    assert '"example.module"' in text


def test_main_honors_no_stdlib_flag(
    tmp_path: Path,
) -> None:
    """Remove standard-library nodes when requested."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.json"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--no-stdlib",
            "--format",
            "json",
            "--output",
            str(destination),
        ],
    )

    text = destination.read_text(
        encoding="utf-8",
    )

    assert '"id": "json"' not in text


def test_main_prints_focused_target_summary_to_stderr(
    capsys,
    tmp_path: Path,
) -> None:
    """Print a focused summary for a resolvable --target module."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.json"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--target",
            "example.module",
            "--format",
            "json",
            "--output",
            str(destination),
        ],
    )

    captured = capsys.readouterr()

    assert "Target: example.module" in captured.err
    assert "Direct dependencies:" in captured.err
    assert "Direct dependents:" in captured.err
    assert "Cycles involving:" in captured.err
    assert destination.is_file()


def test_main_prints_not_found_for_unknown_target(
    capsys,
    tmp_path: Path,
) -> None:
    """Print a not-found message for a --target that is not in the graph."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.json"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--target",
            "does.not.exist",
            "--format",
            "json",
            "--output",
            str(destination),
        ],
    )

    captured = capsys.readouterr()

    assert "Target: does.not.exist" in captured.err
    assert "Not found in graph" in captured.err


def test_main_prints_impact_summary_to_stderr(
    capsys,
    tmp_path: Path,
) -> None:
    """Print an impact summary for a resolvable --impact module."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.json"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--impact",
            "example.module",
            "--format",
            "json",
            "--output",
            str(destination),
        ],
    )

    captured = capsys.readouterr()

    assert "Impact: example.module" in captured.err
    assert "Direct dependents:" in captured.err
    assert "Reachable dependents:" in captured.err
    assert "Direct dependencies:" in captured.err
    assert "Cycles involving:" in captured.err
    assert destination.is_file()


def test_main_prints_not_found_for_unknown_impact_target(
    capsys,
    tmp_path: Path,
) -> None:
    """Print a not-found message for an --impact module missing from the graph."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.json"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--impact",
            "does.not.exist",
            "--format",
            "json",
            "--output",
            str(destination),
        ],
    )

    captured = capsys.readouterr()

    assert "Impact: does.not.exist" in captured.err
    assert "Not found in graph" in captured.err


def test_main_prints_shortest_path_to_stderr(
    capsys,
    tmp_path: Path,
) -> None:
    """Print the import chain for a connected --path pair."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.json"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--path",
            "example",
            "example.module",
            "--format",
            "json",
            "--output",
            str(destination),
        ],
    )

    captured = capsys.readouterr()

    assert "Path: example → example.module" in captured.err


def test_main_prints_no_path_found_for_disconnected_modules(
    capsys,
    tmp_path: Path,
) -> None:
    """Print a not-found message for a disconnected --path pair."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.json"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--path",
            "example.module",
            "example",
            "--format",
            "json",
            "--output",
            str(destination),
        ],
    )

    captured = capsys.readouterr()

    assert "No import path found." in captured.err


def test_main_honors_include_all_flag(
    tmp_path: Path,
) -> None:
    """Disable built-in exclusions when include-all is requested."""
    project = make_project(tmp_path)

    ignored_dir = project / "tests"
    ignored_dir.mkdir()

    (ignored_dir / "helper.py").write_text(
        "import os\n",
        encoding="utf-8",
    )

    destination = tmp_path / "result.json"

    DepCycleCLI.main(
        [
            "analyze",
            str(project),
            "--include-all",
            "--format",
            "json",
            "--output",
            str(destination),
        ],
    )

    text = destination.read_text(
        encoding="utf-8",
    )

    assert "helper" in text


def test_run_reports_analysis_progress(
    capsys,
    tmp_path: Path,
) -> None:
    """Print progress messages to stderr, not stdout."""
    project = make_project(tmp_path)

    output = tmp_path / "result.json"

    from depcycle.config import AnalysisConfig

    config = AnalysisConfig(
        project_path=project,
    )

    DepCycleCLI.run(
        config,
        output_path=output,
        output_format="json",
    )

    captured = capsys.readouterr()

    # Progress belongs on stderr so stdout stays clean for machine consumers.
    assert "Analyzing project:" in captured.err
    assert "Building dependency graph..." in captured.err
    assert "Found " in captured.err
    assert "No circular dependencies detected" in captured.err
    assert "Generating JSON output..." in captured.err
    assert "JSON output saved to:" in captured.err

    # stdout must be empty when writing to a file.
    assert captured.out == ""


def test_run_rejects_unsupported_format(
    tmp_path: Path,
) -> None:
    """Reject output formats not registered by the CLI."""
    from depcycle.config import AnalysisConfig

    config = AnalysisConfig(
        project_path=make_project(tmp_path),
    )

    with pytest.raises(
        ValueError,
        match="Unsupported output format",
    ):
        DepCycleCLI.run(
            config,
            output_path=None,
            output_format="yaml",
        )


def test_main_handles_keyboard_interrupt(
    monkeypatch,
    capsys,
) -> None:
    """Exit cleanly when analysis is interrupted, printing to stderr."""
    monkeypatch.setattr(
        DepCycleCLI,
        "run",
        staticmethod(lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt)),
    )

    with pytest.raises(SystemExit) as exc_info:
        DepCycleCLI.main(
            ["analyze", "."],
        )

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "Interrupted by user" in captured.err
    assert captured.out == ""


def test_create_parser_rejects_invalid_format(
    tmp_path: Path,
) -> None:
    """Reject formats outside the supported choices."""
    parser = DepCycleCLI._create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "analyze",
                str(tmp_path),
                "--format",
                "yaml",
            ]
        )


def test_create_parser_requires_query_subcommand(
    tmp_path: Path,
) -> None:
    """Require one of the query sub-subcommands."""
    parser = DepCycleCLI._create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["query", str(tmp_path)])


def test_query_module_prints_compact_json(
    capsys,
    tmp_path: Path,
) -> None:
    """Print compact JSON node info for `query module`."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        ["query", str(project), "module", "example.module"],
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload == {
        "module": "example.module",
        "type": "local",
        "file": "example/module.py",
        "fan_in": 1,
        "fan_out": 1,
    }


def test_query_module_reports_missing_module(
    capsys,
    tmp_path: Path,
) -> None:
    """Exit with an error for `query module` on an unknown module."""
    project = make_project(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        DepCycleCLI.main(
            ["query", str(project), "module", "does.not.exist"],
        )

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload == {"error": "module not found: does.not.exist"}


def test_query_deps_lists_direct_dependencies(
    capsys,
    tmp_path: Path,
) -> None:
    """Print compact JSON dependency list for `query deps`."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        ["query", str(project), "deps", "example"],
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload == {
        "module": "example",
        "deps": ["example.module"],
    }


def test_query_dependents_lists_direct_dependents(
    capsys,
    tmp_path: Path,
) -> None:
    """Print compact JSON dependent list for `query dependents`."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        ["query", str(project), "dependents", "example.module"],
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload == {
        "module": "example.module",
        "dependents": ["example"],
    }


def test_query_cycles_lists_all_cycles(
    capsys,
    tmp_path: Path,
) -> None:
    """Print compact JSON cycle list for `query cycles`."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        ["query", str(project), "cycles"],
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload == {"cycles": []}


def test_query_cycles_filters_by_module(
    capsys,
    tmp_path: Path,
) -> None:
    """Filter `query cycles` output to cycles touching --module."""
    project = tmp_path
    package = project / "app"
    package.mkdir()

    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "a.py").write_text("from . import b\n", encoding="utf-8")
    (package / "b.py").write_text("from . import a\n", encoding="utf-8")

    DepCycleCLI.main(
        ["query", str(project), "cycles", "--module", "app.a"],
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert len(payload["cycles"]) == 1
    assert "app.a" in payload["cycles"][0]


def test_query_neighborhood_lists_nearby_modules(
    capsys,
    tmp_path: Path,
) -> None:
    """Print compact JSON neighborhood for `query neighborhood`."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        ["query", str(project), "neighborhood", "example.module", "--depth", "1"],
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload == {
        "module": "example.module",
        "depth": 1,
        "neighborhood": ["example", "json"],
    }


def test_query_rejects_missing_project_path(
    capsys,
    tmp_path: Path,
) -> None:
    """Exit with status one for a query against a missing project path."""
    missing = tmp_path / "missing"

    with pytest.raises(SystemExit) as exc_info:
        DepCycleCLI.main(
            ["query", str(missing), "module", "example"],
        )

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert f"Error: Project path does not exist: {missing}" in captured.err
