"""
DepCycle - A dependency graph visualization tool for Python projects.

DepCycle helps developers understand complex codebases by automatically
generating visual maps of module dependencies.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("depcycle")
except PackageNotFoundError:
    __version__ = "0.0.0"

from .cli import DepCycleCLI
from .config import AnalysisConfig
from .graph.graph import Graph
from .graph.node import Node, NodeType
from .output import DotWriter, HtmlWriter, IOutputWriter, JsonWriter
from .parsing.imports import ASTParser
from .parsing.metadata import PackageMetadataReader
from .parsing.workspace import Workspace

__all__ = [
    "ASTParser",
    "AnalysisConfig",
    "DepCycleCLI",
    "DotWriter",
    "Graph",
    "HtmlWriter",
    "IOutputWriter",
    "JsonWriter",
    "Node",
    "NodeType",
    "PackageMetadataReader",
    "Workspace",
]
