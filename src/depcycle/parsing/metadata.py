"""Project metadata reader for third-party Python dependencies."""

from __future__ import annotations

import ast
import configparser
import importlib
import operator
import re
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = importlib.import_module("tomli")  # type: ignore[no-redef]

_NORMALIZE_PATTERN = re.compile(r"[-_.]+")
_VERSION_PART_PATTERN = re.compile(r"\d+")

_MARKER_PATTERN = re.compile(
    r"""(?P<name>python_version|python_full_version)\s*"""
    r"""(?P<operator>==|!=|<=|>=|<|>)\s*"""
    r"""['"](?P<version>[^'"]+)['"]"""
)

_EGG_PATTERN = re.compile(r"(?:#|&)egg=([A-Za-z0-9][A-Za-z0-9_.-]*)")
_EDITABLE_PATTERN = re.compile(r"^(?:-e|--editable)\s+")
_PACKAGE_NAME_PATTERN = re.compile(r"([A-Za-z0-9][A-Za-z0-9_.-]*)")

_CMP_OPS: dict[str, Callable[[tuple[int, ...], tuple[int, ...]], bool]] = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}


class PackageMetadataReader:
    """
    Read declared third-party package names from Python project metadata.

    Metadata parsing is best-effort. Invalid or unsupported metadata files
    are ignored so source-code analysis can continue without interruption.
    """

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize a Python distribution name.

        PEP 503 treats runs of `-`, `_`, and `.` as equivalent for
        distribution names. Canonical form uses `-`.
        """
        return _NORMALIZE_PATTERN.sub("-", name.strip().lower())

    @staticmethod
    def _version_tuple(version: str) -> tuple[int, ...]:
        """Convert a dotted version string into an integer tuple."""
        parts: list[int] = []
        for part in version.split("."):
            match = _VERSION_PART_PATTERN.match(part)
            if match is None:
                break
            parts.append(int(match.group()))
        return tuple(parts)

    @classmethod
    def _marker_matches_python_version(cls, marker: str) -> bool:
        """
        Return whether a simple Python-version environment marker matches.

        Supported forms include:
            python_version < '3.11'
            python_version >= "3.10"
            python_full_version < '3.11.0'

        Unsupported markers are treated as active so dependencies are not
        accidentally discarded.
        """
        match = _MARKER_PATTERN.fullmatch(marker.strip())
        if match is None:
            return True

        marker_name = match.group("name")
        op_symbol = match.group("operator")
        requested_version = cls._version_tuple(match.group("version"))

        if marker_name == "python_version":
            current_version = (sys.version_info.major, sys.version_info.minor)
        else:
            current_version = (
                sys.version_info.major,
                sys.version_info.minor,
                sys.version_info.micro,
            )

        cmp_func = _CMP_OPS.get(op_symbol)
        if cmp_func is not None:
            return cmp_func(current_version, requested_version)

        return True

    @classmethod
    def _requirement_marker_matches(cls, requirement: str) -> bool:
        """
        Return whether a requirement marker is active.

        Python-version markers are evaluated directly. Unsupported or
        complex expressions (`or` logic) are conservatively treated as active.
        """
        if ";" not in requirement:
            return True

        _, marker = requirement.split(";", 1)
        marker = marker.strip()

        if not marker or " or " in marker:
            return True

        parts = [part.strip() for part in marker.split(" and ")]
        return all(cls._marker_matches_python_version(part) for part in parts)

    @classmethod
    def _parse_requirement_name(cls, requirement: str) -> str:
        """Extract and normalize a package name from a requirement string."""
        requirement = requirement.strip()

        if not requirement or requirement.startswith("#"):
            return ""

        if not cls._requirement_marker_matches(requirement):
            return ""

        requirement = requirement.split(";", 1)[0].strip()

        egg_match = _EGG_PATTERN.search(requirement)
        if egg_match:
            return cls._normalize_name(egg_match.group(1))

        requirement = requirement.split("#", 1)[0].strip()
        requirement = _EDITABLE_PATTERN.sub("", requirement).strip()

        match = _PACKAGE_NAME_PATTERN.match(requirement)
        if match is None:
            return ""

        return cls._normalize_name(match.group(1))

    @classmethod
    def _normalize_dependency_entries(
        cls,
        entries: Iterable[str],
    ) -> set[str]:
        """Normalize a collection of dependency requirement strings."""
        packages: set[str] = set()

        for entry in entries:
            package = cls._parse_requirement_name(str(entry))
            if package:
                packages.add(package)

        return packages

    @classmethod
    def _read_pyproject_toml(cls, path: Path) -> set[str]:
        """Read runtime dependencies from pyproject.toml (PEP 621 & Poetry)."""
        try:
            with path.open("rb") as file:
                data = tomllib.load(file)
        except (OSError, ValueError, TypeError):
            return set()

        if not isinstance(data, dict):
            return set()

        packages: set[str] = set()

        project_data = data.get("project")
        if isinstance(project_data, dict):
            dependencies = project_data.get("dependencies", [])
            if isinstance(dependencies, list):
                packages |= cls._normalize_dependency_entries(dependencies)

            optional_deps = project_data.get("optional-dependencies", {})
            if isinstance(optional_deps, dict):
                for entries in optional_deps.values():
                    if isinstance(entries, list):
                        packages |= cls._normalize_dependency_entries(entries)

        tool_data = data.get("tool")
        if isinstance(tool_data, dict):
            poetry_data = tool_data.get("poetry")
            if isinstance(poetry_data, dict):
                poetry_deps = poetry_data.get("dependencies", {})
                if isinstance(poetry_deps, dict):
                    for name in poetry_deps:
                        if name.lower() != "python":
                            packages.add(cls._normalize_name(name))

                groups = poetry_data.get("group", {})
                if isinstance(groups, dict):
                    for group_data in groups.values():
                        if isinstance(group_data, dict):
                            g_deps = group_data.get("dependencies", {})
                            if isinstance(g_deps, dict):
                                for name in g_deps:
                                    packages.add(cls._normalize_name(name))

        return packages

    @classmethod
    def _read_requirements_txt(cls, path: Path) -> set[str]:
        """Read package names from a requirements-style file."""
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return set()

        packages: set[str] = set()
        ignore_prefixes = ("-r ", "--requirement ", "-c ", "--constraint ")

        for line in lines:
            line = line.strip()

            if not line or line.startswith("#") or line.startswith(ignore_prefixes):
                continue

            package = cls._parse_requirement_name(line)
            if package:
                packages.add(package)

        return packages

    @classmethod
    def _read_setup_cfg(cls, path: Path) -> set[str]:
        """Read install_requires entries from setup.cfg using standard configparser."""
        config = configparser.ConfigParser()
        try:
            config.read(path, encoding="utf-8")
        except (configparser.Error, OSError):
            return set()

        if not config.has_section("options"):
            return set()

        requires_raw = config.get("options", "install_requires", fallback="")
        return cls._normalize_dependency_entries(requires_raw.splitlines())

    @classmethod
    def _read_setup_py(cls, path: Path) -> set[str]:
        """Safely extract install_requires strings from setup.py using AST parsing."""
        try:
            content = path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (OSError, SyntaxError, UnicodeDecodeError):
            return set()

        entries: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "install_requires" and isinstance(
                        keyword.value, (ast.List, ast.Tuple, ast.Set)
                    ):
                        for elt in keyword.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(
                                elt.value, str
                            ):
                                entries.append(elt.value)

        return cls._normalize_dependency_entries(entries)

    @classmethod
    def _read_pipfile(cls, path: Path) -> set[str]:
        """Read package names from the [packages] section of a Pipfile via TOML parsing."""
        try:
            with path.open("rb") as file:
                data = tomllib.load(file)
        except (OSError, ValueError, TypeError):
            return set()

        if not isinstance(data, dict):
            return set()

        packages: set[str] = set()
        packages_data = data.get("packages")
        if isinstance(packages_data, dict):
            for name in packages_data:
                packages.add(cls._normalize_name(name))

        return packages

    @classmethod
    def _read_file(cls, path: Path) -> set[str]:
        """Read supported dependency metadata from a single file."""
        name = path.name.lower()

        if name == "pyproject.toml":
            return cls._read_pyproject_toml(path)

        if name == "requirements.txt" or name.startswith("requirements-"):
            return cls._read_requirements_txt(path)

        if name == "setup.cfg":
            return cls._read_setup_cfg(path)

        if name == "setup.py":
            return cls._read_setup_py(path)

        if name == "pipfile":
            return cls._read_pipfile(path)

        return set()

    @staticmethod
    def _candidate_files(project_root: Path) -> Iterable[Path]:
        """
        Return metadata files that may contain dependency information.

        Supported files: `pyproject.toml`, `requirements.txt`,
        `requirements-*.txt`, `setup.cfg`, `setup.py`, `Pipfile`.
        """
        files = [
            project_root / "pyproject.toml",
            project_root / "requirements.txt",
        ]

        files.extend(sorted(project_root.glob("requirements-*.txt")))

        files.extend(
            [
                project_root / "setup.cfg",
                project_root / "setup.py",
                project_root / "Pipfile",
            ]
        )

        return files

    @classmethod
    def read(cls, project_root: Path | str) -> set[str]:
        """Return discovered third-party distribution names."""
        project_root = Path(project_root)
        packages: set[str] = set()

        for path in cls._candidate_files(project_root):
            if not path.is_file():
                continue

            packages |= cls._read_file(path)

        return packages


__all__ = ["PackageMetadataReader"]
