"""Analysis configuration for DepCycle settings."""

from __future__ import annotations

from pathlib import Path

# Default exclusion patterns that are automatically applied
DEFAULT_EXCLUDE_PATTERNS = [
    'venv',
    '.venv',
    'env',
    '.env',
    '__pycache__',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.git',
    '.hg',
    '.svn',
    'node_modules',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    'dist',
    'build',
    '*.egg-info',
    'migrations',
]


class AnalysisConfig:
    """Configuration that affects only analysis behavior, not output rendering."""

    def __init__(
        self,
        project_path: Path,
        exclude_patterns: list[str] | None = None,
        show_third_party: bool = True,
        show_stdlib: bool = True,
        show_unknown: bool = True,
        include_all: bool = False,
    ):
        self.project_path = Path(project_path)
        self.exclude_patterns = self._build_exclude_patterns(exclude_patterns, include_all)
        self.show_third_party = show_third_party
        self.show_stdlib = show_stdlib
        self.show_unknown = show_unknown
        self.include_all = include_all

    @staticmethod
    def _build_exclude_patterns(exclude_patterns: list[str] | None, include_all: bool) -> list[str]:
        user_patterns = exclude_patterns if exclude_patterns is not None else []
        if include_all:
            return list(user_patterns)
        merged = list(DEFAULT_EXCLUDE_PATTERNS)
        for pattern in user_patterns:
            if pattern not in merged:
                merged.append(pattern)
        return merged

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"project_path={self.project_path!r}, "
            f"exclude_patterns={self.exclude_patterns!r}, "
            f"show_third_party={self.show_third_party!r}, "
            f"show_stdlib={self.show_stdlib!r}, "
            f"show_unknown={self.show_unknown!r}, "
            f"include_all={self.include_all!r}"
            ")"
        )


class Config(AnalysisConfig):
    """Backward-compatible alias for older callers that still pass output settings."""

    def __init__(
        self,
        project_path: Path,
        output_file: Path | None = None,
        output_format: str = "png",
        exclude_patterns: list[str] | None = None,
        show_third_party: bool = True,
        show_stdlib: bool = True,
        show_unknown: bool = True,
        include_all: bool = False,
    ):
        super().__init__(
            project_path=project_path,
            exclude_patterns=exclude_patterns,
            show_third_party=show_third_party,
            show_stdlib=show_stdlib,
            show_unknown=show_unknown,
            include_all=include_all,
        )
        self.output_file = output_file
        self.output_format = output_format

