"""Tests for Python project file discovery."""

from pathlib import Path

import pytest

from depcycle.parsing.project import Project


def write_file(
    root: Path,
    relative_path: str,
    content: str = "",
) -> Path:
    """Create a file beneath the temporary project root."""
    file_path = root / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_project_requires_existing_directory(tmp_path: Path) -> None:
    """Reject missing project paths."""
    missing = tmp_path / "missing"

    with pytest.raises(
        ValueError,
        match="Project path does not exist",
    ):
        Project(missing)


def test_project_requires_directory(tmp_path: Path) -> None:
    """Reject a regular file as the project root."""
    file_path = tmp_path / "project.py"
    file_path.write_text("", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Project path is not a directory",
    ):
        Project(file_path)


def test_project_root_is_absolute(tmp_path: Path) -> None:
    """Store the resolved project root."""
    project = Project(tmp_path)

    assert project.root_path.is_absolute()
    assert project.root_path == tmp_path.resolve()


def test_discovers_python_files_recursively(tmp_path: Path) -> None:
    """Discover Python files throughout nested directories."""
    write_file(tmp_path, "main.py")
    write_file(tmp_path, "package/module.py")
    write_file(tmp_path, "package/subpackage/other.py")
    write_file(tmp_path, "README.md")

    project = Project(tmp_path)

    files = project.get_python_files()

    assert files == sorted(
        [
            (tmp_path / "main.py").resolve(),
            (tmp_path / "package/module.py").resolve(),
            (tmp_path / "package/subpackage/other.py").resolve(),
        ]
    )


def test_results_are_sorted(tmp_path: Path) -> None:
    """Return discovered Python files in deterministic order."""
    write_file(tmp_path, "z.py")
    write_file(tmp_path, "a.py")
    write_file(tmp_path, "m/b.py")
    write_file(tmp_path, "m/a.py")

    project = Project(tmp_path)

    files = project.get_python_files()

    assert files == sorted(files)


def test_excludes_matching_file_name(tmp_path: Path) -> None:
    """Exclude files whose names match a supplied pattern."""
    write_file(tmp_path, "main.py")
    write_file(tmp_path, "test.py")
    write_file(tmp_path, "package/test.py")

    project = Project(tmp_path)

    files = project.get_python_files(
        exclude_patterns=["test.py"],
    )

    assert files == [
        (tmp_path / "main.py").resolve(),
    ]


def test_excludes_matching_directory_name(tmp_path: Path) -> None:
    """Exclude Python files beneath a matching directory."""
    write_file(tmp_path, "main.py")
    write_file(tmp_path, "tests/test_module.py")
    write_file(tmp_path, "tests/nested/helper.py")
    write_file(tmp_path, "src/app.py")

    project = Project(tmp_path)

    files = project.get_python_files(
        exclude_patterns=["tests"],
    )

    assert files == [
        (tmp_path / "main.py").resolve(),
        (tmp_path / "src/app.py").resolve(),
    ]


def test_excludes_matching_relative_path(tmp_path: Path) -> None:
    """Exclude a specific relative path pattern."""
    write_file(tmp_path, "package/a.py")
    write_file(tmp_path, "package/b.py")
    write_file(tmp_path, "other/a.py")

    project = Project(tmp_path)

    files = project.get_python_files(
        exclude_patterns=["package/*.py"],
    )

    assert files == [
        (tmp_path / "other/a.py").resolve(),
    ]


def test_excludes_glob_file_pattern(tmp_path: Path) -> None:
    """Support glob patterns against file names."""
    write_file(tmp_path, "main.py")
    write_file(tmp_path, "helper_test.py")
    write_file(tmp_path, "another_test.py")

    project = Project(tmp_path)

    files = project.get_python_files(
        exclude_patterns=["*_test.py"],
    )

    assert files == [
        (tmp_path / "main.py").resolve(),
    ]


def test_duplicate_patterns_do_not_change_results(
    tmp_path: Path,
) -> None:
    """Deduplicate exclusion patterns before scanning."""
    write_file(tmp_path, "main.py")
    write_file(tmp_path, "test.py")

    project = Project(tmp_path)

    files = project.get_python_files(
        exclude_patterns=[
            "test.py",
            "test.py",
            "test.py",
        ],
    )

    assert files == [
        (tmp_path / "main.py").resolve(),
    ]


def test_external_file_is_excluded(tmp_path: Path) -> None:
    """Treat files outside the project root as excluded."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    outside_file = tmp_path / "outside.py"
    outside_file.write_text("", encoding="utf-8")

    project = Project(project_root)

    assert project._should_exclude(
        outside_file,
        [],
    )


def test_non_python_files_are_ignored(tmp_path: Path) -> None:
    """Ignore files that do not have a .py extension."""
    write_file(tmp_path, "main.py")
    write_file(tmp_path, "notes.txt")
    write_file(tmp_path, "data.json")

    project = Project(tmp_path)

    files = project.get_python_files()

    assert files == [
        (tmp_path / "main.py").resolve(),
    ]
