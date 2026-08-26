"""Project metadata reader for declared third-party Python dependencies."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Set

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


class PackageMetadataReader:
    """Read dependency metadata from common Python project files."""

    def read(self, project_root: Path) -> Set[str]:
        """Return discovered third-party package base names for the project."""
        project_root = Path(project_root)
        packages: Set[str] = set()

        for path in self._candidate_files(project_root):
            if not path.exists():
                continue
            packages |= self._read_file(path)

        return packages

    def _candidate_files(self, project_root: Path) -> Iterable[Path]:
        files = [
            project_root / "pyproject.toml",
            project_root / "requirements.txt",
        ]
        files.extend(sorted(project_root.glob("requirements-*.txt")))
        files.extend(sorted(project_root.glob("*.lock")))
        files.extend([project_root / "setup.cfg", project_root / "setup.py", project_root / "Pipfile"])
        return files

    def _read_file(self, path: Path) -> Set[str]:
        name = path.name.lower()
        if name == "pyproject.toml":
            return self._read_pyproject_toml(path)
        if name == "requirements.txt" or name.startswith("requirements-"):
            return self._read_requirements_txt(path)
        if name == "setup.cfg":
            return self._read_setup_cfg(path)
        if name == "setup.py":
            return self._read_setup_py(path)
        if name.endswith(".lock"):
            return self._read_uv_lock(path)
        if name == "pipfile":
            return self._read_pipfile(path)
        return set()

    def _read_pyproject_toml(self, path: Path) -> Set[str]:
        packages: Set[str] = set()

        if tomllib is not None:
            try:
                with path.open("rb") as fh:
                    data = tomllib.load(fh)
            except (OSError, ValueError, TypeError):
                data = {}
            if isinstance(data, dict):
                project_data = data.get("project", {})
                if isinstance(project_data, dict):
                    dependencies = project_data.get("dependencies", [])
                    if isinstance(dependencies, list):
                        packages |= self._normalize_dependency_entries(dependencies)

                groups = data.get("dependency-groups", {})
                if isinstance(groups, dict):
                    for group_value in groups.values():
                        if isinstance(group_value, list):
                            packages |= self._normalize_dependency_entries(group_value)
                if packages:
                    return packages

        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return packages

        for pattern in (
            r'(?ms)^\s*\[project\]\s*.*?^\s*dependencies\s*=\s*\[(.*?)\]',
            r'(?ms)^\s*\[dependency-groups\]\s*(.*)',
        ):
            matches = re.findall(pattern, text)
            for match in matches:
                if pattern.endswith("(.*)"):
                    # dependency groups block: parse each list entry in the block
                    nested = re.findall(r'\[\s*"([^"]+)"\s*\]|\[\s*\'([^\']+)\'\s*\]|"([^"]+)"', match)
                    for candidate in nested:
                        value = next((v for v in candidate if v), "")
                        if value:
                            pkg = self._parse_requirement_name(value)
                            if pkg:
                                packages.add(pkg)
                else:
                    packages |= self._normalize_dependency_entries(re.findall(r'"([^"]+)"', match))

        return packages

    def _read_requirements_txt(self, path: Path) -> Set[str]:
        packages: Set[str] = set()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return packages

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("-r ") or line.startswith("--requirement "):
                continue
            package = self._parse_requirement_name(line)
            if package:
                packages.add(package)
        return packages

    def _read_setup_cfg(self, path: Path) -> Set[str]:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return set()

        match = re.search(r"(?ms)^\s*install_requires\s*=\s*\[(.*?)\]", content)
        if not match:
            return set()

        return self._normalize_dependency_entries(re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)))

    def _read_setup_py(self, path: Path) -> Set[str]:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return set()

        matches = re.findall(r"install_requires\s*=\s*\[(.*?)\]", content, re.S)
        packages: Set[str] = set()
        for match in matches:
            packages |= self._normalize_dependency_entries(re.findall(r"['\"]([^'\"]+)['\"]", match))
        return packages

    def _read_uv_lock(self, path: Path) -> Set[str]:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return set()

        packages: Set[str] = set()
        for match in re.finditer(r'(?ms)^\[\[package\]\]\s*\n(.*?)(?=^\[\[|\Z)', content):
            block = match.group(1)
            name_match = re.search(r'^\s*name\s*=\s*["\']([^"\']+)["\']\s*$', block, re.M)
            if name_match:
                packages.add(self._normalize_name(name_match.group(1)))
        return packages

    def _read_pipfile(self, path: Path) -> Set[str]:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return set()

        packages: Set[str] = set()
        match = re.search(r"(?ms)^\[packages\]\s*(.*?)(?=^\[|\Z)", content)
        if not match:
            return packages

        block = match.group(1)
        for name_match in re.finditer(r"^\s*['\"]?([A-Za-z0-9_.-]+)['\"]?\s*=\s*.*$", block, re.M):
            packages.add(self._normalize_name(name_match.group(1)))
        return packages

    def _normalize_dependency_entries(self, entries: Iterable[str]) -> Set[str]:
        packages: Set[str] = set()
        for entry in entries:
            package = self._parse_requirement_name(str(entry))
            if package:
                packages.add(package)
        return packages

    def _parse_requirement_name(self, requirement: str) -> str:
        requirement = requirement.strip()
        if not requirement or requirement.startswith("#"):
            return ""

        requirement = requirement.split(";", 1)[0].strip()
        requirement = requirement.split("#", 1)[0].strip()

        match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
        if not match:
            return ""
        return self._normalize_name(match.group(1))

    def _normalize_name(self, name: str) -> str:
        return name.strip().lower().replace("_", "-")


__all__ = ["PackageMetadataReader"]
