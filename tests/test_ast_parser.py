import pytest
import textwrap
from depcycle.parsing.ast_parser import ASTParser

@pytest.mark.parametrize("code,expected_imports", [
    ("import os", {"os"}),
    ("import sys as s", {"sys"}),
    ("from json import dumps", {"json.dumps"}),
    ("from os.path import join as j", {"os.path.join"}),
    ("from . import localmod", {"."}),
    ("from .pkg import submod", {".pkg"}),
    ("import os, sys", {"os", "sys"}),
    ("from .sub import *", {".sub"}),
])
def test_parser_imports(tmp_path, code, expected_imports):
    """Verify AST parser correctly identifies various import styles."""
    f = tmp_path / "module.py"
    f.write_text(code, encoding="utf-8")
    
    imports = ASTParser.get_imports_from_file(f)
    assert imports.issuperset(expected_imports)

def test_parser_handles_syntax_errors(tmp_path):
    """Resilience test: Parser should not crash on invalid Python syntax."""
    f = tmp_path / "broken.py"
    f.write_text("def broken_func( param: ", encoding="utf-8")
    
    # Should simply return empty set, not raise SyntaxError
    imports = ASTParser.get_imports_from_file(f)
    assert imports == set()