# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""Command-line entry point for the realistic example."""

import json
from pathlib import Path

import requests
from rich.console import Console

from realistic_app.api.routes import create_order_route


def main() -> None:
    """Print a sample order result without making external requests."""
    order = create_order_route("order-001")
    payload = {"order_id": order.order_id, "working_directory": str(Path.cwd())}
    Console().print(json.dumps(payload))
    # requests is included to demonstrate a declared third-party dependency.
    _ = requests.__name__


if __name__ == "__main__":
    main()
