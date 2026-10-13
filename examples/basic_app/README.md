# Basic app — beginner

A tiny project with a direct one-way dependency chain. Start here to understand nodes and edges.

Expected local relationships:

```text
basic_app.main → basic_app.greetings
basic_app.main → basic_app.formatting
basic_app.formatting → basic_app.greetings
```

Run from the repository root:

```bash
depcycle analyze examples/basic_app --format dot -o -
```
