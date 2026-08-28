"""
This module contains the command-line interface logic for DepCycle.
It defines the user-facing commands, parses arguments, and orchestrates
the dependency analysis and visualization workflow.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import AnalysisConfig
from .graph.graph import DependencyGraph
from .output import DotWriter, HtmlWriter, JsonWriter, build_export
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
    def _create_parser() -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            prog="depcycle",
            description="Visualize Python project dependencies",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s /path/to/project
  %(prog)s /path/to/project -o output.html
  %(prog)s /path/to/project --format dot --exclude tests
  %(prog)s /path/to/project --no-third-party --no-stdlib
  %(prog)s /path/to/project --include-all
  %(prog)s /path/to/project -o -
""",
        )

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

        return parser

    @staticmethod
    def run(
        config: AnalysisConfig,
        output_path: Path | None = None,
        output_format: str = "html",
    ) -> None:
        """Execute the dependency analysis and visualization workflow."""
        print(f"Analyzing project: {config.project_path}")

        project = Project(config.project_path)
        parser = ASTParser()
        metadata_reader = PackageMetadataReader()

        print("Building dependency graph...")

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

        print(f"Found {len(graph)} modules")

        cycles = graph.find_cycles()

        if cycles:
            print(f"\n⚠️  Warning: Found {len(cycles)} circular dependency cycles!")

            for i, cycle in enumerate(cycles[:5], start=1):
                cycle_names = [node.name for node in cycle]
                print(f"  Cycle {i}: {' → '.join(cycle_names)}")

            if len(cycles) > 5:
                print(f"  ... and {len(cycles) - 5} more cycles")
        else:
            print("✓ No circular dependencies detected")

        writer_cls = _WRITERS.get(output_format)

        if writer_cls is None:
            raise ValueError(f"Unsupported output format: {output_format}")

        export = build_export(
            graph,
            cycles=cycles,
        )

        print(f"\nGenerating {output_format.upper()} output...")

        writer_cls().write(
            export,
            output_path,
        )

        label = (
            "written to stdout" if output_path is None else f"saved to: {output_path}"
        )

        print(f"✓ {output_format.upper()} output {label}")

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

        project_path = Path(parsed_args.project_path)

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
        )

        try:
            DepCycleCLI.run(
                config,
                output_path=output_path,
                output_format=output_format,
            )
        except KeyboardInterrupt:
            print("\nInterrupted by user")
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
