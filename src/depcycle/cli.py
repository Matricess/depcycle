"""Command-line interface for DepCycle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyzer import analyze_project
from .config import AnalysisConfig
from .output import DotWriter, HtmlWriter, JsonWriter, TextWriter, build_export

_WRITERS = {
    "html": HtmlWriter,
    "json": JsonWriter,
    "dot": DotWriter,
}


class DepCycleCLI:
    """Parse command-line arguments and orchestrate dependency workflows."""

    @staticmethod
    def _create_parser() -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            prog="depcycle",
            description="Visualize and inspect Python project dependencies",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s analyze /path/to/project
  %(prog)s analyze /path/to/project -o output.html
  %(prog)s analyze /path/to/project --fail-on-cycles
  %(prog)s inspect /path/to/project my_app.cli
  %(prog)s inspect /path/to/project --cycles
""",
        )

        subparsers = parser.add_subparsers(
            dest="command",
            required=True,
        )

        analyze_parser = subparsers.add_parser(
            "analyze",
            help="Analyze project dependencies and generate report output (HTML/JSON/DOT)",
        )
        analyze_parser.add_argument(
            "project_path",
            help="Path to the Python project directory",
        )
        analyze_parser.add_argument(
            "-o",
            "--output",
            help="Output file path (default: dependencies.<format>). Use '-' for stdout.",
            default=None,
        )
        analyze_parser.add_argument(
            "-f",
            "--format",
            choices=["html", "json", "dot"],
            help="Output format (default: inferred from output filename, otherwise html)",
            default=None,
        )
        analyze_parser.add_argument(
            "-e",
            "--exclude",
            action="append",
            help="Glob patterns to exclude. Can be specified multiple times.",
            default=None,
        )
        analyze_parser.add_argument(
            "--no-third-party",
            action="store_true",
            help="Exclude third-party dependencies from the graph",
        )
        analyze_parser.add_argument(
            "--no-stdlib",
            action="store_true",
            help="Exclude standard library modules from the graph",
        )
        analyze_parser.add_argument(
            "--no-unknown",
            action="store_true",
            help="Exclude unknown dependencies from the graph",
        )
        analyze_parser.add_argument(
            "--include-all",
            action="store_true",
            help="Include files normally excluded by default (venv, __pycache__, etc.)",
        )
        analyze_parser.add_argument(
            "--fail-on-cycles",
            action="store_true",
            help="Exit with status 1 if any circular dependencies are found (CI/CD integration)",
        )

        inspect_parser = subparsers.add_parser(
            "inspect",
            help="Inspect a specific module or query circular dependencies",
        )
        inspect_parser.add_argument(
            "project_path",
            help="Path to the Python project directory",
        )
        inspect_parser.add_argument(
            "module_name",
            nargs="?",
            default=None,
            help="Name of the module to inspect",
        )
        inspect_parser.add_argument(
            "--cycles",
            action="store_true",
            help="List all circular dependencies in the project",
        )
        inspect_parser.add_argument(
            "-e",
            "--exclude",
            action="append",
            help="Glob patterns to exclude",
            default=None,
        )

        query_parser = subparsers.add_parser(
            "query",
            help="Legacy subcommand alias for inspect",
        )
        query_parser.add_argument("project_path")
        query_parser.add_argument(
            "query_type",
            nargs="?",
            choices=["module", "deps", "dependents", "cycles", "neighborhood"],
            default=None,
        )
        query_parser.add_argument("module_name", nargs="?", default=None)
        query_parser.add_argument("--module", default=None)
        query_parser.add_argument("--depth", type=int, default=1)

        return parser

    @staticmethod
    def _validate_project_path(project_path: Path) -> None:
        """Exit with status 1 if project path is missing or not a directory."""
        if not project_path.exists():
            print(
                f"Error: Project path does not exist: {project_path}", file=sys.stderr
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
        """Run the analyze subcommand."""
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

        if output_arg is None and not output_to_stdout:
            output_path = Path(f"dependencies.{output_format}")

        config = AnalysisConfig.from_pyproject(
            project_path=project_path,
            cli_exclude=parsed_args.exclude,
            cli_show_third_party=not parsed_args.no_third_party,
            cli_show_stdlib=not parsed_args.no_stdlib,
            cli_show_unknown=not parsed_args.no_unknown,
            include_all=parsed_args.include_all,
            fail_on_cycles=parsed_args.fail_on_cycles,
        )

        print(f"Analyzing project: {config.project_path}", file=sys.stderr)
        graph, cycles = analyze_project(config)
        print(f"Found {len(graph.nodes)} modules", file=sys.stderr)

        if cycles:
            print(
                f"\nWarning: Found {len(cycles)} circular dependency cycles!",
                file=sys.stderr,
            )
            for i, cycle in enumerate(cycles[:5], start=1):
                cycle_names = [node.name for node in cycle]
                print(f"  Cycle {i}: {' → '.join(cycle_names)}", file=sys.stderr)
            if len(cycles) > 5:
                print(f"  ... and {len(cycles) - 5} more cycles", file=sys.stderr)
        else:
            print("✓ No circular dependencies detected", file=sys.stderr)

        writer_cls = _WRITERS.get(output_format)
        if writer_cls is None:
            raise ValueError(f"Unsupported output format: {output_format}")

        export = build_export(graph, cycles=cycles)
        print(f"\nGenerating {output_format.upper()} output...", file=sys.stderr)
        writer_cls().write(export, output_path)

        label = (
            "written to stdout" if output_path is None else f"saved to: {output_path}"
        )
        print(f"✓ {output_format.upper()} output {label}", file=sys.stderr)

        if config.fail_on_cycles and cycles:
            print(
                "\nError: Circular dependencies found and --fail-on-cycles is active.",
                file=sys.stderr,
            )
            sys.exit(1)

    @staticmethod
    def _main_inspect(parsed_args: argparse.Namespace) -> None:
        """Run the inspect / query subcommand."""
        project_path = Path(parsed_args.project_path)
        DepCycleCLI._validate_project_path(project_path)

        cli_exclude = getattr(parsed_args, "exclude", None)
        config = AnalysisConfig.from_pyproject(
            project_path=project_path,
            cli_exclude=cli_exclude,
        )

        graph, cycles = analyze_project(config)

        show_cycles_only = (
            getattr(parsed_args, "cycles", False)
            or getattr(parsed_args, "query_type", None) == "cycles"
        )
        target_module = getattr(parsed_args, "module_name", None) or getattr(
            parsed_args, "module", None
        )

        if show_cycles_only:
            result = TextWriter.format_cycles(cycles)
        elif target_module:
            result = TextWriter.format_inspection(graph, cycles, target_module)
            if "error" in result:
                print(json.dumps(result))
                sys.exit(1)
        else:
            result = TextWriter.format_cycles(cycles)

        print(json.dumps(result, indent=2))

    @staticmethod
    def main(args: list[str] | None = None) -> None:
        """Main entry point for DepCycle CLI."""
        if args is None:
            args = sys.argv[1:]

        parser = DepCycleCLI._create_parser()
        parsed_args = parser.parse_args(args)

        if parsed_args.command in ("inspect", "query"):
            DepCycleCLI._main_inspect(parsed_args)
        else:
            DepCycleCLI._main_analyze(parsed_args)
