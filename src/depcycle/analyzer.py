"""Orchestrator for analyzing project dependencies and detecting cycles."""

from __future__ import annotations

from .config import AnalysisConfig
from .graph.graph import Graph
from .graph.node import Node, NodeType
from .parsing.imports import ASTParser
from .parsing.metadata import PackageMetadataReader
from .parsing.workspace import Workspace
from .utils import get_stdlib_names, normalize_name, path_to_module_name


def analyze_project(
    config: AnalysisConfig,
    parser: ASTParser | None = None,
    metadata_reader: PackageMetadataReader | None = None,
) -> tuple[Graph, list[list[Node]]]:
    """
    Execute end-to-end dependency analysis for a Python project.

    Handles workspace discovery, AST import parsing, metadata reading,
    node classification, graph filtering, and cycle detection.
    """
    workspace = Workspace(config.project_path)
    parser = parser or ASTParser()
    metadata_reader = metadata_reader or PackageMetadataReader()

    python_files = list(
        workspace.get_python_files(exclude_patterns=config.exclude_patterns)
    )

    graph = Graph()

    for file_path in python_files:
        module_name = path_to_module_name(file_path, workspace.root_path)
        if module_name and module_name not in graph.nodes:
            node = Node(
                name=module_name,
                file_path=file_path,
                node_type=NodeType.LOCAL,
            )
            graph.add_node(node)

    for file_path in python_files:
        source_module = path_to_module_name(file_path, workspace.root_path)
        if not source_module:
            continue

        source_node = graph.nodes[source_module]
        imported_modules = parser.get_imports_from_file(file_path)

        for target_name in imported_modules:
            target_node = graph.get_node(target_name)
            if not target_node:
                target_node = Node(
                    name=target_name,
                    file_path=None,
                    node_type=NodeType.UNKNOWN,
                )
                graph.add_node(target_node)

            source_node.add_dependency(target_node)

    known_third_party = metadata_reader.read(workspace.root_path)
    normalized_third_party = {normalize_name(pkg) for pkg in known_third_party}
    stdlib_names = get_stdlib_names()

    for node in graph.nodes.values():
        if node.node_type == NodeType.LOCAL or node.file_path is not None:
            continue

        root_package = node.name.split(".")[0]
        normalized_root = normalize_name(root_package)

        if root_package in stdlib_names:
            node.node_type = NodeType.STDLIB
        elif normalized_root in normalized_third_party:
            node.node_type = NodeType.THIRD_PARTY
        else:
            node.node_type = NodeType.UNKNOWN

    to_remove: set[str] = set()
    for name, node in graph.nodes.items():
        if (
            (node.node_type == NodeType.STDLIB and not config.show_stdlib)
            or (node.node_type == NodeType.THIRD_PARTY and not config.show_third_party)
            or (node.node_type == NodeType.UNKNOWN and not config.show_unknown)
        ):
            to_remove.add(name)

    for name in to_remove:
        del graph.nodes[name]

    for node in graph.nodes.values():
        node.dependencies.intersection_update(
            {dep for dep in node.dependencies if dep.name in graph.nodes}
        )

    cycles = graph.find_cycles()

    return graph, cycles
