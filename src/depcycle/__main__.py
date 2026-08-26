"""Entry point for running depcycle as a module: python -m depcycle"""

from .cli import DepCycleCLI

if __name__ == '__main__':
    DepCycleCLI.main()
