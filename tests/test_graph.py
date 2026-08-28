"""Tests for dependency graph construction and analysis."""

from pathlib import Path

from depcycle.graph.graph import DependencyGraph
from depcycle.graph.node import ModuleNode, ModuleType


class FakeParser:
    """Minimal parser test double."""

    def __init__(self, imports: dict[Path, set[str]]) -> None:
        self.imports = imports

    def get_imports_from_file(self, file_path: Path) -> set[str]:
        """Return predefined imports for a file."""
        return self.imports.get(file_path, set())


def make_graph(
    tmp_path: Path,
    files: dict[str, set[str]],
) -> DependencyGraph:
    """Build a graph from temporary Python files."""
    paths: list[Path] = []
    imports: dict[Path, set[str]] = {}

    for relative_path, module_imports in files.items():
        file_path = tmp_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("", encoding="utf-8")

        paths.append(file_path)
        imports[file_path.resolve()] = module_imports

    parser = FakeParser(imports)

    return DependencyGraph().build(
        paths,
        tmp_path,
        parser,
    )


def test_build_uses_package_name_for_regular_layout(
    tmp_path: Path,
) -> None:
    """Create module names from a normal package layout."""
    graph = make_graph(
        tmp_path,
        {
            "depcycle/__init__.py": set(),
            "depcycle/cli.py": set(),
            "depcycle/utils.py": set(),
        },
    )

    assert set(graph.nodes) == {
        "depcycle",
        "depcycle.cli",
        "depcycle.utils",
    }

    assert graph.nodes["depcycle"].module_type is ModuleType.LOCAL


def test_build_ignores_src_directory_in_module_name(
    tmp_path: Path,
) -> None:
    """Do not include src in module names for src-layout projects."""
    graph = make_graph(
        tmp_path,
        {
            "src/depcycle/__init__.py": set(),
            "src/depcycle/cli.py": set(),
        },
    )

    assert set(graph.nodes) == {
        "depcycle",
        "depcycle.cli",
    }

    assert graph.nodes["depcycle.cli"].file_path == (tmp_path / "src/depcycle/cli.py")


def test_resolve_absolute_local_imports(
    tmp_path: Path,
) -> None:
    """Resolve absolute imports to local modules."""
    graph = make_graph(
        tmp_path,
        {
            "depcycle/__init__.py": {"depcycle.cli"},
            "depcycle/cli.py": {"depcycle.config"},
            "depcycle/config.py": set(),
        },
    )

    assert graph.nodes["depcycle"].dependencies == {
        graph.nodes["depcycle.cli"],
    }

    assert graph.nodes["depcycle.cli"].dependencies == {
        graph.nodes["depcycle.config"],
    }


def test_resolve_relative_imports(
    tmp_path: Path,
) -> None:
    """Resolve relative imports against the current package."""
    graph = make_graph(
        tmp_path,
        {
            "depcycle/__init__.py": set(),
            "depcycle/cli.py": {".config"},
            "depcycle/config.py": set(),
        },
    )

    assert graph.nodes["depcycle.cli"].dependencies == {
        graph.nodes["depcycle.config"],
    }


def test_resolve_parent_relative_import(
    tmp_path: Path,
) -> None:
    """Resolve imports that move to a parent package."""
    graph = make_graph(
        tmp_path,
        {
            "depcycle/__init__.py": set(),
            "depcycle/models/__init__.py": set(),
            "depcycle/models/user.py": {"..config"},
            "depcycle/config.py": set(),
        },
    )

    assert graph.nodes["depcycle.models.user"].dependencies == {
        graph.nodes["depcycle.config"],
    }


def test_resolve_bare_relative_submodule_import(
    tmp_path: Path,
) -> None:
    """Resolve names emitted for bare relative imports."""
    graph = make_graph(
        tmp_path,
        {
            "depcycle/__init__.py": set(),
            "depcycle/parsing/__init__.py": {".ast_parser"},
            "depcycle/parsing/ast_parser.py": set(),
        },
    )

    assert graph.nodes["depcycle.parsing"].dependencies == {
        graph.nodes["depcycle.parsing.ast_parser"],
    }


