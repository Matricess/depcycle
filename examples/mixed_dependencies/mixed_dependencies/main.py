# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""Entry point showing several kinds of imports."""

import json
from pathlib import Path

from rich.console import Console

from mixed_dependencies.client import fetch_status
from mixed_dependencies.settings import APP_NAME


def describe_project() -> str:
    """Return a JSON description without making a network request."""
    return json.dumps({"name": APP_NAME, "directory": str(Path.cwd())})


def main() -> None:
    """Print the project description."""
    console = Console()
    console.print(describe_project())
    console.print(f"Example HTTP status: fetch_status is available ({fetch_status.__name__})")


if __name__ == "__main__":
    main()
