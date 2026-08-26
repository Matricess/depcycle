"""Concrete visualization implementations for different output formats."""

from pathlib import Path
from typing import Dict

from ..config import Config
from ..graph.graph import DependencyGraph
from ..graph.node import ModuleType
from .interface import IGraphVisualizer


class GraphvizVisualizer(IGraphVisualizer):
    """
    Visualizer using Graphviz to generate PNG/SVG images.

    Temporary stub: the Graphviz dependency has been removed from this
    project (see refactor/p1-foundation). This class is replaced by the
    pure-Python output writers introduced in later refactor phases.
    """

    def __init__(self):
        """Initialize the GraphvizVisualizer."""
        self.graphviz = None
    
    def render(self, graph: DependencyGraph, config: Config):
        """
        Render the dependency graph as a PNG or SVG image.
        
        Args:
            graph: The DependencyGraph to visualize.
            config: Configuration including output path and format.
        """
        # Choose format; fallback to SVG for large graphs to improve readability
        node_count = len(graph.nodes)
        chosen_format = config.output_format
        if chosen_format == 'png' and node_count > 100:
            chosen_format = 'svg'
        
        # Create a new directed graph
        dot = self.graphviz.Digraph(
            comment='Dependency Graph',
            format=chosen_format,
            engine='dot',
            graph_attr={
                'rankdir': 'LR',  # Left to Right improves readability
                'bgcolor': 'white',
                'dpi': '300',
                'splines': 'polyline',
                'concentrate': 'true',
                'nodesep': '0.45',
                'ranksep': '1.1',
                'fontname': 'Helvetica',
                'pad': '0.4'
            }
        )
        # Standardize edge appearance
        dot.attr('edge', arrowhead='normal', arrowsize='0.8')
        
        # Detect circular dependencies
        cycles = graph.find_cycles()
        nodes_in_cycles = set()
        edges_in_cycles = set()
        
        for cycle in cycles:
            for node in cycle:
                nodes_in_cycles.add(node.name)
            # Create edge pairs for the cycle
            for i in range(len(cycle)):
                source = cycle[i].name
                target = cycle[(i + 1) % len(cycle)].name
                edges_in_cycles.add((source, target))
        
        # Group nodes by top-level package for clustering
        groups: Dict[str, list] = {}
        for node in graph.nodes.values():
            top = node.name.split('.')[0] if '.' in node.name else node.name
            groups.setdefault(top, []).append(node)
        
        # Add nodes inside clusters
        for group_name, nodes in sorted(groups.items(), key=lambda kv: kv[0]):
            with dot.subgraph(name=f'cluster_{self._escape_node_name(group_name)}') as sub:
                sub.attr(label=group_name, style='rounded', color='#D0D0D0', fontname='Helvetica', fontsize='12')
                for node in nodes:
                    is_in_cycle = node.name in nodes_in_cycles
                    self._add_node(sub, node, is_in_cycle)
        
        # Add edges
        for node in graph.nodes.values():
            for dependency in node.dependencies:
                # Only add edge if both nodes are in the graph
                if dependency.name in graph.nodes:
                    edge_in_cycle = (node.name, dependency.name) in edges_in_cycles
                    self._add_edge(dot, node.name, dependency.name, edge_in_cycle)
        
        # Add title and legend
        self._add_title(dot, node_count)
        self._add_legend(dot)
        
        # Render to file
        output_path = Path(config.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Adjust output file extension if we switched format
        final_output_path = output_path
        if output_path.suffix.lower().lstrip('.') != chosen_format:
            final_output_path = output_path.with_suffix(f'.{chosen_format}')
        
        # graphviz expects path without extension
        base_path = final_output_path.with_suffix('')
        dot.render(base_path, cleanup=True)
    
    def _add_node(self, dot, node, is_in_cycle=False):
        """
        Add a node to the graph with appropriate styling.
        
        Args:
            dot: The graphviz Digraph object.
            node: The ModuleNode to add.
            is_in_cycle: Whether this node is part of a circular dependency.
        """
        escaped_name = self._escape_node_name(node.name)
        
        # Highlight circular dependencies with red background
        if is_in_cycle:
            style = {
                'color': '#7F0000',      # Dark red border
                'fillcolor': '#F97068',  # Accessible red
                'style': 'filled,rounded,bold',
                'fontcolor': '#FFFFFF',
                'fontsize': '10',
                'penwidth': '2.5'        # Thicker border
            }
        elif node.module_type == ModuleType.LOCAL:
            style = {
                'color': '#1E88E5',      # Blue border (CB-friendly)
                'fillcolor': '#BBDEFB',  # Light blue background
                'style': 'filled,rounded',
                'fontcolor': '#000000',  # Black text
                'fontsize': '10'
            }
        elif node.module_type == ModuleType.THIRD_PARTY:
            style = {
                'color': '#FB8C00',      # Orange border
                'fillcolor': '#FFE0B2',  # Light orange background
                'style': 'filled,rounded',
                'fontcolor': '#000000',  # Black text
                'fontsize': '10'
            }
        else:  # STDLIB
            style = {
                'color': '#6D6D6D',      # Gray border
                'fillcolor': '#EEEEEE',  # Light gray background
                'style': 'filled,rounded',
                'fontcolor': '#333333',  # Dark gray text
                'fontsize': '9'
            }
        
        # Truncate long names for display
        display_name = node.name
        if len(display_name) > 40:
            display_name = display_name[:37] + "..."
        
        dot.node(escaped_name, display_name, tooltip=node.name, **style)
    
    def _add_edge(self, dot, source: str, target: str, is_in_cycle: bool = False):
        """
        Add an edge to the graph with appropriate styling.
        
        Args:
            dot: The graphviz Digraph object.
            source: Source node name.
            target: Target node name.
            is_in_cycle: Whether this edge is part of a circular dependency.
        """
        edge_attr = {}
        
        if is_in_cycle:
            # Highlight cycle edges with red and thicker line
            edge_attr = {
                'color': '#D32F2F',    # Accessible red
                'penwidth': '3.0'      # Thicker line
            }
        else:
            # Normal edges
            edge_attr = {
                'color': '#708090',    # Slate gray
                'penwidth': '1.5'
            }
        
        dot.edge(
            self._escape_node_name(source),
            self._escape_node_name(target),
            **edge_attr
        )
    
    def _escape_node_name(self, name: str) -> str:
        """
        Escape special characters in node names for Graphviz.
        
        Args:
            name: The module name.
        
        Returns:
            An escaped version safe for Graphviz.
        """
        return name.replace('.', '_').replace('-', '_')
    
    def _add_title(self, dot, node_count: int):
        """
        Add a title to the graph.
        
        Args:
            dot: The graphviz Digraph object.
            node_count: Number of nodes in the graph.
        """
        title = f"Dependency Graph • {node_count} modules"
        dot.attr(label=title, labelloc='t', fontsize='16', fontname='Helvetica', fontcolor='#333333')

    def _add_legend(self, dot):
        """
        Add a legend explaining colors and cycle highlighting.
        """
        with dot.subgraph(name='cluster_legend') as legend:
            legend.attr(label='Legend', color='#B0B0B0', style='rounded', fontname='Helvetica', fontsize='12')
            # Create example nodes
            legend.node('legend_local', 'Local', shape='box', style='filled,rounded', fillcolor='#BBDEFB', color='#1E88E5')
            legend.node('legend_third', 'Third-party', shape='box', style='filled,rounded', fillcolor='#FFE0B2', color='#FB8C00')
            legend.node('legend_std', 'Stdlib', shape='box', style='filled,rounded', fillcolor='#EEEEEE', color='#6D6D6D')
            legend.node('legend_cycle', 'In Cycle', shape='box', style='filled,rounded,bold', fillcolor='#F97068', color='#7F0000', fontcolor='#FFFFFF')
            # Arrange legend nodes
            legend.attr(rank='same')
            legend.edges([('legend_local', 'legend_third'), ('legend_third', 'legend_std'), ('legend_std', 'legend_cycle')])


class HtmlVisualizer(IGraphVisualizer):
    """
    Visualizer for generating interactive HTML output using D3.js.
    
    This creates an interactive, web-based visualization that allows
    users to explore dependencies dynamically.
    """
    
    def render(self, graph: DependencyGraph, config: Config):
        """
        Render the dependency graph as an interactive HTML page.
        
        Args:
            graph: The DependencyGraph to visualize.
            config: Configuration including output path.
        """
        # Generate node data
        nodes = []
        links = []
        
        # Create node mapping
        node_id_map = {}
        for idx, node in enumerate(graph.nodes.values()):
            node_id_map[node.name] = idx
            nodes.append({
                'id': idx,
                'name': node.name,
                'type': node.module_type.value,
                'deps_count': len(node.dependencies)
            })
        
        # Create links
        for node in graph.nodes.values():
            source_idx = node_id_map[node.name]
            for dependency in node.dependencies:
                if dependency.name in node_id_map:
                    target_idx = node_id_map[dependency.name]
                    links.append({
                        'source': source_idx,
                        'target': target_idx
                    })
        
        # Generate HTML
        html_content = self._generate_html(nodes, links)
        
        # Write to file
        output_path = Path(config.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding='utf-8')
    
    def _generate_html(self, nodes: list, links: list) -> str:
        """
        Generate the HTML content with embedded JavaScript.
        
        Args:
            nodes: List of node data dictionaries.
            links: List of link data dictionaries.
        
        Returns:
            Complete HTML as a string.
        """
        # This is a simplified HTML visualizer
        # In production, you'd want to use a proper templating engine
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dependency Graph</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2E86AB;
            margin-bottom: 20px;
        }}
        .stats {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .stats p {{
            margin: 5px 0;
        }}
        #graph {{
            border: 1px solid #ddd;
            border-radius: 5px;
            min-height: 600px;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Dependency Graph</h1>
        <div class="stats">
            <p><strong>Total Modules:</strong> {len(nodes)}</p>
            <p><strong>Total Dependencies:</strong> {len(links)}</p>
        </div>
        <div id="graph">
            <p style="text-align: center; padding: 50px; color: #666;">
                Interactive visualization coming soon. 
                Please use Graphviz output for now.
            </p>
        </div>
    </div>
    <script>
        // Nodes data would be used here with D3.js in a full implementation
        const nodes = {nodes};
        const links = {links};
        console.log("Graph data loaded:", {{ nodes, links }});
    </script>
</body>
</html>
"""

