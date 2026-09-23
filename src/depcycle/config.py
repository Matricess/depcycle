"""Configuration settings that control DepCycle analysis behavior."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

DEFAULT_EXCLUDE_PATTERNS = [
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "dist",
    "build",
    "*.egg-info",
    "migrations",
    "tests",
    "test",
    "scripts",
    "examples",
]


class AnalysisConfig:
    """Configuration that controls dependency analysis behavior."""

    @staticmethod
    def _build_exclude_patterns(
        exclude_patterns: list[str] | None,
        include_all: bool,
    ) -> list[str]:
        """
        Build the final exclusion pattern list.

        When ``include_all`` is false, built-in exclusions are included
        before user-provided exclusions. Duplicate patterns are removed
        while preserving their original order.

        When ``include_all`` is true, only user-provided exclusions are used.
        """
        user_patterns = list(exclude_patterns or [])

        if include_all:
            return list(dict.fromkeys(user_patterns))

        patterns = list(DEFAULT_EXCLUDE_PATTERNS)

        for pattern in user_patterns:
            if pattern not in patterns:
                patterns.append(pattern)

        return patterns

    def __init__(
        self,
        project_path: Path | str,
        exclude_patterns: list[str] | None = None,
        show_third_party: bool = True,
        show_stdlib: bool = True,
        show_unknown: bool = True,
        include_all: bool = False,
        fail_on_cycles: bool = False,
        targets: list[str] | None = None,
    ) -> None:
        """
        Initialize analysis configuration.

        Args:
            project_path: Root directory of the project being analyzed.
            exclude_patterns: Additional file or directory patterns to exclude.
            show_third_party: Whether third-party dependencies should appear in graph.
            show_stdlib: Whether standard-library dependencies should appear.
            show_unknown: Whether unknown dependencies should appear.
            include_all: Whether to disable built-in exclusion patterns.
            fail_on_cycles: Whether analysis should indicate failure when cycles are found.
            targets: Optional list of target module filters.
        """
        self.project_path = Path(project_path)

        self.exclude_patterns = self._build_exclude_patterns(
            exclude_patterns,
            include_all,
        )

        self.show_third_party = show_third_party
        self.show_stdlib = show_stdlib
        self.show_unknown = show_unknown
        self.include_all = include_all
        self.fail_on_cycles = fail_on_cycles
        self.targets = list(targets or [])

    @classmethod
    def from_pyproject(
        cls,
        project_path: Path | str,
        cli_exclude: list[str] | None = None,
        cli_show_third_party: bool = True,
        cli_show_stdlib: bool = True,
        include_all: bool = False,
        fail_on_cycles: bool = False,
    ) -> AnalysisConfig:
        """Create AnalysisConfig, combining pyproject.toml [tool.depcycle] settings with CLI overrides."""
        path = Path(project_path)
        pyproject_file = path / "pyproject.toml"

        toml_exclude: list[str] = []
        toml_third_party = True
        toml_stdlib = True
        toml_fail_on_cycles = False

        if pyproject_file.is_file():
            try:
                with open(pyproject_file, "rb") as f:
                    data = tomllib.load(f)
                tool_config = data.get("tool", {}).get("depcycle", {})
                toml_exclude = tool_config.get("exclude", [])
                toml_third_party = tool_config.get("show_third_party", True)
                toml_stdlib = tool_config.get("show_stdlib", True)
                toml_fail_on_cycles = tool_config.get("fail_on_cycles", False)
            except (OSError, ValueError, TypeError):
                pass

        combined_exclude = list(dict.fromkeys(toml_exclude + (cli_exclude or [])))

        return cls(
            project_path=path,
            exclude_patterns=combined_exclude,
            show_third_party=cli_show_third_party and toml_third_party,
            show_stdlib=cli_show_stdlib and toml_stdlib,
            show_unknown=True,
            include_all=include_all,
            fail_on_cycles=fail_on_cycles or toml_fail_on_cycles,
        )

    def __repr__(self) -> str:
        """Return a developer-friendly representation of the configuration."""
        return (
            f"{self.__class__.__name__}("
            f"project_path={self.project_path!r}, "
            f"exclude_patterns={self.exclude_patterns!r}, "
            f"show_third_party={self.show_third_party!r}, "
            f"show_stdlib={self.show_stdlib!r}, "
            f"show_unknown={self.show_unknown!r}, "
            f"include_all={self.include_all!r}, "
            f"fail_on_cycles={self.fail_on_cycles!r}, "
            f"targets={self.targets!r}"
            ")"
        )
