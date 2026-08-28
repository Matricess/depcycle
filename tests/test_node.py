"""Tests for dependency graph node models."""

from pathlib import Path

from depcycle.graph.node import ModuleNode, ModuleType


def test_module_type_contains_expected_values() -> None:
    """Expose all supported module categories."""
    assert ModuleType.LOCAL.value == "local"
    assert ModuleType.THIRD_PARTY.value == "third_party"
    assert ModuleType.STDLIB.value == "stdlib"
    assert ModuleType.UNKNOWN.value == "unknown"


def test_module_node_initializes_attributes() -> None:
    """Initialize a node with its core graph attributes."""
    file_path = Path("/project/example.py")

    node = ModuleNode(
        name="example",
        file_path=file_path,
        module_type=ModuleType.LOCAL,
    )

    assert node.name == "example"
    assert node.file_path == file_path
    assert node.module_type is ModuleType.LOCAL
    assert node.raw_imports == set()
    assert node.dependencies == set()


def test_module_node_allows_external_node_without_file() -> None:
    """Allow non-local nodes to have no source file."""
    node = ModuleNode(
        name="requests",
        file_path=None,
        module_type=ModuleType.THIRD_PARTY,
    )

    assert node.name == "requests"
    assert node.file_path is None
    assert node.module_type is ModuleType.THIRD_PARTY


def test_module_node_raw_imports_are_mutable() -> None:
    """Allow the parser to populate raw imports after construction."""
    node = ModuleNode(
        name="example",
        file_path=Path("example.py"),
        module_type=ModuleType.LOCAL,
    )

    node.raw_imports.update(
        {
            "json",
            "example.utils",
        }
    )

    assert node.raw_imports == {
        "json",
        "example.utils",
    }


def test_module_node_dependencies_are_mutable() -> None:
    """Allow graph resolution to populate dependency nodes."""
    first = ModuleNode(
        name="first",
        file_path=Path("first.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="second",
        file_path=Path("second.py"),
        module_type=ModuleType.LOCAL,
    )

    first.dependencies.add(second)

    assert first.dependencies == {second}


def test_module_nodes_with_same_name_are_equal() -> None:
    """Use module name as node identity."""
    first = ModuleNode(
        name="example",
        file_path=Path("/one/example.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="example",
        file_path=Path("/two/example.py"),
        module_type=ModuleType.UNKNOWN,
    )

    assert first == second


def test_module_nodes_with_different_names_are_not_equal() -> None:
    """Treat different module names as different graph identities."""
    first = ModuleNode(
        name="example",
        file_path=Path("example.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="other",
        file_path=Path("other.py"),
        module_type=ModuleType.LOCAL,
    )

    assert first != second


def test_module_node_is_not_equal_to_unrelated_object() -> None:
    """Return NotImplemented semantics for unrelated object types."""
    node = ModuleNode(
        name="example",
        file_path=Path("example.py"),
        module_type=ModuleType.LOCAL,
    )

    assert node != "example"
    assert node != object()


def test_equal_module_nodes_have_same_hash() -> None:
    """Keep hashing consistent with module-name equality."""
    first = ModuleNode(
        name="example",
        file_path=Path("/one/example.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="example",
        file_path=Path("/two/example.py"),
        module_type=ModuleType.UNKNOWN,
    )

    assert hash(first) == hash(second)


def test_module_node_hash_uses_name_identity() -> None:
    """Use module name for set membership and dictionary keys."""
    first = ModuleNode(
        name="example",
        file_path=Path("/one/example.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="example",
        file_path=Path("/two/example.py"),
        module_type=ModuleType.UNKNOWN,
    )

    nodes = {first, second}

    assert len(nodes) == 1
    assert first in nodes
    assert second in nodes


def test_module_node_can_be_dictionary_key() -> None:
    """Allow graph nodes to be used as dictionary keys."""
    node = ModuleNode(
        name="example",
        file_path=Path("example.py"),
        module_type=ModuleType.LOCAL,
    )

    mapping = {node: "value"}

    equivalent = ModuleNode(
        name="example",
        file_path=Path("different.py"),
        module_type=ModuleType.UNKNOWN,
    )

    assert mapping[equivalent] == "value"


def test_repr_contains_name_type_and_dependency_count() -> None:
    """Provide a useful developer-facing representation."""
    node = ModuleNode(
        name="example",
        file_path=Path("example.py"),
        module_type=ModuleType.LOCAL,
    )

    dependency = ModuleNode(
        name="json",
        file_path=None,
        module_type=ModuleType.STDLIB,
    )

    node.dependencies.add(dependency)

    assert repr(node) == ("ModuleNode(name='example', type=LOCAL, deps=1)")


def test_repr_for_empty_node() -> None:
    """Report zero dependencies for a new node."""
    node = ModuleNode(
        name="example",
        file_path=Path("example.py"),
        module_type=ModuleType.LOCAL,
    )

    assert repr(node) == ("ModuleNode(name='example', type=LOCAL, deps=0)")


def test_file_path_is_informational_for_equality() -> None:
    """Do not use source file path as graph identity."""
    first = ModuleNode(
        name="example",
        file_path=Path("/project/src/example.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="example",
        file_path=Path("/different/location/example.py"),
        module_type=ModuleType.LOCAL,
    )

    assert first == second


def test_module_type_is_informational_for_equality() -> None:
    """Do not use module category as graph identity."""
    first = ModuleNode(
        name="example",
        file_path=None,
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="example",
        file_path=None,
        module_type=ModuleType.UNKNOWN,
    )

    assert first == second
