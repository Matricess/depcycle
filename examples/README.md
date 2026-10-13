# DepCycle example projects

These five small projects progress from simple local imports to a more realistic dependency graph.

## Examples

| Example | Level | Demonstrates |
|---|---|---|
| `basic_app/` | Beginner | A few local modules and one-way dependencies |
| `layered_app/` | Easy | API → service → repository layering, fan-in, and fan-out |
| `mixed_dependencies/` | Intermediate | Local, standard-library, and declared third-party imports |
| `cyclic_app/` | Intermediate | One two-module cycle and one three-module cycle |
| `realistic_app/` | Advanced | Multiple packages, declared third-party dependencies, exclusions, and an intentional architectural cycle |

## Run them

From the DepCycle repository root, with DepCycle installed or otherwise available on your `PATH`:

```bash
depcycle analyze examples/basic_app --format html -o basic-report.html
depcycle analyze examples/layered_app --format dot -o layered.dot
depcycle analyze examples/mixed_dependencies --format json -o mixed-report.json
depcycle inspect examples/cyclic_app --cycles
depcycle analyze examples/realistic_app --format html -o realistic-report.html
```

For a quick terminal-only export, use `--output -`, for example:

```bash
depcycle analyze examples/cyclic_app --format dot -o -
```

The cycles in `cyclic_app/` and `realistic_app/` are intentional, so they can be used to test cycle reporting and `--fail-on-cycles`.

## Import style note

The examples use package-qualified imports such as `from basic_app.greetings import greeting`. This lets the current analyzer match import targets to module names consistently. The current implementation records relative imports like `from . import helper` as `.helper` without resolving that name to the corresponding local module, so relative-import resolution should be improved separately before using relative imports in these examples.
