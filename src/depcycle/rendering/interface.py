"""Interface for graph visualization implementations."""

from abc import ABC, abstractmethod

from ..config import Config
from ..graph.graph import DependencyGraph


class IGraphVisualizer(ABC):
    """
    The Artist's Interface: Defines a contract for rendering the dependency graph.
    
    This abstract base class ensures that all visualization implementations
    follow the same interface, making it easy to add new output formats.
    """
    
    @abstractmethod
    def render(self, graph: DependencyGraph, config: Config):
        """
        Render a dependency graph to the output format.
        
        This method takes a DependencyGraph and generates a visualization
        in the specified format according to the Config settings.
        
        Args:
            graph: The DependencyGraph to visualize.
            config: Configuration settings including output file path.
        
        Raises:
            NotImplementedError: If the subclass doesn't implement this method.
        """
        pass

