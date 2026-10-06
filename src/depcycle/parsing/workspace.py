"""Workspace discovery and exclusion filtering for Python source files."""

from __future__ import annotations

import fnmatch
from collections.abc import Sequence
from pathlib import Path


class Workspace:
    """
    Represent a local code workspace being analyzed.

    Responsible for discovering Python source files and applying caller-supplied
    exclusion patterns.
    """

    def __init__(self, root_path: Path | str) -> None:
        """
        Initialize a Workspace instance.

        Args:
            root_path: Path to the workspace root directory.

        Raises:
            ValueError: If the path does not exist or is not a directory.
        """
        self.root_path = Path(root_path).resolve()

        if not self.root_path.exists():
            raise ValueError(f"Workspace path does not exist: {root_path}")
        if not self.root_path.is_dir():
            raise ValueError(f"Workspace path is not a directory: {root_path}")

    def _should_exclude(self, file_path: Path, patterns: Sequence[str]) -> bool:
        """
        Return whether a file path matches any exclusion pattern.

        Patterns may match:
            - The file name
            - The complete path relative to the workspace root
            - Any individual directory or file name component in the relative path
        """
        try:
            relative_path = file_path.relative_to(self.root_path)
        except ValueError:
            return True

        relative_path_str = relative_path.as_posix()

        for pattern in patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
            if fnmatch.fnmatch(relative_path_str, pattern):
                return True
            if any(fnmatch.fnmatch(part, pattern) for part in relative_path.parts):
                return True

        return False

    def get_python_files(
        self, exclude_patterns: Sequence[str] | None = None
    ) -> list[Path]:
        """
        Discover all valid Python files in the workspace.

        Args:
            exclude_patterns: Glob patterns supplied to exclude files or directories.

        Returns:
            Sorted list of absolute paths to discovered Python files.
        """
        patterns = list(dict.fromkeys(exclude_patterns or []))

        python_files = [
            py_file
            for py_file in self.root_path.rglob("*.py")
            if not self._should_exclude(py_file, patterns)
        ]

        return sorted(python_files)
