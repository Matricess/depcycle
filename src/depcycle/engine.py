"""Core execution engine for building dependency graphs from configuration."""

from __future__ import annotations

from .config import AnalysisConfig
from .graph.graph import DependencyGraph
from .graph.node import ModuleNode
from .parsing.ast_parser import ASTParser
from .parsing.metadata import PackageMetadataReader
from .parsing.project import Project


def analyze_project(
    config: AnalysisConfig,
) -> tuple[DependencyGraph, list[list[ModuleNode]]]:
    """
    Single unified project dependency analyzer.

    Executes project parsing, dependency graph building, package metadata reading,
    node classification, filtering, and cycle detection.

    Returns:
        A tuple containing (built_and_filtered_graph, detected_cycles).
    """
    project = Project(config.project_path)
    parser = ASTParser()
    metadata_reader = PackageMetadataReader()

    graph = DependencyGraph()

    files = project.get_python_files(
        exclude_patterns=config.exclude_patterns,
    )

    graph.build(
        files,
        project.root_path,
        parser,
    )

    known_third_party = metadata_reader.read(
        project.root_path,
    )

    graph.classify(
        known_third_party=known_third_party,
    )

    graph.filter(
        show_stdlib=config.show_stdlib,
        show_third_party=config.show_third_party,
        show_unknown=config.show_unknown,
    )

    cycles = graph.find_cycles()

    return graph, cycles
