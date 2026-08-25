Examples for trying DepCycle quickly

Contents
- clean_project: No cycles, simple layered imports
- messy_project: Intentional cycle between modules

How to run
- From repo root (this folder):

Clean (acyclic) graph, SVG:
```bash
uv run depcycle "examples/clean_project" -o clean_deps.svg --format svg
```

Messy graph, SVG (shows cycle warning):
```bash
uv run depcycle "examples/messy_project" -o messy_deps.svg --format svg
```

Tips
- Try adding or removing imports to see edges appear/disappear.
- Move an import to function scope to break a cycle without changing structure.
- Add -e "**/__pycache__" to ignore bytecode caches if present.