def test_unknown_absolute_import_becomes_unknown_node(
    tmp_path: Path,
) -> None:
    """Create an external node for an unresolved absolute import."""
    graph = make_graph(
        tmp_path,
        {
            "depcycle/cli.py": {"some_external_package"},
        },
    )

    dependency = graph.nodes["some_external_package"]

    assert dependency.file_path is None
    assert dependency.module_type is ModuleType.UNKNOWN

    assert graph.nodes["depcycle.cli"].dependencies == {
        dependency,
    }


def test_unresolved_relative_import_is_ignored(
    tmp_path: Path,
) -> None:
    """Ignore relative imports that cannot be resolved locally."""
    graph = make_graph(
        tmp_path,
        {
            "depcycle/cli.py": {".missing"},
        },
    )

    assert "depcycle.cli" in graph.nodes
    assert "depcycle.missing" not in graph.nodes
    assert graph.nodes["depcycle.cli"].dependencies == set()


def test_import_variants_are_generated(
    tmp_path: Path,
) -> None:
    """Generate progressively shorter module-name variants."""
    del tmp_path

    assert DependencyGraph._get_import_variants(
        "foo.bar.Baz",
    ) == [
        "foo.bar.Baz",
        "foo.bar",
        "foo",
    ]


def test_empty_import_variant_list() -> None:
    """Return no variants for an empty import string."""
    assert DependencyGraph._get_import_variants("") == []


def test_classify_stdlib() -> None:
    """Classify known standard-library modules correctly."""
    graph = DependencyGraph()

    graph.add_node(
        ModuleNode(
            name="json",
            file_path=None,
            module_type=ModuleType.UNKNOWN,
        )
    )

    graph.classify(
        known_stdlib={"json"},
        known_third_party={"requests"},
    )

    assert graph.nodes["json"].module_type is ModuleType.STDLIB


def test_classify_third_party() -> None:
    """Classify known third-party modules correctly."""
    graph = DependencyGraph()

    graph.add_node(
        ModuleNode(
            name="requests",
            file_path=None,
            module_type=ModuleType.UNKNOWN,
        )
    )

    graph.classify(
        known_stdlib={"json"},
        known_third_party={"requests"},
    )

    assert graph.nodes["requests"].module_type is ModuleType.THIRD_PARTY


def test_classify_unknown_when_known_third_party_set_is_provided() -> None:
    """Mark unrecognized external modules as unknown."""
    graph = DependencyGraph()

    graph.add_node(
        ModuleNode(
            name="mystery",
            file_path=None,
            module_type=ModuleType.UNKNOWN,
        )
    )

    graph.classify(
        known_stdlib={"json"},
        known_third_party={"requests"},
    )

    assert graph.nodes["mystery"].module_type is ModuleType.UNKNOWN


def test_classify_defaults_unresolved_modules_to_third_party() -> None:
    """Use third-party as the fallback when no dependency metadata is known."""
    graph = DependencyGraph()

    graph.add_node(
        ModuleNode(
            name="mystery",
            file_path=None,
            module_type=ModuleType.UNKNOWN,
        )
    )

    graph.classify(
        known_stdlib={"json"},
        known_third_party=set(),
    )

    assert graph.nodes["mystery"].module_type is ModuleType.THIRD_PARTY


def test_local_nodes_remain_local_after_classification() -> None:
    """Do not reclassify local modules."""
    graph = DependencyGraph()

    node = ModuleNode(
        name="depcycle",
        file_path=Path("depcycle/__init__.py"),
        module_type=ModuleType.LOCAL,
    )

    graph.add_node(node)
    graph.classify(
        known_stdlib={"depcycle"},
        known_third_party={"depcycle"},
    )

    assert graph.nodes["depcycle"].module_type is ModuleType.LOCAL


def test_filter_preserves_local_modules() -> None:
    """Keep local modules regardless of category visibility."""
    graph = DependencyGraph()

    local = ModuleNode(
        name="local",
        file_path=Path("local.py"),
        module_type=ModuleType.LOCAL,
    )

    stdlib = ModuleNode(
        name="json",
        file_path=None,
        module_type=ModuleType.STDLIB,
    )

    third_party = ModuleNode(
        name="requests",
        file_path=None,
        module_type=ModuleType.THIRD_PARTY,
    )

    local.dependencies = {
        stdlib,
        third_party,
    }

    graph.add_node(local)
    graph.add_node(stdlib)
    graph.add_node(third_party)

    graph.filter(
        show_stdlib=False,
        show_third_party=False,
        show_unknown=True,
    )

    assert set(graph.nodes) == {"local"}
    assert graph.nodes["local"].dependencies == set()


