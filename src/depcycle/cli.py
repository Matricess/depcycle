"""
this module contains the command-line interface logic for DepCycle.
it defines the user-facing commands, parses arguments, and orchestrates
the dependency analysis and visualization workflow.
"""

import argparse
import sys
from pathlib import Path

from .config import AnalysisConfig, Config
from .graph.graph import DependencyGraph
from .output import DotWriter, HtmlWriter, JsonWriter
from .parsing.ast_parser import ASTParser
from .parsing.project import Project
from .rendering.interface import IGraphVisualizer
from .rendering.visualizers import GraphvizVisualizer, HtmlVisualizer


class DepCycleCLI:
    """
    The Conductor: Parses arguments and orchestrates the workflow.
    
    This class handles all command-line interaction, from parsing user
    arguments to coordinating the analysis and visualization pipeline.
    """
    
    @staticmethod
    def main(args: list = None):
        """
        Main entry point for the DepCycle CLI.
        
        Parses command-line arguments, creates configuration, and runs
        the dependency analysis workflow.
        
        Args:
            args: Command-line arguments (defaults to sys.argv).
        """
        if args is None:
            args = sys.argv[1:]
        
        # Parse arguments
        parser = DepCycleCLI._create_parser()
        parsed_args = parser.parse_args(args)
        
        # Validate arguments
        if not parsed_args.project_path:
            parser.error("Project path is required")
        
        output_arg = parsed_args.output
        output_path = Path(output_arg) if output_arg and output_arg != '-' else None
        output_format = parsed_args.format

        if output_format is None:
            if output_path is not None and output_path.suffix.lower().lstrip('.') in {'png', 'svg', 'html', 'json', 'dot'}:
                output_format = output_path.suffix.lower().lstrip('.')
            else:
                output_format = 'html'

        if output_path is None and output_format in {'html', 'json', 'dot'}:
            output_path = Path(f"dependencies.{output_format}")

        config = AnalysisConfig(
            project_path=Path(parsed_args.project_path),
            exclude_patterns=parsed_args.exclude,
            show_third_party=not parsed_args.no_third_party,
            show_stdlib=not parsed_args.no_stdlib,
            show_unknown=True,
            include_all=parsed_args.include_all,
        )

        if not config.project_path.exists():
            print(f"Error: Project path does not exist: {config.project_path}")
            sys.exit(1)

        try:
            DepCycleCLI.run(config, output_path=output_path, output_format=output_format)
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    @staticmethod
    def run(config: AnalysisConfig, output_path: Path = None, output_format: str = "png"):
        """Execute the dependency analysis and visualization workflow."""
        print(f"Analyzing project: {config.project_path}")

        project = Project(config.project_path)
        parser = ASTParser()

        print("Building dependency graph...")
        graph = DependencyGraph()
        graph.build(project, parser, Config(
            project_path=config.project_path,
            output_file=output_path or Path("dependencies.png"),
            output_format=output_format,
            exclude_patterns=config.exclude_patterns,
            show_third_party=config.show_third_party,
            show_stdlib=config.show_stdlib,
            show_unknown=config.show_unknown,
            include_all=config.include_all,
        ))

        print(f"Found {len(graph)} modules")

        cycles = graph.find_cycles()
        if cycles:
            print(f"\n⚠️  Warning: Found {len(cycles)} circular dependency cycles!")
            for i, cycle in enumerate(cycles[:5], 1):
                cycle_names = [node.name for node in cycle]
                print(f"  Cycle {i}: {' → '.join(cycle_names)}")
            if len(cycles) > 5:
                print(f"  ... and {len(cycles) - 5} more cycles")
        else:
            print("✓ No circular dependencies detected")

        if output_format == 'json':
            print("\nGenerating JSON output...")
            JsonWriter().write(graph, output_path)
            if output_path is None:
                print("✓ JSON output written to stdout")
            else:
                print(f"✓ JSON output saved to: {output_path}")
            return

        if output_format == 'dot':
            print("\nGenerating DOT output...")
            DotWriter().write(graph, output_path)
            if output_path is None:
                print("✓ DOT output written to stdout")
            else:
                print(f"✓ DOT output saved to: {output_path}")
            return

        if output_format == 'html':
            print("\nGenerating HTML output...")
            HtmlWriter().write(graph, output_path)
            if output_path is None:
                print("✓ HTML output written to stdout")
            else:
                print(f"✓ HTML output saved to: {output_path}")
            return

        output_file = output_path or Path("dependencies.png")
        print(f"\nGenerating {output_format.upper()} visualization...")
        visualizer = DepCycleCLI._create_visualizer(output_format)
        visualizer.render(graph, Config(
            project_path=config.project_path,
            output_file=output_file,
            output_format=output_format,
            exclude_patterns=config.exclude_patterns,
            show_third_party=config.show_third_party,
            show_stdlib=config.show_stdlib,
            show_unknown=config.show_unknown,
            include_all=config.include_all,
        ))

        print(f"✓ Visualization saved to: {output_file}")
    
    @staticmethod
    def _create_parser() -> argparse.ArgumentParser:
        """
        Create and configure the argument parser.
        
        Returns:
            Configured ArgumentParser instance.
        """
        parser = argparse.ArgumentParser(
            prog='depcycle',
            description='Visualize Python project dependencies',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s /path/to/project
  %(prog)s /path/to/project -o output.png
  %(prog)s /path/to/project --format svg --exclude tests
  %(prog)s /path/to/project --no-third-party --no-stdlib
  %(prog)s /path/to/project --include-all  # Include venv, __pycache__, etc.
            """
        )
        
        parser.add_argument(
            'project_path',
            nargs='?',
            help='Path to the Python project to analyze'
        )
        
        parser.add_argument(
            '-o', '--output',
            help='Output file path (default: dependencies.png)',
            default=None
        )
        
        parser.add_argument(
            '-f', '--format',
            choices=['html', 'json', 'dot', 'png', 'svg'],
            help='Output format (default: inferred from output file, otherwise html)',
            default=None
        )
        
        parser.add_argument(
            '-e', '--exclude',
            action='append',
            help='Glob patterns to exclude (e.g., venv, tests/*.py). Can be specified multiple times.',
            default=[]
        )
        
        parser.add_argument(
            '--no-third-party',
            action='store_true',
            help='Exclude third-party dependencies from the graph'
        )
        
        parser.add_argument(
            '--no-stdlib',
            action='store_true',
            help='Exclude standard library modules from the graph'
        )
        
        parser.add_argument(
            '--include-all',
            action='store_true',
            help='Include files normally excluded by default (venv, __pycache__, etc.)'
        )
        
        return parser
    
    @staticmethod
    def _create_visualizer(output_format: str) -> IGraphVisualizer:
        """
        Create the appropriate visualizer based on output format.
        
        Args:
            output_format: Desired output format ('png', 'svg', 'html').
        
        Returns:
            An instance of the appropriate visualizer.
        
        Raises:
            ValueError: If the format is not supported.
        """
        if output_format in ['png', 'svg']:
            return GraphvizVisualizer()
        elif output_format == 'html':
            return HtmlVisualizer()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")


# Entry point for running as a script
if __name__ == '__main__':
    DepCycleCLI.main()
