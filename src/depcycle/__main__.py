"""Entry point for running DepCycle as a module: python -m depcycle."""

from __future__ import annotations

from .cli import DepCycleCLI

if __name__ == "__main__":
    DepCycleCLI.main()
