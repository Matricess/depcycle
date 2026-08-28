"""ASTParser class for extracting imported modules from Python files."""

from __future__ import annotations

import ast
from pathlib import Path


class _ImportVisitor(ast.NodeVisitor):
    """
    Internal AST visitor for collecting imported module names.

    The visitor records module-level import targets. Imported symbols are
    ignored except for bare relative imports, where each imported name may
    itself be a local submodule.
    """

    def __init__(self) -> None:
        """Initialize the visitor with an empty imports set."""
        self.imports: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        """
        Visit an ``import`` statement.

        Examples:
            import os -> adds "os"
            import os.path -> adds "os.path"
            import os as operating_system -> adds "os"
            import os, sys -> adds "os", "sys"
        """
        for alias in node.names:
            self.imports.add(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """
        Visit a ``from ... import ...`` statement.

        For normal imports, only the module portion is recorded.

        For bare relative imports such as ``from . import localmod``,
        each imported name is recorded as a relative module candidate.

        Examples:
            from os import path -> adds "os"
            from os.path import join -> adds "os.path"
            from . import localmod -> adds ".localmod"
            from . import a, b -> adds ".a", ".b"
            from .utils import helper -> adds ".utils"
            from .. import models -> adds "..models"
            from ..models import User -> adds "..models"
            from .TimeAccount import TimeAccount -> adds ".TimeAccount"
            from .sub import * -> adds ".sub"
            from __future__ import annotations -> ignored
        """
        if node.module == "__future__":
            return

        dots = "." * node.level

        if node.module is None:
            if not dots:
                return

            for alias in node.names:
                if alias.name == "*":
                    continue

                self.imports.add(
                    f"{dots}{alias.name}",
                )

            return

        self.imports.add(
            f"{dots}{node.module}",
        )


class ASTParser:
    """
    Stateless utility for extracting imported modules from Python files.

    This class uses Python's built-in ``ast`` module to parse source code
    without executing it.
    """

    @staticmethod
    def get_imports_from_file(file_path: Path) -> set[str]:
        """
        Extract imported module names from a Python file.

        Args:
            file_path:
                Path to the Python file to parse.

        Returns:
            Set of imported module names found in the file.

        Raises:
            FileNotFoundError:
                If the file does not exist.
            UnicodeDecodeError:
                If the source cannot be decoded as UTF-8.
            SyntaxError:
                If the file contains invalid Python syntax.
        """
        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:
            content = file.read()

        tree = ast.parse(
            content,
            filename=str(file_path),
        )

        visitor = _ImportVisitor()
        visitor.visit(tree)

        return visitor.imports
