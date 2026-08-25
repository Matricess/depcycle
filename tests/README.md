# Test Coverage Summary

This directory contains the comprehensive test suite for DepCycle. The tests are designed to cover all **Key Functionalities** of the application, ensuring robustness, accuracy, and deployment readiness.

## Key Functionalities Covered

### 1. CLI & Integration (End-to-End)
**File:** `tests/test_cli.py`
* **Functionality Tested:** The application entry point, argument parsing, and workflow orchestration.
* **Scenarios:**
    * **Happy Path:** Running against a valid project to ensure artifacts are created.
    * **Error Handling:** Graceful exit when provided invalid paths.
    * **Mocking:** We use `unittest.mock` to simulate the Graphviz visualizer. This ensures tests pass in CI/CD environments even if the Graphviz binary is missing, making the suite robust and portable.

### 2. Cycle Detection & Graph Logic
**File:** `tests/test_dependency_graph.py`
* **Functionality Tested:** Core algorithms for graph building and cycle detection.
* **Scenarios:**
    * **Cycle Detection:** Verifies the Depth-First Search (DFS) algorithm accurately detects circular dependency chains.
    * **Dynamic Resolution:** Ensures external dependencies (like `requests` or `os`) are automatically detected and classified, preventing crashes.
    * **Filtering:** Tests flags like `--no-stdlib` to ensure they effectively prune the graph.

### 3. Import Parsing Strategy
**File:** `tests/test_ast_parser.py`
* **Functionality Tested:** Extracting imports from Python source code using Abstract Syntax Trees (AST).
* **Scenarios:**
    * **Complex Imports:** Handling aliased (`import numpy as np`), relative (`from . import utils`), and absolute imports.
    * **Resilience:** Ensuring the parser handles broken code (files with `SyntaxError`) gracefully without crashing the entire tool.

### 4. Project Discovery & Exclusion
**File:** `tests/test_project.py`
* **Functionality Tested:** File system traversal and exclusion logic.
* **Assertion:** Verifies that high-noise directories (`venv`, `node_modules`, `__pycache__`) are excluded by default to optimize performance.

## How to Run
We use `pytest` for execution with a centralized `conftest.py` fixture configuration.

```bash
# Install project and test dependencies
uv sync

# Run all tests (should pass 17/17)
uv run pytest -v
```
