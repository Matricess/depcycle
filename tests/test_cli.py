"""Tests for the DepCycle command-line interface."""

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


def test_create_parser_requires_project_path() -> None:
    """Require a positional project path."""
    parser = DepCycleCLI._create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_create_parser_accepts_project_path(
    tmp_path: Path,
) -> None:
    """Parse the project path argument."""
    parser = DepCycleCLI._create_parser()

    parsed = parser.parse_args(
        [str(tmp_path)],
    )

    assert parsed.project_path == str(tmp_path)


def test_create_parser_accepts_output_options(
    tmp_path: Path,
) -> None:
    """Parse output path and format options."""
    parser = DepCycleCLI._create_parser()

    parsed = parser.parse_args(
        [
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
            str(tmp_path),
            "--no-third-party",
            "--no-stdlib",
            "--include-all",
        ],
    )

    assert parsed.no_third_party is True
    assert parsed.no_stdlib is True
    assert parsed.include_all is True


def test_main_rejects_missing_project_path(
    capsys,
    tmp_path: Path,
) -> None:
    """Exit with status one for a missing project path."""
    missing = tmp_path / "missing"

    with pytest.raises(SystemExit) as exc_info:
        DepCycleCLI.main(
            [str(missing)],
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
            [str(project_file)],
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
        [str(project)],
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
            str(project),
            "--output",
            str(destination),
        ],
    )

    assert destination.is_file()

    text = destination.read_text(
        encoding="utf-8",
    )

    assert '"schema_version": 1' in text


def test_main_infers_dot_format_from_output_suffix(
    tmp_path: Path,
) -> None:
    """Infer DOT output from a .dot destination."""
    project = make_project(tmp_path)
    destination = tmp_path / "result.dot"

    DepCycleCLI.main(
        [
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

    assert '"schema_version": 1' in text


def test_main_can_write_json_to_stdout(
    capsys,
    tmp_path: Path,
) -> None:
    """Write JSON directly to stdout when output is '-'."""
    project = make_project(tmp_path)

    DepCycleCLI.main(
        [
            str(project),
            "--format",
            "json",
            "--output",
            "-",
        ],
    )

    captured = capsys.readouterr()

    assert '"schema_version": 1' in captured.out
    assert '"project"' in captured.out


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
    """Print normal progress messages during analysis."""
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

    assert "Analyzing project:" in captured.out
    assert "Building dependency graph..." in captured.out
    assert "Found " in captured.out
    assert "No circular dependencies detected" in captured.out
    assert "Generating JSON output..." in captured.out
    assert "JSON output saved to:" in captured.out


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
) -> None:
    """Exit cleanly when analysis is interrupted."""
    monkeypatch.setattr(
        DepCycleCLI,
        "run",
        staticmethod(lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt)),
    )

    with pytest.raises(SystemExit) as exc_info:
        DepCycleCLI.main(
            ["."],
        )

    assert exc_info.value.code == 1


def test_create_parser_rejects_invalid_format(
    tmp_path: Path,
) -> None:
    """Reject formats outside the supported choices."""
    parser = DepCycleCLI._create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                str(tmp_path),
                "--format",
                "yaml",
            ]
        )
