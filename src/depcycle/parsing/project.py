"""Project class for discovering and managing Python files in a project."""

from __future__ import annotations

import fnmatch
from pathlib import Path


class Project:
    """
    Represents a Python project being analyzed.

    This class is responsible for discovering all Python files in a project
    directory, respecting exclusion patterns.

    Attributes:
        root_path (Path): The absolute path to the project root directory.
    """

    def __init__(self, root_path: Path):
        """
        Initialize a Project instance.

        Args:
            root_path: Path to the project root directory.
        """
        self.root_path = Path(root_path).resolve()
        if not self.root_path.exists():
            raise ValueError(f"Project path does not exist: {root_path}")
        if not self.root_path.is_dir():
            raise ValueError(f"Project path is not a directory: {root_path}")

    def get_python_files(
        self,
        exclude_patterns: list[str] | None = None,
        include_defaults: bool = True,
    ) -> list[Path]:
        """
        Discover all Python files in the project.

        Recursively scans the project directory for .py files, excluding
        directories and files that match any of the provided patterns.

        Args:
            exclude_patterns: Custom glob patterns to exclude (e.g., ['venv', '*.test.py']).
                              Patterns can match file or directory names.
            include_defaults: When True (default) also excludes common virtualenv,
                              cache, and VCS directories that should never be parsed.

        Returns:
            List of absolute Path objects for each Python file found.
        """
        exclude_patterns = exclude_patterns or []
        if include_defaults:
            default_excludes = [
                "venv",
                ".venv",
                "env",
                ".env",
                "__pycache__",
                ".git",
                "site-packages",
                "node_modules",
                "dist",
                "build",
                ".mypy_cache",
                ".pytest_cache",
            ]
            exclude_patterns = list(dict.fromkeys(default_excludes + exclude_patterns))
        python_files: list[Path] = []

        for py_file in self.root_path.rglob("*.py"):
            if self._should_exclude(py_file, exclude_patterns):
                continue
            python_files.append(py_file)

        return python_files

    def _should_exclude(self, file_path: Path, patterns: list[str]) -> bool:
        """
        Check if a file should be excluded based on patterns.

        Args:
            file_path: The file path to check.
            patterns: List of glob patterns.

        Returns:
            True if the file should be excluded, False otherwise.
        """
        try:
            relative_path = file_path.relative_to(self.root_path)
        except ValueError:
            return True

        for pattern in patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True

            if fnmatch.fnmatch(str(relative_path).replace("\\", "/"), pattern):
                return True

            for part in relative_path.parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

        return False

