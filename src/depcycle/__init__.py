"""
DepCycle - A dependency graph visualization tool for Python projects.

DepCycle helps developers understand complex codebases by automatically 
generating visual maps of module dependencies.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("depcycle")
except PackageNotFoundError:
    __version__ = "0.0.0"

from .cli import DepCycleCLI
from .config import AnalysisConfig, Config
from .graph import DependencyGraph, ModuleNode, ModuleType
from .output import DotWriter, HtmlWriter, IOutputWriter, JsonWriter
from .parsing import ASTParser, PackageMetadataReader, Project

__all__ = [
    'ASTParser',
    'AnalysisConfig',
    'Config',
    'DepCycleCLI',
    'DependencyGraph',
    'DotWriter',
    'HtmlWriter',
    'IOutputWriter',
    'JsonWriter',
    'ModuleNode',
    'ModuleType',
    'PackageMetadataReader',
    'Project',
]
