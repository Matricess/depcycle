# Test Coverage Summary

This directory contains the project test suite for DepCycle. The tests cover parsing, graph logic, output writing, metadata detection, and CLI behavior.

## Coverage Areas

### CLI and integration
**File:** `tests/test_cli.py`
- Valid project execution
- Error handling for invalid paths
- CLI compatibility checks for output generation

### Graph logic and cycle detection
**File:** `tests/test_dependency_graph.py`
- Local dependency resolution
- Stdlib / third-party / unknown classification
- Cycle detection and filtering behavior

### Import parsing
**File:** `tests/test_ast_parser.py`
- Absolute, relative, and aliased imports
- Graceful handling of invalid Python files

### Project discovery
**File:** `tests/test_project.py`
- Recursive file scanning
- Default exclusion of common noise directories

### Output writers
**Files:** `tests/test_output_json.py`, `tests/test_output_dot.py`, `tests/test_output_html.py`
- JSON structure validation
- DOT syntax validation
- HTML generation checks

### Metadata detection
**File:** `tests/test_metadata.py`
- `pyproject.toml` parsing
- `requirements.txt` parsing

## Run the suite

```bash
uv sync
uv run pytest -q
```
