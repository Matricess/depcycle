"""
This module contains the command-line interface logic for DepCycle.
It defines the user-facing commands, parses arguments, and orchestrates
the dependency analysis and visualization workflow.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import AnalysisConfig
from .graph.graph import DependencyGraph
from .graph.node import ModuleNode
from .output import DotWriter, HtmlWriter, JsonWriter, build_export
from .output.base import relative_file_path
from .parsing.ast_parser import ASTParser
from .parsing.metadata import PackageMetadataReader
from .parsing.project import Project

_WRITERS = {
    "html": HtmlWriter,
    "json": JsonWriter,
    "dot": DotWriter,
}


class DepCycleCLI:
    """Parse command-line arguments and orchestrate the dependency workflow."""

    @staticmethod
    def _add_analyze_arguments(parser: argparse.ArgumentParser) -> None:
        """Add the arguments accepted by the `analyze` subcommand."""
        parser.add_argument(
            "project_path",
            help="Path to the Python project to analyze",
        )

        parser.add_argument(
            "-o",
            "--output",
            help=(
                "Output file path (default: dependencies.<format>). "
                "Use '-' to write to stdout."
            ),
            default=None,
        )

        parser.add_argument(
            "-f",
            "--format",
            choices=["html", "json", "dot"],
            help=("Output format (default: inferred from output file, otherwise html)"),
            default=None,
        )

        parser.add_argument(
            "-e",
            "--exclude",
            action="append",
            help=(
                "Glob patterns to exclude "
                "(e.g., venv, tests/*.py). Can be specified multiple times."
            ),
            default=None,
        )

        parser.add_argument(
            "--no-third-party",
            action="store_true",
            help="Exclude third-party dependencies from the graph",
        )

        parser.add_argument(
            "--no-stdlib",
            action="store_true",
            help="Exclude standard library modules from the graph",
        )

        parser.add_argument(
            "--include-all",
            action="store_true",
            help=(
                "Include files normally excluded by default (venv, __pycache__, etc.)"
            ),
        )

        parser.add_argument(
            "--target",
            action="append",
            help=(
                "Module name to print a focused summary for "
                "(direct deps, direct dependents, cycles touching it). "
                "Can be specified multiple times."
            ),
            default=None,
        )

        parser.add_argument(
            "--impact",
            action="append",
            help=(
                "Module name to print an impact summary for "
                "(direct/reachable dependents, direct deps, cycles touching it). "
                "Can be specified multiple times."
            ),
            default=None,
        )

        parser.add_argument(
            "--path",
            nargs=2,
            metavar=("SOURCE", "TARGET"),
            help="Print the shortest import chain from SOURCE to TARGET.",
            default=None,
        )

    @staticmethod
    def _add_query_arguments(parser: argparse.ArgumentParser) -> None:
        """Add the arguments accepted by the `query` subcommand."""
        parser.add_argument(
            "project_path",
            help="Path to the Python project to analyze",
        )

        query_subparsers = parser.add_subparsers(
            dest="query_command",
            required=True,
        )

        module_parser = query_subparsers.add_parser(
            "module",
            help="Print compact JSON info for a single module",
        )
        module_parser.add_argument("module_name")

        deps_parser = query_subparsers.add_parser(
            "deps",
            help="List the direct dependencies of a module as compact JSON",
        )
        deps_parser.add_argument("module_name")

        dependents_parser = query_subparsers.add_parser(
            "dependents",
            help="List the direct dependents of a module as compact JSON",
        )
        dependents_parser.add_argument("module_name")

        cycles_parser = query_subparsers.add_parser(
            "cycles",
            help="List detected cycles as compact JSON",
        )
        cycles_parser.add_argument(
            "--module",
            default=None,
            help="Only include cycles that touch this module",
        )

        neighborhood_parser = query_subparsers.add_parser(
            "neighborhood",
            help="List modules within N hops of a module as compact JSON",
        )
        neighborhood_parser.add_argument("module_name")
        neighborhood_parser.add_argument(
            "--depth",
            type=int,
            default=1,
        )

    @staticmethod
    def _create_parser() -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            prog="depcycle",
            description="Visualize and query Python project dependencies",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s analyze /path/to/project
  %(prog)s analyze /path/to/project -o output.html
  %(prog)s analyze /path/to/project --format dot --exclude tests
  %(prog)s analyze /path/to/project --no-third-party --no-stdlib
  %(prog)s analyze /path/to/project --include-all
  %(prog)s analyze /path/to/project -o -
  %(prog)s query /path/to/project module my_app.services.orders
  %(prog)s query /path/to/project deps my_app.services.orders
""",
        )

        subparsers = parser.add_subparsers(
            dest="command",
            required=True,
        )

        analyze_parser = subparsers.add_parser(
            "analyze",
            help="Analyze a project and generate dependency output (HTML/JSON/DOT)",
        )
        DepCycleCLI._add_analyze_arguments(analyze_parser)

        query_parser = subparsers.add_parser(
            "query",
            help="Query the dependency graph for compact, machine-readable answers",
        )
        DepCycleCLI._add_query_arguments(query_parser)

        return parser

    @staticmethod
    def run(
        config: AnalysisConfig,
        output_path: Path | None = None,
        output_format: str = "html",
        impact_targets: list[str] | None = None,
        path_query: tuple[str, str] | None = None,
    ) -> None:
        """Execute the dependency analysis and visualization workflow."""
        print(f"Analyzing project: {config.project_path}", file=sys.stderr)

        project = Project(config.project_path)
        parser = ASTParser()
        metadata_reader = PackageMetadataReader()

        print("Building dependency graph...", file=sys.stderr)

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

        print(f"Found {len(graph)} modules", file=sys.stderr)

        cycles = graph.find_cycles()

        if cycles:
            print(f"\n⚠️  Warning: Found {len(cycles)} circular dependency cycles!", file=sys.stderr)

            for i, cycle in enumerate(cycles[:5], start=1):
                cycle_names = [node.name for node in cycle]
                print(f"  Cycle {i}: {' → '.join(cycle_names)}", file=sys.stderr)

            if len(cycles) > 5:
                print(f"  ... and {len(cycles) - 5} more cycles", file=sys.stderr)
        else:
            print("✓ No circular dependencies detected", file=sys.stderr)

        for target in config.targets:
            DepCycleCLI._print_target_summary(graph, cycles, target)

        for module_name in impact_targets or []:
            DepCycleCLI._print_impact_summary(graph, cycles, module_name)

        if path_query is not None:
            DepCycleCLI._print_path(graph, *path_query)

        writer_cls = _WRITERS.get(output_format)

        if writer_cls is None:
            raise ValueError(f"Unsupported output format: {output_format}")

        export = build_export(
            graph,
            cycles=cycles,
        )

        print(f"\nGenerating {output_format.upper()} output...", file=sys.stderr)

        writer_cls().write(
            export,
            output_path,
        )

        label = (
            "written to stdout" if output_path is None else f"saved to: {output_path}"
        )

        print(f"✓ {output_format.upper()} output {label}", file=sys.stderr)

    @staticmethod
    def _print_target_summary(
        graph: DependencyGraph,
        cycles: list[list[ModuleNode]],
        target: str,
    ) -> None:
        """Print a focused summary of a single target module to stderr."""
        print(f"\nTarget: {target}", file=sys.stderr)

        if target not in graph.nodes:
            print("  Not found in graph", file=sys.stderr)
            return

        touching_cycles = [
            cycle for cycle in cycles if any(node.name == target for node in cycle)
        ]

        print(f"  Direct dependencies: {graph.fan_out(target)}", file=sys.stderr)
        print(f"  Direct dependents:   {graph.fan_in(target)}", file=sys.stderr)
        print(f"  Cycles involving:    {len(touching_cycles)}", file=sys.stderr)

    @staticmethod
    def _print_impact_summary(
        graph: DependencyGraph,
        cycles: list[list[ModuleNode]],
        module_name: str,
    ) -> None:
        """Print an impact summary of a single module to stderr."""
        print(f"\nImpact: {module_name}", file=sys.stderr)

        if module_name not in graph.nodes:
            print("  Not found in graph", file=sys.stderr)
            return

        touching_cycles = [
            cycle for cycle in cycles if any(node.name == module_name for node in cycle)
        ]

        print(f"  Direct dependents:    {graph.fan_in(module_name)}", file=sys.stderr)
        print(
            f"  Reachable dependents: {len(graph.reachable_dependents(module_name))}",
            file=sys.stderr,
        )
        print(f"  Direct dependencies:  {graph.fan_out(module_name)}", file=sys.stderr)
        print(f"  Cycles involving:     {len(touching_cycles)}", file=sys.stderr)

    @staticmethod
    def _print_path(
        graph: DependencyGraph,
        source: str,
        target: str,
    ) -> None:
        """Print the shortest import chain between two modules to stderr."""
        path = graph.shortest_path(source, target)

        if path is None:
            print(f"\nPath: {source} → {target}", file=sys.stderr)
            print("  No import path found.", file=sys.stderr)
            return

        print(
            f"\nPath: {' → '.join(node.name for node in path)}",
            file=sys.stderr,
        )

    @staticmethod
    def _validate_project_path(project_path: Path) -> None:
        """Exit with status one if the project path is missing or not a directory."""
        if not project_path.exists():
            print(
                f"Error: Project path does not exist: {project_path}",
                file=sys.stderr,
            )
            sys.exit(1)

        if not project_path.is_dir():
            print(
                f"Error: Project path is not a directory: {project_path}",
                file=sys.stderr,
            )
            sys.exit(1)

    @staticmethod
    def _main_analyze(parsed_args: argparse.Namespace) -> None:
        """Run the `analyze` subcommand: the full analysis and output pipeline."""
        project_path = Path(parsed_args.project_path)

        DepCycleCLI._validate_project_path(project_path)

        output_arg = parsed_args.output
        output_to_stdout = output_arg == "-"

        output_path = (
            None if output_to_stdout or output_arg is None else Path(output_arg)
        )

        output_format = parsed_args.format

        if output_format is None:
            if output_path is not None and output_path.suffix.lower().lstrip(".") in {
                "html",
                "json",
                "dot",
            }:
                output_format = output_path.suffix.lower().lstrip(".")
            else:
                output_format = "html"

        if output_arg is None:
            output_path = Path(f"dependencies.{output_format}")

        config = AnalysisConfig(
            project_path=project_path,
            exclude_patterns=parsed_args.exclude,
            show_third_party=not parsed_args.no_third_party,
            show_stdlib=not parsed_args.no_stdlib,
            show_unknown=True,
            include_all=parsed_args.include_all,
            targets=parsed_args.target,
        )

        try:
            DepCycleCLI.run(
                config,
                output_path=output_path,
                output_format=output_format,
                impact_targets=parsed_args.impact,
                path_query=(
                    tuple(parsed_args.path) if parsed_args.path is not None else None
                ),
            )
        except KeyboardInterrupt:
            print("\nInterrupted by user", file=sys.stderr)
            sys.exit(1)
        except (
            OSError,
            RuntimeError,
            ValueError,
            SyntaxError,
            UnicodeDecodeError,
        ) as exc:
            print(
                f"Error: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)

    @staticmethod
    def _build_query_graph(project_path: Path) -> DependencyGraph:
        """Build a classified, unfiltered dependency graph for query commands."""
        project = Project(project_path)
        parser = ASTParser()
        metadata_reader = PackageMetadataReader()

        graph = DependencyGraph()

        files = project.get_python_files(
            exclude_patterns=AnalysisConfig(project_path=project_path).exclude_patterns,
        )

        graph.build(
            files,
            project.root_path,
            parser,
        )

        graph.classify(
            known_third_party=metadata_reader.read(project.root_path),
        )

        return graph

    @staticmethod
    def _query_module(graph: DependencyGraph, parsed_args: argparse.Namespace) -> None:
        """Handle `query module <name>`."""
        name = parsed_args.module_name
        node = graph.nodes.get(name)

        if node is None:
            print(json.dumps({"error": f"module not found: {name}"}))
            sys.exit(1)

        print(
            json.dumps(
                {
                    "module": node.name,
                    "type": node.module_type.value,
                    "file": relative_file_path(graph, node.file_path),
                    "fan_in": graph.fan_in(name),
                    "fan_out": graph.fan_out(name),
                }
            )
        )

    @staticmethod
    def _query_deps(graph: DependencyGraph, parsed_args: argparse.Namespace) -> None:
        """Handle `query deps <name>`."""
        name = parsed_args.module_name

        if name not in graph.nodes:
            print(json.dumps({"error": f"module not found: {name}"}))
            sys.exit(1)

        deps = sorted(dependency.name for dependency in graph.nodes[name].dependencies)
        print(json.dumps({"module": name, "deps": deps}))

    @staticmethod
    def _query_dependents(
        graph: DependencyGraph,
        parsed_args: argparse.Namespace,
    ) -> None:
        """Handle `query dependents <name>`."""
        name = parsed_args.module_name

        if name not in graph.nodes:
            print(json.dumps({"error": f"module not found: {name}"}))
            sys.exit(1)

        dependents = [node.name for node in graph.dependents(name)]
        print(json.dumps({"module": name, "dependents": dependents}))

    @staticmethod
    def _query_cycles(graph: DependencyGraph, parsed_args: argparse.Namespace) -> None:
        """Handle `query cycles [--module <name>]`."""
        cycles = graph.find_cycles()

        if parsed_args.module is not None:
            cycles = [
                cycle
                for cycle in cycles
                if any(node.name == parsed_args.module for node in cycle)
            ]

        print(
            json.dumps(
                {"cycles": [[node.name for node in cycle] for cycle in cycles]}
            )
        )

    @staticmethod
    def _query_neighborhood(
        graph: DependencyGraph,
        parsed_args: argparse.Namespace,
    ) -> None:
        """Handle `query neighborhood <name> [--depth N]`."""
        name = parsed_args.module_name

        if name not in graph.nodes:
            print(json.dumps({"error": f"module not found: {name}"}))
            sys.exit(1)

        neighborhood = sorted(
            node.name for node in graph.neighborhood(name, depth=parsed_args.depth)
        )

        print(
            json.dumps(
                {
                    "module": name,
                    "depth": parsed_args.depth,
                    "neighborhood": neighborhood,
                }
            )
        )

    _QUERY_HANDLERS = {
        "module": "_query_module",
        "deps": "_query_deps",
        "dependents": "_query_dependents",
        "cycles": "_query_cycles",
        "neighborhood": "_query_neighborhood",
    }

    @staticmethod
    def _main_query(parsed_args: argparse.Namespace) -> None:
        """Run the `query` subcommand: a compact JSON answer for one question."""
        project_path = Path(parsed_args.project_path)

        DepCycleCLI._validate_project_path(project_path)

        try:
            graph = DepCycleCLI._build_query_graph(project_path)
        except (
            OSError,
            RuntimeError,
            ValueError,
            SyntaxError,
            UnicodeDecodeError,
        ) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

        handler_name = DepCycleCLI._QUERY_HANDLERS[parsed_args.query_command]
        handler = getattr(DepCycleCLI, handler_name)
        handler(graph, parsed_args)

    @staticmethod
    def main(args: list[str] | None = None) -> None:
        """
        Main entry point for the DepCycle CLI.

        Args:
            args:
                Command-line arguments. Defaults to sys.argv[1:].
        """
        if args is None:
            args = sys.argv[1:]

        parser = DepCycleCLI._create_parser()
        parsed_args = parser.parse_args(args)

        if parsed_args.command == "query":
            DepCycleCLI._main_query(parsed_args)
            return

        DepCycleCLI._main_analyze(parsed_args)
