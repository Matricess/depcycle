"""Configuration settings that control DepCycle analysis behavior."""

from __future__ import annotations

from pathlib import Path

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
            return list(
                dict.fromkeys(user_patterns),
            )

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
        targets: list[str] | None = None,
    ) -> None:
        """
        Initialize analysis configuration.

        Args:
            project_path:
                Root directory of the project being analyzed.
            exclude_patterns:
                Additional file or directory patterns to exclude.
            show_third_party:
                Whether third-party dependencies should appear in the graph.
            show_stdlib:
                Whether standard-library dependencies should appear.
            show_unknown:
                Whether unknown dependencies should appear.
            include_all:
                Whether to disable built-in exclusion patterns.
            targets:
                Optional target modules for future focused analysis.
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
        self.targets = list(targets or [])

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
            f"targets={self.targets!r}"
            ")"
        )
