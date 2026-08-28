"""Project class for discovering and managing Python files in a project."""

from __future__ import annotations

import fnmatch
from pathlib import Path


class Project:
    """
    Represent a Python project being analyzed.

    This class is responsible only for discovering Python files and applying
    the exclusion patterns supplied by the caller.
    """

    def __init__(self, root_path: Path | str) -> None:
        """
        Initialize a Project instance.

        Args:
            root_path:
                Path to the project root directory.

        Raises:
            ValueError:
                If the project path does not exist or is not a directory.
        """
        self.root_path = Path(root_path).resolve()

        if not self.root_path.exists():
            raise ValueError(f"Project path does not exist: {root_path}")

        if not self.root_path.is_dir():
            raise ValueError(f"Project path is not a directory: {root_path}")

    def _should_exclude(
        self,
        file_path: Path,
        patterns: list[str],
    ) -> bool:
        """
        Return whether a file matches any exclusion pattern.

        Patterns may match:

        - the file name,
        - the complete path relative to the project root,
        - any individual directory or file name in that relative path.
        """
        try:
            relative_path = file_path.relative_to(
                self.root_path,
            )
        except ValueError:
            return True

        relative_path_str = relative_path.as_posix()

        for pattern in patterns:
            if fnmatch.fnmatch(
                file_path.name,
                pattern,
            ):
                return True

            if fnmatch.fnmatch(
                relative_path_str,
                pattern,
            ):
                return True

            if any(
                fnmatch.fnmatch(
                    part,
                    pattern,
                )
                for part in relative_path.parts
            ):
                return True

        return False

    def get_python_files(
        self,
        exclude_patterns: list[str] | None = None,
    ) -> list[Path]:
        """
        Discover Python files in the project.

        Args:
            exclude_patterns:
                Glob patterns supplied by the caller to exclude files or
                directories.

        Returns:
            Sorted list of absolute paths to discovered Python files.
        """
        patterns = list(
            dict.fromkeys(
                exclude_patterns or [],
            )
        )

        python_files = [
            py_file
            for py_file in self.root_path.rglob("*.py")
            if not self._should_exclude(
                py_file,
                patterns,
            )
        ]

        return sorted(python_files)
