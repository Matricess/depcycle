"""DependencyGraph class representing the core graph data structure."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from .node import ModuleNode, ModuleType


def _stdlib_module_names() -> set[str]:
    """Return Python stdlib module names available on this runtime."""
    stdlib_names = getattr(sys, "stdlib_module_names", None)

    if stdlib_names is not None:
        return set(stdlib_names)

    fallback = {
        "abc",
        "argparse",
        "ast",
        "asyncio",
        "base64",
        "binascii",
        "calendar",
        "codecs",
        "collections",
        "configparser",
        "copy",
        "csv",
        "dataclasses",
        "datetime",
        "difflib",
        "dis",
        "doctest",
        "email",
        "enum",
        "fnmatch",
        "functools",
        "gc",
        "getopt",
        "glob",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "importlib",
        "inspect",
        "io",
        "itertools",
        "json",
        "keyword",
        "linecache",
        "locale",
        "logging",
        "math",
        "mimetypes",
        "multiprocessing",
        "operator",
        "os",
        "pathlib",
        "pickle",
        "platform",
        "pprint",
        "queue",
        "random",
        "re",
        "secrets",
        "selectors",
        "shlex",
        "shutil",
        "signal",
        "socket",
        "sqlite3",
        "statistics",
        "string",
        "struct",
        "subprocess",
        "sys",
        "tarfile",
        "tempfile",
        "textwrap",
        "threading",
        "time",
        "traceback",
        "typing",
        "unittest",
        "urllib",
        "uuid",
        "warnings",
        "wave",
        "weakref",
        "xml",
        "zipfile",
        "zlib",
    }

    return fallback


class DependencyGraph:
    """
    Central data structure holding the dependency graph.

    The graph uses a fully qualified module name as each node's identity.
    Local modules are discovered from source files, imports are resolved to
    local modules when possible, and unresolved imports become external nodes.
    """

    def __init__(self) -> None:
        """Initialize an empty dependency graph."""
        self.nodes: dict[str, ModuleNode] = {}
        self._project_root: Path | None = None
        self._known_stdlib: set[str] = _stdlib_module_names()
        self._known_third_party: set[str] = set()

    @staticmethod
    def _normalize_distribution_name(name: str) -> str:
        """
        Normalize a distribution or import name for classification.

        Distribution metadata treats runs of ``-``, ``_`` and ``.`` as
        equivalent. Python import names may use underscores, so normalize
        both forms to the same comparison key.
        """
        return re.sub(
            r"[-_.]+",
            "-",
            name.strip().lower(),
        )

    def _create_module_node(
        self,
        file_path: Path,
        project_root: Path,
    ) -> ModuleNode:
        """
        Create a local ModuleNode from a Python file path.

        Supports both common layouts:

            project/
                package/
                    module.py

            project/
                src/
                    package/
                        module.py

        For a ``src/`` layout, ``src`` is treated as the source root rather
        than part of the Python module name.
        """
        relative_path = file_path.relative_to(project_root)
        parts = relative_path.parts

        if parts and parts[0] == "src" and (project_root / "src").is_dir():
            module_parts = parts[1:]
        else:
            module_parts = parts

        module_path = Path(*module_parts).with_suffix("")

        if module_path.name == "__init__":
            module_name = ".".join(module_path.parent.parts)
        else:
            module_name = ".".join(module_path.parts)

        return ModuleNode(
            name=module_name,
            file_path=file_path,
            module_type=ModuleType.LOCAL,
        )

    def _is_package_node(self, module_name: str) -> bool:
        """Return True when a local module represents an __init__.py file."""
        node = self.nodes.get(module_name)

        if node is None or node.file_path is None:
            return False

        return node.file_path.name == "__init__.py"

    def _resolve_relative_import(
        self,
        relative_str: str,
        current_module: str,
    ) -> str:
        """
        Convert a relative import reference into an absolute module name.

        Examples:
            x.y.z + .utils
                -> x.y.utils

            x.y.z + ..utils
                -> x.utils

            x.y (__init__.py) + .utils
                -> x.y.utils

            pkg.a + .b
                -> pkg.b
        """
        dots = 0

        while dots < len(relative_str) and relative_str[dots] == ".":
            dots += 1

        if dots == 0:
            return relative_str

        remaining = relative_str[dots:]
        current_parts = current_module.split(".")

        if self._is_package_node(current_module):
            package_parts = current_parts
        else:
            package_parts = current_parts[:-1]

        levels_up = dots - 1

        if levels_up > len(package_parts):
            return relative_str

        if levels_up:
            base_parts = package_parts[:-levels_up]
        else:
            base_parts = package_parts

        if remaining:
            base_parts.append(remaining)

        return ".".join(base_parts)

    @staticmethod
    def _get_import_variants(import_str: str) -> list[str]:
        """
        Return progressively shorter module-name variants.

        Example:
            foo.bar.Baz
                -> foo.bar.Baz
                -> foo.bar
                -> foo
        """
        if not import_str:
            return []

        parts = import_str.split(".")
        variants = [import_str]

        for index in range(len(parts) - 1, 0, -1):
            candidate = ".".join(parts[:index])

            if candidate not in variants:
                variants.append(candidate)

        return variants

    def _resolve_import(
        self,
        import_str: str,
        current_module: str,
    ) -> ModuleNode | None:
        """
        Resolve an import reference to the best matching local module.
        """
        if import_str.startswith("."):
            absolute_name = self._resolve_relative_import(
                import_str,
                current_module,
            )
            candidates = self._get_import_variants(absolute_name)
        else:
            candidates = self._get_import_variants(import_str)

        for candidate in candidates:
            dependency = self.nodes.get(candidate)

            if dependency is not None:
                return dependency

        return None

    def resolve(self) -> DependencyGraph:
        """
        Resolve raw imports and attach dependency nodes.

        Each raw import produces at most one dependency edge.
        """
        for node in list(self.nodes.values()):
            if node.module_type != ModuleType.LOCAL:
                continue

            node.dependencies = set()

            for import_str in sorted(node.raw_imports):
                dependency_node = self._resolve_import(
                    import_str,
                    node.name,
                )

                if dependency_node is None:
                    if import_str.startswith("."):
                        continue

                    dependency_node = ModuleNode(
                        name=import_str,
                        file_path=None,
                        module_type=ModuleType.UNKNOWN,
                    )

                    self.add_node(dependency_node)

                node.dependencies.add(dependency_node)

        return self

    def build(
        self,
        files: list[Path],
        project_root: Path,
        parser,
    ) -> DependencyGraph:
        """Build and resolve a dependency graph from Python source files."""
        project_root = Path(project_root).resolve()

        if not hasattr(parser, "get_imports_from_file"):
            raise TypeError(
                "A parser with get_imports_from_file() is required for graph builds."
            )

        self._project_root = project_root
        self.nodes.clear()

        for file_path in sorted(Path(path) for path in files):
            if not file_path.is_file():
                continue

            node = self._create_module_node(
                file_path,
                project_root,
            )

            self.nodes[node.name] = node
            node.raw_imports = parser.get_imports_from_file(
                file_path,
            )

        return self.resolve()

    def classify(
        self,
        known_stdlib: set[str] | None = None,
        known_third_party: set[str] | None = None,
    ) -> DependencyGraph:
        """Classify each non-local node as stdlib, third-party, or unknown."""
        if known_stdlib is not None:
            self._known_stdlib = set(known_stdlib) or _stdlib_module_names()

        if known_third_party is not None:
            self._known_third_party = {
                self._normalize_distribution_name(name) for name in known_third_party
            }

        for node in self.nodes.values():
            if node.module_type == ModuleType.LOCAL:
                continue

            module_base = node.name.split(".")[0]
            normalized_base = self._normalize_distribution_name(
                module_base,
            )

            if node.name in self._known_stdlib or module_base in self._known_stdlib:
                node.module_type = ModuleType.STDLIB

            elif (
                self._normalize_distribution_name(node.name) in self._known_third_party
                or normalized_base in self._known_third_party
            ):
                node.module_type = ModuleType.THIRD_PARTY

            elif self._known_third_party:
                node.module_type = ModuleType.UNKNOWN

            else:
                node.module_type = ModuleType.THIRD_PARTY

        return self

    def filter(
        self,
        show_stdlib: bool = True,
        show_third_party: bool = True,
        show_unknown: bool = True,
    ) -> DependencyGraph:
        """Filter nodes by category while preserving local modules."""
        if show_stdlib and show_third_party and show_unknown:
            return self

        keep_modules: set[str] = set()

        for node in self.nodes.values():
            if node.module_type == ModuleType.LOCAL or (
                (node.module_type == ModuleType.THIRD_PARTY and show_third_party)
                or (node.module_type == ModuleType.STDLIB and show_stdlib)
                or (node.module_type == ModuleType.UNKNOWN and show_unknown)
            ):
                keep_modules.add(node.name)

        filtered_out = set(self.nodes) - keep_modules

        for module_name in filtered_out:
            del self.nodes[module_name]

        for node in self.nodes.values():
            node.dependencies = {
                dependency
                for dependency in node.dependencies
                if dependency.name in self.nodes
            }

        return self

    def add_node(self, node: ModuleNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.name] = node

    def find_cycles(self) -> list[list[ModuleNode]]:
        """
        Detect circular dependencies using depth-first search.

        Returns:
            A list of dependency cycles encountered during DFS.
        """
        cycles: list[list[ModuleNode]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[ModuleNode] = []

        def dfs(node: ModuleNode) -> None:
            """Recursively visit dependencies and detect back edges."""
            visited.add(node.name)
            rec_stack.add(node.name)
            path.append(node)

            dependencies = sorted(
                node.dependencies,
                key=lambda dependency: dependency.name,
            )

            for dependency in dependencies:
                if dependency.name not in visited:
                    dfs(dependency)

                elif dependency.name in rec_stack:
                    cycle_start = next(
                        index
                        for index, path_node in enumerate(path)
                        if path_node.name == dependency.name
                    )

                    cycles.append(
                        path[cycle_start:] + [dependency],
                    )

            rec_stack.remove(node.name)
            path.pop()

        for node in sorted(
            self.nodes.values(),
            key=lambda item: item.name,
        ):
            if node.name not in visited:
                dfs(node)

        return cycles

    def __repr__(self) -> str:
        """Provide a developer-friendly representation."""
        return f"DependencyGraph(nodes={len(self.nodes)})"

    def __len__(self) -> int:
        """Return the number of nodes in the graph."""

        return len(self.nodes)

    def __iter__(self):
        """Allow iteration over graph nodes."""
        return iter(self.nodes.values())