def test_filter_can_keep_stdlib_and_remove_third_party() -> None:
    """Filter categories independently."""
    graph = DependencyGraph()

    local = ModuleNode(
        name="local",
        file_path=Path("local.py"),
        module_type=ModuleType.LOCAL,
    )

    stdlib = ModuleNode(
        name="json",
        file_path=None,
        module_type=ModuleType.STDLIB,
    )

    third_party = ModuleNode(
        name="requests",
        file_path=None,
        module_type=ModuleType.THIRD_PARTY,
    )

    local.dependencies = {
        stdlib,
        third_party,
    }

    graph.add_node(local)
    graph.add_node(stdlib)
    graph.add_node(third_party)

    graph.filter(
        show_stdlib=True,
        show_third_party=False,
        show_unknown=False,
    )

    assert set(graph.nodes) == {
        "local",
        "json",
    }

    assert graph.nodes["local"].dependencies == {
        stdlib,
    }


def test_filter_noop_when_all_categories_enabled() -> None:
    """Do not modify the graph when every category is shown."""
    graph = DependencyGraph()

    node = ModuleNode(
        name="json",
        file_path=None,
        module_type=ModuleType.STDLIB,
    )

    graph.add_node(node)

    result = graph.filter()

    assert result is graph
    assert graph.nodes["json"] is node


def test_find_simple_cycle() -> None:
    """Detect a two-node dependency cycle."""
    first = ModuleNode(
        name="a",
        file_path=Path("a.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="b",
        file_path=Path("b.py"),
        module_type=ModuleType.LOCAL,
    )

    first.dependencies = {second}
    second.dependencies = {first}

    graph = DependencyGraph()
    graph.add_node(first)
    graph.add_node(second)

    cycles = graph.find_cycles()

    assert len(cycles) == 1
    assert [node.name for node in cycles[0]] in (
        ["a", "b", "a"],
        ["b", "a", "b"],
    )


def test_find_cycle_longer_than_two_nodes() -> None:
    """Detect a three-node dependency cycle."""
    first = ModuleNode(
        name="a",
        file_path=Path("a.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="b",
        file_path=Path("b.py"),
        module_type=ModuleType.LOCAL,
    )

    third = ModuleNode(
        name="c",
        file_path=Path("c.py"),
        module_type=ModuleType.LOCAL,
    )

    first.dependencies = {second}
    second.dependencies = {third}
    third.dependencies = {first}

    graph = DependencyGraph()

    for node in (first, second, third):
        graph.add_node(node)

    cycles = graph.find_cycles()

    assert len(cycles) == 1
    assert [node.name for node in cycles[0]][-1] == "a"


def test_find_cycles_returns_empty_for_acyclic_graph() -> None:
    """Return no cycles for an acyclic dependency graph."""
    first = ModuleNode(
        name="a",
        file_path=Path("a.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="b",
        file_path=Path("b.py"),
        module_type=ModuleType.LOCAL,
    )

    third = ModuleNode(
        name="c",
        file_path=Path("c.py"),
        module_type=ModuleType.LOCAL,
    )

    first.dependencies = {second}
    second.dependencies = {third}

    graph = DependencyGraph()

    for node in (first, second, third):
        graph.add_node(node)

    assert graph.find_cycles() == []


def test_graph_length_and_iteration() -> None:
    """Support len() and iteration over graph nodes."""
    first = ModuleNode(
        name="a",
        file_path=Path("a.py"),
        module_type=ModuleType.LOCAL,
    )

    second = ModuleNode(
        name="b",
        file_path=Path("b.py"),
        module_type=ModuleType.LOCAL,
    )

    graph = DependencyGraph()
    graph.add_node(first)
    graph.add_node(second)

    assert len(graph) == 2
    assert {node.name for node in graph} == {"a", "b"}


def test_repr_reports_node_count() -> None:
    """Return a useful developer representation."""
    graph = DependencyGraph()

    graph.add_node(
        ModuleNode(
            name="a",
            file_path=Path("a.py"),
            module_type=ModuleType.LOCAL,
        )
    )

    assert repr(graph) == "DependencyGraph(nodes=1)"
