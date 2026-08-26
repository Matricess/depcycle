# DepCycle

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Matricess/depcycle/actions/workflows/ci.yml/badge.svg)](https://github.com/Matricess/depcycle/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/depcycle)](https://pepy.tech/project/depcycle)
[![PyPI](https://img.shields.io/pypi/v/depcycle.svg)](https://pypi.org/project/depcycle/)

DepCycle is a Python dependency analysis tool that inspects a project, builds a module graph, classifies imports, and emits browser-friendly or machine-friendly outputs for review.

## Features

- AST-based import discovery across a Python project
- Local / stdlib / third-party / unknown classification
- Dependency cycle detection and reporting
- Output writers for HTML, JSON, and DOT
- Project metadata scanning via pyproject.toml, requirements.txt, and similar files
- CLI filtering for third-party and stdlib visibility

## Installation

```bash
uv sync
```

Or install from a clone:

```bash
git clone https://github.com/Matricess/depcycle.git
cd depcycle
uv sync
```

## Usage

### Default HTML output

```bash
uv run depcycle /path/to/your/project
```

This writes an HTML report to `dependencies.html` by default.

### JSON output

```bash
depcycle /path/to/your/project -f json -o deps.json
```

### DOT output

```bash
depcycle /path/to/your/project -f dot -o deps.dot
```

### Example projects

The repository includes three small projects for trying the analyzer:

```bash
uv run depcycle examples/clean_project -f html -o clean-project.html
uv run depcycle examples/pipeline_project -f dot -o pipeline-project.dot
uv run depcycle examples/messy_project -f json -o messy-project.json
```

`clean_project` is an e-commerce order flow with no cycles. `pipeline_project`
models an analytics ingestion and reporting pipeline. `messy_project` contains
an intentional checkout dependency cycle.

HTML is the interactive browser report, JSON is the machine-readable report,
and DOT is Graphviz-compatible directed graph text.

### Override the output destination

```bash
depcycle /path/to/your/project -f html -o reports/project-deps.html
```

### Filter noisy modules

```bash
depcycle /path/to/your/project --no-third-party --no-stdlib
```

### Exclude patterns

```bash
depcycle /path/to/your/project -e venv -e "tests/*.py" -e "*.generated.py"
```

### Full help

```bash
uv run depcycle --help
```

> By default, common noise directories such as `.venv`, `venv`, `__pycache__`, `.git`, and build artifacts are excluded automatically.

## Project Structure

```text
depcycle/
├── src/
│   └── depcycle/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── graph.py
│       │   └── node.py
│       ├── output/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── dot_writer.py
│       │   ├── html_writer.py
│       │   └── json_writer.py
│       ├── parsing/
│       │   ├── __init__.py
│       │   ├── ast_parser.py
│       │   ├── metadata.py
│       │   └── project.py
│       └── py.typed
├── tests/
├── README.md
├── LICENSE
└── pyproject.toml
```

## Architecture

DepCycle follows a modular design:

1. CLI layer: parses options and orchestrates analysis
2. Configuration layer: analysis settings only, without output concerns
3. Graph layer: resolves import relationships and identifies cycles
4. Parsing layer: discovers Python files and extracts imports
5. Metadata layer: inspects dependency declarations in project files
6. Output layer: writes HTML, JSON, or DOT data

## Key Classes

- `DepCycleCLI`: CLI entry point
- `DependencyGraph`: core graph model
- `ModuleNode`: per-module state and metadata
- `ASTParser`: imports from Python source
- `PackageMetadataReader`: reads third-party names from project metadata
- `JsonWriter`: JSON serialization
- `DotWriter`: DOT graph serialization
- `HtmlWriter`: self-contained HTML visualization

## How It Works

1. Discover Python source files in the target project.
2. Parse each file with Python's AST.
3. Resolve local imports and classify external ones.
4. Read metadata files such as `pyproject.toml` and `requirements.txt` to detect known third-party packages.
5. Detect cycles and produce the requested output.

## Example Output

Typical CLI output:

```text
Analyzing project: /path/to/my-project
Building dependency graph...
Found 42 modules
✓ No circular dependencies detected
Generating HTML output...
✓ HTML output saved to: dependencies.html
```

If cycles are detected, the CLI prints a warning with the offending chain.

## Tests

Run the suite with:

```bash
uv run pytest -q
```

Install the pre-commit hooks once, then run the same checks locally before
committing:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

The hooks run Ruff and the full pytest suite. CI runs the same pre-commit
checks on every push to `main` and every pull request.

## Contributing

Contributions are welcome.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
