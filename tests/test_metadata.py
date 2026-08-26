from depcycle.parsing.metadata import PackageMetadataReader


def test_metadata_reader_pyproject(create_project):
    tmp_path = create_project({
        "pyproject.toml": '''
[project]
dependencies = [
  "requests>=2.0",
  "pandas>=2.0",
]

[dependency-groups]
lint = ["ruff>=0.6.0"]
'''.strip(),
    })

    packages = PackageMetadataReader().read(tmp_path)

    assert "requests" in packages
    assert "pandas" in packages
    assert "ruff" in packages


def test_metadata_reader_requirements(create_project):
    tmp_path = create_project({
        "requirements.txt": '''
# comment
requests>=2.0
pandas==2.2.0
pytest
'''.strip(),
    })

    packages = PackageMetadataReader().read(tmp_path)

    assert "requests" in packages
    assert "pandas" in packages
    assert "pytest" in packages
