"""Tests for project dependency metadata parsing."""

from pathlib import Path

from depcycle.parsing.metadata import PackageMetadataReader


def write_file(
    tmp_path: Path,
    name: str,
    content: str,
) -> Path:
    """Create a metadata file in the temporary project root."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_normalize_name() -> None:
    """Normalize equivalent Python distribution names."""
    reader = PackageMetadataReader()

    assert reader._normalize_name("Requests") == "requests"
    assert reader._normalize_name("my_package") == "my-package"
    assert reader._normalize_name("my.package") == "my-package"
    assert reader._normalize_name("my-package") == "my-package"


def test_parse_requirement_name() -> None:
    """Extract package names from common requirement forms."""
    reader = PackageMetadataReader()

    assert reader._parse_requirement_name("requests>=2.0") == "requests"
    assert reader._parse_requirement_name("requests==2.31.0") == "requests"
    assert reader._parse_requirement_name("my_package>=1.0") == "my-package"
    assert reader._parse_requirement_name("  flask  ") == "flask"


def test_parse_requirement_ignores_comments() -> None:
    """Ignore empty and commented requirement lines."""
    reader = PackageMetadataReader()

    assert reader._parse_requirement_name("") == ""
    assert reader._parse_requirement_name("# requests") == ""


def test_parse_requirement_handles_inline_comments() -> None:
    """Ignore comments after a requirement."""
    reader = PackageMetadataReader()

    assert reader._parse_requirement_name("requests>=2.0  # HTTP client") == "requests"


def test_parse_requirement_handles_environment_marker() -> None:
    """Parse requirements with active Python-version markers."""
    reader = PackageMetadataReader()

    assert (
        reader._parse_requirement_name("requests>=2.0; python_version >= '3.10'")
        == "requests"
    )


def test_parse_requirement_ignores_inactive_python_marker(
    monkeypatch,
) -> None:
    """Skip requirements whose Python-version marker is inactive."""
    reader = PackageMetadataReader()

    class FakeVersionInfo:
        """Minimal replacement for sys.version_info."""

        major = 3
        minor = 10
        micro = 0

    monkeypatch.setattr(
        "depcycle.parsing.metadata.sys.version_info",
        FakeVersionInfo,
    )

    assert (
        reader._parse_requirement_name("requests>=2.0; python_version >= '3.11'") == ""
    )


def test_parse_requirement_keeps_unsupported_marker_active() -> None:
    """Keep complex unsupported markers instead of dropping dependencies."""
    reader = PackageMetadataReader()

    assert (
        reader._parse_requirement_name("requests>=2.0; platform_system == 'Darwin'")
        == "requests"
    )


def test_parse_editable_requirement_with_egg_name() -> None:
    """Extract package names from editable VCS requirements."""
    reader = PackageMetadataReader()

    requirement = "-e git+https://github.com/example/project.git#egg=project"

    assert reader._parse_requirement_name(requirement) == "project"


def test_normalize_dependency_entries() -> None:
    """Normalize a collection of dependency strings."""
    reader = PackageMetadataReader()

    entries = [
        "Requests>=2.0",
        "my_package",
        "",
        "# comment",
    ]

    assert reader._normalize_dependency_entries(entries) == {
        "requests",
        "my-package",
    }


def test_read_pyproject_runtime_dependencies(
    tmp_path: Path,
) -> None:
    """Read runtime and optional dependencies from pyproject.toml."""
    path = write_file(
        tmp_path,
        "pyproject.toml",
        """
[project]
dependencies = [
    "requests>=2.0",
    "my-package==1.0",
]

[project.optional-dependencies]
test = [
    "pytest>=9.0",
]
""",
    )

    reader = PackageMetadataReader()

    assert reader._read_pyproject_toml(path) == {
        "requests",
        "my-package",
        "pytest",
    }


def test_read_pyproject_without_project_table(
    tmp_path: Path,
) -> None:
    """Return an empty set when pyproject lacks project metadata."""
    path = write_file(
        tmp_path,
        "pyproject.toml",
        """
[tool.ruff]
target-version = "py310"
""",
    )

    reader = PackageMetadataReader()

    assert reader._read_pyproject_toml(path) == set()


def test_read_requirements_txt(
    tmp_path: Path,
) -> None:
    """Read standard requirements files."""
    path = write_file(
        tmp_path,
        "requirements.txt",
        """
