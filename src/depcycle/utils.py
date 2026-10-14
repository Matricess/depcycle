"""Utility functions for module name normalization and standard library inspection."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def get_stdlib_names() -> set[str]:
    """Retrieve standard library module names available on the current runtime."""
    stdlib_names = getattr(sys, "stdlib_module_names", None)
    if stdlib_names is not None:
        return set(stdlib_names)

    return {
        "os",
        "sys",
        "pathlib",
        "json",
        "ast",
        "re",
        "math",
        "collections",
        "itertools",
        "functools",
        "typing",
        "dataclasses",
        "enum",
        "logging",
    }


def normalize_name(name: str) -> str:
    """Normalize package or import name by treating -, _, and . as equivalent."""
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def path_to_module_name(file_path: Path, root_path: Path) -> str | None:
    """
    Convert a file path relative to the root directory into a Python module path.

    Args:
        file_path: Absolute or relative path to the target Python file.
        root_path: Root path of the workspace.

    Returns:
        Dot-separated module string (e.g., 'parsing.imports'), or None if outside root.
    """
    try:
        rel_path = Path(file_path).resolve().relative_to(Path(root_path).resolve())
    except ValueError:
        return None

    parts = list(rel_path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()

    return ".".join(parts) if parts else None


def resolve_relative_import(
    import_name: str,
    source_module: str,
    *,
    is_package: bool = False,
) -> str | None:
    """Resolve a relative import to its fully qualified module name."""
    if not import_name.startswith("."):
        return import_name

    level = len(import_name) - len(import_name.lstrip("."))
    imported_module = import_name[level:]

    package_name = source_module if is_package else source_module.rpartition(".")[0]
    package_parts = package_name.split(".") if package_name else []

    ascend = level - 1

    if not package_parts or ascend >= len(package_parts):
        return None

    if ascend:
        package_parts = package_parts[:-ascend]

    if imported_module:
        package_parts.extend(imported_module.split("."))

    return ".".join(package_parts) or None
