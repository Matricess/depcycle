import sys
from pathlib import Path

import pytest

# Ensure src/ is in the python path so imports work without installation
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

@pytest.fixture
def create_project(tmp_path):
    """
    Factory fixture to create a temporary project structure.
    
    Usage:
        create_project({
            "main.py": "import os",
            "pkg/module.py": "x = 1"
        })
    """
    def _write(files_dict):
        for rel_path, content in files_dict.items():
            p = tmp_path / rel_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        return tmp_path
    return _write
