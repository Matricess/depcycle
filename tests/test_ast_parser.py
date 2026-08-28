"""Tests for AST-based import extraction."""

from pathlib import Path

import pytest

from depcycle.parsing.ast_parser import ASTParser


def write_source(tmp_path: Path, source: str) -> Path:
    """Write Python source to a temporary file."""
    file_path = tmp_path / "module.py"
    file_path.write_text(source, encoding="utf-8")
    return file_path


def test_import_statements(tmp_path: Path) -> None:
    """Extract modules from regular import statements."""
    file_path = write_source(
        tmp_path,
        """
import os
import os.path
import sys
import json as json_module
""",
    )

    imports = ASTParser.get_imports_from_file(file_path)

    assert imports == {
        "os",
        "os.path",
        "sys",
        "json",
    }


def test_from_import_statements(tmp_path: Path) -> None:
    """Extract module targets from from-import statements."""
    file_path = write_source(
        tmp_path,
        """
from os import path
from os.path import join
from pathlib import Path
""",
    )

    imports = ASTParser.get_imports_from_file(file_path)

    assert imports == {
        "os",
        "os.path",
        "pathlib",
    }


def test_relative_imports(tmp_path: Path) -> None:
    """Extract relative module targets."""
    file_path = write_source(
        tmp_path,
        """
from .utils import helper
from ..models import User
from ...common import value
""",
    )

    imports = ASTParser.get_imports_from_file(file_path)

    assert imports == {
        ".utils",
        "..models",
        "...common",
    }


def test_bare_relative_imports(tmp_path: Path) -> None:
    """Preserve imported names from bare relative imports."""
    file_path = write_source(
        tmp_path,
        """
from . import localmod
from . import first, second
from .. import models
""",
    )

    imports = ASTParser.get_imports_from_file(file_path)

    assert imports == {
        ".localmod",
        ".first",
        ".second",
        "..models",
    }


def test_relative_wildcard_import(tmp_path: Path) -> None:
    """Ignore wildcard names from bare relative imports."""
    file_path = write_source(
        tmp_path,
        """
from . import *
from .sub import *
""",
    )

    imports = ASTParser.get_imports_from_file(file_path)

    assert imports == {
        ".sub",
    }


def test_future_imports_are_ignored(tmp_path: Path) -> None:
    """Ignore __future__ imports."""
    file_path = write_source(
        tmp_path,
        """
from __future__ import annotations
import pathlib
""",
    )

    imports = ASTParser.get_imports_from_file(file_path)

    assert imports == {
        "pathlib",
    }


def test_duplicate_imports_are_deduplicated(
    tmp_path: Path,
) -> None:
    """Return each module only once."""
    file_path = write_source(
        tmp_path,
        """
import os
import os
from os import path
from os import getcwd
""",
    )

    imports = ASTParser.get_imports_from_file(file_path)

    assert imports == {"os"}


def test_invalid_python_raises_syntax_error(
    tmp_path: Path,
) -> None:
    """Reject syntactically invalid Python."""
    file_path = write_source(
        tmp_path,
        """
def broken(
""",
    )

    with pytest.raises(SyntaxError):
        ASTParser.get_imports_from_file(file_path)


def test_missing_file_raises_file_not_found(
    tmp_path: Path,
) -> None:
    """Raise FileNotFoundError for missing files."""
    file_path = tmp_path / "missing.py"

    with pytest.raises(FileNotFoundError):
        ASTParser.get_imports_from_file(file_path)