requests>=2.0
flask==3.0.0
# comment
-r base.txt
-c constraints.txt
""",
    )

    reader = PackageMetadataReader()

    assert reader._read_requirements_txt(path) == {
        "requests",
        "flask",
    }


def test_read_requirements_variant_file(
    tmp_path: Path,
) -> None:
    """Read requirements-dev style files."""
    path = write_file(
        tmp_path,
        "requirements-dev.txt",
        """
pytest>=9.0
ruff>=0.11
""",
    )

    reader = PackageMetadataReader()

    assert reader._read_file(path) == {
        "pytest",
        "ruff",
    }


def test_read_setup_cfg(
    tmp_path: Path,
) -> None:
    """Read install_requires from setup.cfg."""
    path = write_file(
        tmp_path,
        "setup.cfg",
        """
[metadata]
name = example

[options]
install_requires =
    requests>=2.0
    flask
python_requires = >=3.10
""",
    )

    reader = PackageMetadataReader()

    assert reader._read_setup_cfg(path) == {
        "requests",
        "flask",
    }


def test_read_setup_py(
    tmp_path: Path,
) -> None:
    """Read simple install_requires lists from setup.py."""
    path = write_file(
        tmp_path,
        "setup.py",
        """
from setuptools import setup

setup(
    name="example",
    install_requires=[
        "requests>=2.0",
        "flask",
    ],
)
""",
    )

    reader = PackageMetadataReader()

    assert reader._read_setup_py(path) == {
        "requests",
        "flask",
    }


def test_read_pipfile(
    tmp_path: Path,
) -> None:
    """Read packages from Pipfile."""
    path = write_file(
        tmp_path,
        "Pipfile",
        """
[packages]
requests = "*"
flask = ">=3.0"

[dev-packages]
pytest = "*"
""",
    )

    reader = PackageMetadataReader()

    assert reader._read_pipfile(path) == {
        "requests",
        "flask",
    }


def test_candidate_files(
    tmp_path: Path,
) -> None:
    """Discover supported metadata file names."""
    write_file(
        tmp_path,
        "pyproject.toml",
        "",
    )
    write_file(
        tmp_path,
        "requirements.txt",
        "",
    )
    write_file(
        tmp_path,
        "requirements-dev.txt",
        "",
    )
    write_file(
        tmp_path,
        "setup.cfg",
        "",
    )
    write_file(
        tmp_path,
        "setup.py",
        "",
    )
    write_file(
        tmp_path,
        "Pipfile",
        "",
    )

    reader = PackageMetadataReader()

    names = {path.name for path in reader._candidate_files(tmp_path)}

    assert names == {
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
        "setup.cfg",
        "setup.py",
        "Pipfile",
    }


def test_read_combines_supported_files(
    tmp_path: Path,
) -> None:
    """Combine dependencies discovered across supported metadata files."""
    write_file(
        tmp_path,
        "pyproject.toml",
        """
[project]
dependencies = [
    "requests>=2.0",
]
""",
    )

    write_file(
        tmp_path,
        "requirements-extra.txt",
        """
flask>=3.0
""",
    )

    write_file(
        tmp_path,
        "Pipfile",
        """
[packages]
click = "*"
""",
    )

    reader = PackageMetadataReader()

    assert reader.read(tmp_path) == {
        "requests",
        "flask",
        "click",
    }


def test_missing_metadata_files_are_ignored(
    tmp_path: Path,
) -> None:
    """Return an empty set when no supported metadata exists."""
    reader = PackageMetadataReader()

    assert reader.read(tmp_path) == set()


def test_invalid_pyproject_is_ignored(
    tmp_path: Path,
) -> None:
    """Ignore malformed TOML without raising."""
    path = write_file(
        tmp_path,
        "pyproject.toml",
        """
[project
dependencies = [
    "requests",
]
""",
    )

    reader = PackageMetadataReader()

    assert reader._read_pyproject_toml(path) == set()


def test_python_full_version_marker() -> None:
    """Evaluate python_full_version markers using the runtime version."""
    reader = PackageMetadataReader()

    assert reader._marker_matches_python_version("python_full_version >= '3.0.0'")


def test_simple_and_marker() -> None:
    """Evaluate simple AND combinations of Python-version markers."""
    reader = PackageMetadataReader()

    assert reader._requirement_marker_matches(
        "requests; python_version >= '3.10' and python_full_version >= '3.10.0'"
    )


def test_or_marker_is_conservatively_active() -> None:
    """Keep unsupported OR marker expressions active."""
    reader = PackageMetadataReader()

    assert reader._requirement_marker_matches(
        "requests; python_version < '3.10' or platform_system == 'Darwin'"
    )
