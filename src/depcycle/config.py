"""Configuration settings that control DepCycle analysis behavior."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
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


@dataclass
class AnalysisConfig:
    """Configuration that controls dependency analysis behavior."""

    project_path: Path | str
    exclude_patterns: list[str] = field(default_factory=list)
    show_third_party: bool = True
    show_stdlib: bool = True
    show_unknown: bool = True
    include_all: bool = False
    fail_on_cycles: bool = False
    targets: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize types and compute final exclusion patterns."""
        self.project_path = Path(self.project_path)
        user_patterns = self.exclude_patterns or []

        if self.include_all:
            patterns = user_patterns
        else:
            patterns = DEFAULT_EXCLUDE_PATTERNS + user_patterns

        self.exclude_patterns = list(dict.fromkeys(patterns))
        self.targets = list(self.targets or [])

    @classmethod
    def from_pyproject(
        cls,
        project_path: Path | str,
        cli_exclude: list[str] | None = None,
        cli_show_third_party: bool = True,
        cli_show_stdlib: bool = True,
        cli_show_unknown: bool = True,
        include_all: bool = False,
        fail_on_cycles: bool = False,
    ) -> AnalysisConfig:
        """Create AnalysisConfig, combining pyproject.toml [tool.depcycle] settings with CLI overrides."""
        path = Path(project_path)
        pyproject_file = path / "pyproject.toml"
        toml_cfg = {}

        if pyproject_file.is_file():
            try:
                with open(pyproject_file, "rb") as f:
                    data = tomllib.load(f)
                toml_cfg = data.get("tool", {}).get("depcycle", {})
            except (OSError, ValueError, TypeError):
                pass

        toml_exclude = toml_cfg.get("exclude", [])
        combined_exclude = list(dict.fromkeys(toml_exclude + (cli_exclude or [])))

        return cls(
            project_path=path,
            exclude_patterns=combined_exclude,
            show_third_party=cli_show_third_party
            and toml_cfg.get("show_third_party", True),
            show_stdlib=cli_show_stdlib and toml_cfg.get("show_stdlib", True),
            show_unknown=cli_show_unknown and toml_cfg.get("show_unknown", True),
            include_all=include_all,
            fail_on_cycles=fail_on_cycles or toml_cfg.get("fail_on_cycles", False),
        )
