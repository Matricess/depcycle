"""Tests for DepCycle analysis configuration."""

from pathlib import Path

from depcycle.config import (
    DEFAULT_EXCLUDE_PATTERNS,
    AnalysisConfig,
)


def test_default_exclude_patterns_are_defined() -> None:
    """Provide the expected built-in exclusion patterns."""
    assert "venv" in DEFAULT_EXCLUDE_PATTERNS
    assert ".venv" in DEFAULT_EXCLUDE_PATTERNS
    assert "__pycache__" in DEFAULT_EXCLUDE_PATTERNS
    assert "tests" in DEFAULT_EXCLUDE_PATTERNS
    assert "dist" in DEFAULT_EXCLUDE_PATTERNS
    assert "build" in DEFAULT_EXCLUDE_PATTERNS


def test_default_configuration() -> None:
    """Initialize configuration with expected defaults."""
    config = AnalysisConfig(
        project_path=Path("/project"),
    )

    assert config.project_path == Path("/project")
    assert config.show_third_party is True
    assert config.show_stdlib is True
    assert config.show_unknown is True
    assert config.include_all is False
    assert config.targets == []


def test_default_exclusion_patterns_are_applied() -> None:
    """Include built-in exclusion patterns by default."""
    config = AnalysisConfig(
        project_path=Path("/project"),
    )

    assert config.exclude_patterns == DEFAULT_EXCLUDE_PATTERNS


def test_custom_exclusion_patterns_are_added() -> None:
    """Append caller-provided exclusion patterns."""
    config = AnalysisConfig(
        project_path=Path("/project"),
        exclude_patterns=[
            "coverage",
            "*.generated.py",
        ],
    )

    assert "coverage" in config.exclude_patterns
    assert "*.generated.py" in config.exclude_patterns

    for pattern in DEFAULT_EXCLUDE_PATTERNS:
        assert pattern in config.exclude_patterns


def test_duplicate_exclusion_patterns_are_removed() -> None:
    """Remove duplicate built-in and user exclusion patterns."""
    config = AnalysisConfig(
        project_path=Path("/project"),
        exclude_patterns=[
            "tests",
            "coverage",
            "coverage",
            "tests",
        ],
    )

    assert config.exclude_patterns.count("tests") == 1
    assert config.exclude_patterns.count("coverage") == 1


def test_exclusion_pattern_order_is_preserved() -> None:
    """Preserve built-in order followed by new user patterns."""
    config = AnalysisConfig(
        project_path=Path("/project"),
        exclude_patterns=[
            "coverage",
            "generated",
        ],
    )

    assert config.exclude_patterns[: len(DEFAULT_EXCLUDE_PATTERNS)] == (
        DEFAULT_EXCLUDE_PATTERNS
    )

    assert config.exclude_patterns[-2:] == [
        "coverage",
        "generated",
    ]


def test_include_all_disables_default_exclusions() -> None:
    """Use only caller exclusions when include-all is enabled."""
    config = AnalysisConfig(
        project_path=Path("/project"),
        exclude_patterns=[
            "coverage",
            "tests",
        ],
        include_all=True,
    )

    assert config.exclude_patterns == [
        "coverage",
        "tests",
    ]


def test_include_all_removes_duplicate_user_patterns() -> None:
    """Deduplicate user patterns when include-all is enabled."""
    config = AnalysisConfig(
        project_path=Path("/project"),
        exclude_patterns=[
            "coverage",
            "coverage",
            "tests",
            "tests",
        ],
        include_all=True,
    )

    assert config.exclude_patterns == [
        "coverage",
        "tests",
    ]


def test_include_all_with_no_custom_patterns() -> None:
    """Produce an empty exclusion list when include-all is enabled."""
    config = AnalysisConfig(
        project_path=Path("/project"),
        include_all=True,
    )

    assert config.exclude_patterns == []


def test_visibility_options_are_stored() -> None:
    """Store graph visibility options exactly as supplied."""
    config = AnalysisConfig(
        project_path=Path("/project"),
        show_third_party=False,
        show_stdlib=False,
        show_unknown=False,
    )

    assert config.show_third_party is False
    assert config.show_stdlib is False
    assert config.show_unknown is False


def test_targets_are_copied() -> None:
    """Copy target modules instead of retaining the caller's list."""
    targets = [
        "depcycle.cli",
        "depcycle.graph",
    ]

    config = AnalysisConfig(
        project_path=Path("/project"),
        targets=targets,
    )

    assert config.targets == targets

    targets.append("depcycle.output")

    assert config.targets == [
        "depcycle.cli",
        "depcycle.graph",
    ]


def test_none_targets_becomes_empty_list() -> None:
    """Normalize a missing target list to an empty list."""
    config = AnalysisConfig(
        project_path=Path("/project"),
        targets=None,
    )

    assert config.targets == []


def test_none_exclusions_use_defaults() -> None:
    """Normalize missing custom exclusions to built-in exclusions."""
    config = AnalysisConfig(
        project_path=Path("/project"),
        exclude_patterns=None,
    )

    assert config.exclude_patterns == DEFAULT_EXCLUDE_PATTERNS


def test_project_path_is_preserved_as_path_object() -> None:
    """Store project paths as pathlib Path objects."""
    config = AnalysisConfig(
        project_path="relative/project",
    )

    assert isinstance(config.project_path, Path)
    assert config.project_path == Path("relative/project")


def test_repr_contains_configuration_values() -> None:
    """Provide a useful developer-facing representation."""
    config = AnalysisConfig(
        project_path=Path("/project"),
        exclude_patterns=["coverage"],
        show_third_party=False,
        show_stdlib=False,
        show_unknown=True,
        include_all=True,
        targets=["depcycle.cli"],
    )

    representation = repr(config)

    assert representation.startswith("AnalysisConfig(")
    assert "project_path=PosixPath('/project')" in representation
    assert "exclude_patterns=" in representation
    assert "show_third_party=False" in representation
    assert "show_stdlib=False" in representation
    assert "show_unknown=True" in representation
    assert "include_all=True" in representation
    assert "targets=['depcycle.cli']" in representation


def test_build_exclude_patterns_can_be_called_directly() -> None:
    """Build exclusion patterns through the shared helper."""
    result = AnalysisConfig._build_exclude_patterns(
        ["coverage"],
        include_all=False,
    )

    assert result[: len(DEFAULT_EXCLUDE_PATTERNS)] == (DEFAULT_EXCLUDE_PATTERNS)
    assert result[-1] == "coverage"


def test_build_exclude_patterns_include_all() -> None:
    """Build only user exclusions when include-all is enabled."""
    result = AnalysisConfig._build_exclude_patterns(
        [
            "coverage",
            "coverage",
            "generated",
        ],
        include_all=True,
    )

    assert result == [
        "coverage",
        "generated",
    ]
