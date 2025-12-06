from depcycle.parsing.project import Project

def test_project_discovers_python_files_with_default_excludes(create_project):
    """Verify venv and node_modules are ignored by default."""
    tmp_path = create_project({
        "pkg/a.py": "import sys",
        "pkg/b.py": "from . import a",
        "venv/fake.py": "import nothing",      
        "node_modules/noop.py": "x = 1"        
    })

    project = Project(tmp_path)
    # Also test explicit exclude of specific file
    files = project.get_python_files(exclude_patterns=["pkg/b.py"])

    names = {f.name for f in files}
    assert names == {"a.py"}
    assert "fake.py" not in names

def test_project_can_opt_out_of_default_excludes(create_project):
    """Verify defaults can be overridden."""
    tmp_path = create_project({
        "venv/fake.py": "x = 1"
    })

    project = Project(tmp_path)
    files = project.get_python_files(include_defaults=False)

    assert {f.name for f in files} == {"fake.py"}