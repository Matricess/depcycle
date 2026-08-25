# DepCycle

[![Python
3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License:
MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/depcycle)](https://pepy.tech/project/depcycle)
[![Downloads per
month](https://img.shields.io/pypi/dm/depcycle.svg)](https://pypi.org/project/depcycle/)

**DepCycle** is a command-line tool to visualize Python project dependencies. It helps developers understand complex codebases by automatically generating visual maps of how modules are connected, making it easy to spot architectural problems like **circular dependencies** and untangle coupled code.

## Features

- **Automatic Dependency Discovery**: Scans Python projects and builds a complete dependency graph
- **Cycle Detection**: Identifies circular dependencies that can lead to architectural issues
- **Flexible Visualization**: Multiple output formats including PNG, SVG, and HTML
- **Smart Filtering**: Exclude specific patterns, third-party libraries, or standard library modules
- **AST-Based Parsing**: Uses Python's Abstract Syntax Tree for accurate import detection

## Links

- **Repository:** https://github.com/Matricess/depcycle.git
- **Tests:** https://github.com/Matricess/depcycle/tree/main/tests
- **Design commentary:** https://github.com/Matricess/depcycle/blob/main/DESIGN.md
- **Sample dependency graph:** `examples/` (local)

## Prerequisites

- Python 3.8 or higher
- [Graphviz](https://graphviz.org/download/) (for PNG/SVG output)

### Installing Graphviz

The Python `graphviz` package is installed by uv. The Graphviz system
executable is also required for PNG and SVG output.

**macOS:**
```bash
brew install graphviz
```

**Ubuntu/Debian:**
```bash
sudo apt-get install graphviz
```

**Windows:**
Download and install from [Graphviz website](https://graphviz.org/download/)

## Installation

### Install with uv

```bash
uv sync
```

### Install from a clone (editable dev setup)

```bash
git clone https://github.com/Matricess/depcycle.git
cd depcycle
uv sync
```

## Usage

### Basic Usage

Analyze a Python project and generate a dependency graph (PNG by default):

```bash
uv run depcycle /path/to/your/project
```

The output is written to `dependencies.png` in the current working directory.

> **Note:** By default DepCycle skips common noise directories such as `venv/`, `.venv/`, `.git/`, `__pycache__/`, `node_modules/`, build artifacts, and Python cache folders. Use `-e` flags if you need extra exclusions, or disable the defaults via the API (`Project.get_python_files(include_defaults=False)`).

### Using as a Module

```bash
uv run python -m depcycle /path/to/your/project
```

### Advanced Options

Generate a different output format or explicit location:

```bash
uv run depcycle /path/to/project --format svg --output diagrams/dependencies.svg
```

Exclude specific directories or files (glob syntax):

```bash
uv run depcycle /path/to/project -e venv -e ".*/tests/*" -e "*.test.py"
```

Focus only on local code:

```bash
uv run depcycle /path/to/project --no-third-party --no-stdlib
```

**Full help:**

```bash
uv run depcycle --help
```

## Tests

Tests live under `tests/` and run without touching the sample projects in `examples/`.

```bash
uv sync
uv run pytest -q
```

See [`tests/README.md`](tests/README.md) for a quick summary.

## Project Structure

```
depcycle/
├── src/
│   └── depcycle/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py                  # Command-line interface
│       ├── config.py               # Configuration management
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── dependency_graph.py # Core graph logic
│       │   └── module_node.py      # Module representation
│       ├── parsing/
│       │   ├── __init__.py
│       │   ├── ast_parser.py       # AST-based import parsing
│       │   └── project.py          # File discovery
│       └── rendering/
│           ├── __init__.py
│           ├── interface.py        # Visualization interface
│           └── visualizers.py      # Output implementations
├── README.md
└── LICENSE
```

## Architecture

DepCycle follows a clean, modular architecture:

1. **CLI Layer** (`cli.py`): Handles user input and orchestrates the workflow
2. **Configuration** (`config.py`): Manages all settings and options
3. **Graph Layer** (`graph/`): Core data structures for the dependency graph
4. **Parsing Layer** (`parsing/`): Discovers files and extracts imports using AST
5. **Rendering Layer** (`rendering/`): Generates visualizations in various formats

## Key Classes

- **`DepCycleCLI`**: Main entry point that handles command-line arguments
- **`DependencyGraph`**: Central data structure holding all module relationships
- **`ModuleNode`**: Represents a single Python module/file
- **`Project`**: Discovers and manages Python files in a project
- **`ASTParser`**: Extracts imports using Python's AST module
- **`GraphvizVisualizer`**: Renders graphs as PNG/SVG images
- **`HtmlVisualizer`**: Generates interactive HTML visualizations

## How It Works

1. **Discovery**: Recursively scans the project directory for all `.py` files
2. **Parsing**: Uses Python's AST to extract import statements from each file
3. **Resolution**: Maps import strings to actual modules in the project
4. **Classification**: Categorizes modules as LOCAL, THIRD_PARTY, or STDLIB
5. **Analysis**: Detects circular dependencies using depth-first search
6. **Visualization**: Renders the graph using Graphviz or HTML

## Example Output

When you run DepCycle, you'll see output like:

```
Analyzing project: /path/to/my-project
Building dependency graph...
Found 42 modules
✓ No circular dependencies detected
Generating PNG visualization...
✓ Visualization saved to: dependencies.png
```

If circular dependencies are found:

```
⚠️  Warning: Found 2 circular dependency cycles!
  Cycle 1: app.models.user → app.services.auth → app.models.user
  Cycle 2: app.core.database → app.core.config → app.core.database
```

## Analytics
-   https://pepy.tech/project/depcycle
-   https://pypistats.org/packages/depcycle

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built as part of a Software Design and Testing course project (IT643).
