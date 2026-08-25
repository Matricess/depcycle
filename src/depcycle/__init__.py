"""
DepCycle - A dependency graph visualization tool for Python projects.

DepCycle helps developers understand complex codebases by automatically 
generating visual maps of module dependencies.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("depcycle")
except PackageNotFoundError:
    # Package is not installed (e.g. running directly from source).
    __version__ = "0.0.0"

from .cli import DepCycleCLI
from .config import Config
from .graph import DependencyGraph, ModuleNode, ModuleType
from .parsing import ASTParser, Project
from .rendering import GraphvizVisualizer, HtmlVisualizer, IGraphVisualizer

__all__ = [
    'DepCycleCLI',
    'Config',
    'DependencyGraph',
    'ModuleNode',
    'ModuleType',
    'Project',
    'ASTParser',
    'IGraphVisualizer',
    'GraphvizVisualizer',
    'HtmlVisualizer',
]

