"""Project metadata reader for third-party Python dependencies."""

from __future__ import annotations

import importlib
import re
import sys
from collections.abc import Iterable
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = importlib.import_module("tomli")


class PackageMetadataReader:
    """
    Read declared third-party package names from Python project metadata.

    Metadata parsing is best-effort. Invalid or unsupported metadata files
    are ignored so source-code analysis can continue.
    """

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize a Python distribution name.

        PEP 503 treats runs of ``-``, ``_`` and ``.`` as equivalent for
        distribution names. Internally we use ``-``.
        """
        return re.sub(
            r"[-_.]+",
            "-",
            name.strip().lower(),
        )

    @staticmethod
    def _version_tuple(version: str) -> tuple[int, ...]:
        """Convert a dotted version string into an integer tuple."""
        parts: list[int] = []

        for part in version.split("."):
            match = re.match(r"\d+", part)

            if match is None:
                break

            parts.append(int(match.group()))

        return tuple(parts)

    @classmethod
    def _marker_matches_python_version(
        cls,
        marker: str,
    ) -> bool:
        """
        Return whether a simple Python-version environment marker matches.

        Supported forms include:

            python_version < '3.11'
            python_version >= "3.10"
            python_full_version < '3.11.0'

        Unsupported markers are treated as active so dependencies are not
        accidentally discarded.
        """
        marker = marker.strip()

        match = re.fullmatch(
            r"""(?P<name>python_version|python_full_version)\s*"""
            r"""(?P<operator>==|!=|<=|>=|<|>)\s*"""
            r"""['"](?P<version>[^'"]+)['"]""",
            marker,
        )

        if match is None:
            return True

        marker_name = match.group("name")
        operator = match.group("operator")
        requested_version = cls._version_tuple(
            match.group("version"),
        )

        if marker_name == "python_version":
            current_version = (
                sys.version_info.major,
                sys.version_info.minor,
            )
        else:
            current_version = (
                sys.version_info.major,
                sys.version_info.minor,
                sys.version_info.micro,
            )

        if operator == "==":
            return current_version == requested_version

        if operator == "!=":
            return current_version != requested_version

        if operator == "<":
            return current_version < requested_version

        if operator == "<=":
            return current_version <= requested_version

        if operator == ">":
            return current_version > requested_version

        if operator == ">=":
            return current_version >= requested_version

        return True

    @classmethod
    def _requirement_marker_matches(
        cls,
        requirement: str,
    ) -> bool:
        """
        Return whether a simple requirement marker is active.

        Python-version markers are evaluated directly. Unsupported or
        complex expressions are conservatively treated as active.
        """
        if ";" not in requirement:
            return True

        _, marker = requirement.split(";", 1)
        marker = marker.strip()

        if not marker:
            return True

        if " or " in marker:
            return True

        parts = [part.strip() for part in marker.split(" and ")]

        return all(cls._marker_matches_python_version(part) for part in parts)

    @classmethod
    def _parse_requirement_name(
        cls,
        requirement: str,
    ) -> str:
        """Extract and normalize a package name from a requirement string."""
        requirement = requirement.strip()

        if not requirement or requirement.startswith("#"):
            return ""

        if not cls._requirement_marker_matches(requirement):
            return ""

        requirement = requirement.split(";", 1)[0].strip()

        egg_match = re.search(
            r"(?:#|&)egg=([A-Za-z0-9][A-Za-z0-9_.-]*)",
            requirement,
        )

        if egg_match:
            return cls._normalize_name(
                egg_match.group(1),
            )

        requirement = requirement.split("#", 1)[0].strip()

        requirement = re.sub(
            r"^(?:-e|--editable)\s+",
            "",
            requirement,
        ).strip()

        match = re.match(
            r"([A-Za-z0-9][A-Za-z0-9_.-]*)",
            requirement,
        )

        if match is None:
            return ""

        return cls._normalize_name(
            match.group(1),
        )

    def _normalize_dependency_entries(
        self,
        entries: Iterable[str],
    ) -> set[str]:
        """Normalize a collection of dependency requirement strings."""
        packages: set[str] = set()

        for entry in entries:
            package = self._parse_requirement_name(
                str(entry),
            )

            if package:
                packages.add(package)

        return packages

    def _read_pyproject_toml(
        self,
        path: Path,
    ) -> set[str]:
        """Read runtime dependencies from pyproject.toml."""
        try:
            with path.open("rb") as file:
                data = tomllib.load(file)
        except (OSError, ValueError, TypeError):
            return set()

        if not isinstance(data, dict):
            return set()

        project_data = data.get("project")

        if not isinstance(project_data, dict):
            return set()

        dependencies = project_data.get(
            "dependencies",
            [],
        )

        if not isinstance(dependencies, list):
            return set()

        packages = self._normalize_dependency_entries(
            dependencies,
        )

        optional_dependencies = project_data.get(
            "optional-dependencies",
            {},
        )

        if isinstance(optional_dependencies, dict):
            for entries in optional_dependencies.values():
                if isinstance(entries, list):
                    packages |= self._normalize_dependency_entries(
                        entries,
                    )

        return packages

    def _read_requirements_txt(
        self,
        path: Path,
    ) -> set[str]:
        """Read package names from a requirements-style file."""
        try:
            lines = path.read_text(
                encoding="utf-8",
            ).splitlines()
        except OSError:
            return set()

        packages: set[str] = set()

        for line in lines:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith(
                (
                    "-r ",
                    "--requirement ",
                    "-c ",
                    "--constraint ",
                )
            ):
                continue

            package = self._parse_requirement_name(
                line,
            )

            if package:
                packages.add(package)

        return packages

    def _read_setup_cfg(
        self,
        path: Path,
    ) -> set[str]:
        """Read install_requires entries from setup.cfg."""
        try:
            content = path.read_text(
                encoding="utf-8",
            )
        except OSError:
            return set()

        section_match = re.search(
            r"(?ms)^\s*\[options\]\s*(.*?)(?=^\s*\[|\Z)",
            content,
        )

        if not section_match:
            return set()

        section = section_match.group(1)

        requires_match = re.search(
            r"(?ms)^\s*install_requires\s*=\s*"
            r"(.*?)(?=^\s*\w[\w-]*\s*=|\Z)",
            section,
        )

        if not requires_match:
            return set()

        return self._normalize_dependency_entries(
            requires_match.group(1).splitlines(),
        )

    def _read_setup_py(
        self,
        path: Path,
    ) -> set[str]:
        """Read simple install_requires lists from setup.py."""
        try:
            content = path.read_text(
                encoding="utf-8",
            )
        except OSError:
            return set()

        packages: set[str] = set()

        matches = re.findall(
            r"install_requires\s*=\s*\[(.*?)\]",
            content,
            re.DOTALL,
        )

        for match in matches:
            entries = re.findall(
                r"""['"]([^'"]+)['"]""",
                match,
            )

            packages |= self._normalize_dependency_entries(
                entries,
            )

        return packages

    def _read_pipfile(
        self,
        path: Path,
    ) -> set[str]:
        """Read package names from the [packages] section of a Pipfile."""
        try:
            content = path.read_text(
                encoding="utf-8",
            )
        except OSError:
            return set()

        packages: set[str] = set()

        match = re.search(
            r"(?ms)^\[packages\]\s*(.*?)(?=^\[|\Z)",
            content,
        )

        if not match:
            return packages

        block = match.group(1)

        for name_match in re.finditer(
            r"^\s*['\"]?([A-Za-z0-9_.-]+)['\"]?"
            r"\s*=\s*.*$",
            block,
            re.MULTILINE,
        ):
            packages.add(
                self._normalize_name(
                    name_match.group(1),
                )
            )

        return packages

    def _read_file(
        self,
        path: Path,
    ) -> set[str]:
        """Read supported dependency metadata from a single file."""
        name = path.name.lower()

        if name == "pyproject.toml":
            return self._read_pyproject_toml(path)

        if name == "requirements.txt" or name.startswith("requirements-"):
            return self._read_requirements_txt(path)

        if name == "setup.cfg":
            return self._read_setup_cfg(path)

        if name == "setup.py":
            return self._read_setup_py(path)

        if name == "pipfile":
            return self._read_pipfile(path)

        return set()

    def _candidate_files(
        self,
        project_root: Path,
    ) -> Iterable[Path]:
        """Return metadata files that may contain dependency information."""
        files = [
            project_root / "pyproject.toml",
            project_root / "requirements.txt",
        ]

        files.extend(
            sorted(
                project_root.glob("requirements-*.txt"),
            )
        )

        files.extend(
            [
                project_root / "setup.cfg",
                project_root / "setup.py",
                project_root / "Pipfile",
            ]
        )

        return files

    def read(
        self,
        project_root: Path,
    ) -> set[str]:
        """Return discovered third-party distribution names."""
        project_root = Path(project_root)
        packages: set[str] = set()

        for path in self._candidate_files(project_root):
            if not path.is_file():
                continue

            packages |= self._read_file(path)

        return packages


__all__ = ["PackageMetadataReader"]
