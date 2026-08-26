# Examples

These projects are intentionally small but model familiar application shapes:

- `clean_project`: an e-commerce order flow across catalog, payments, shipping,
	and domain packages. It has no circular dependencies.
- `pipeline_project`: an analytics pipeline that ingests events, transforms
	them, stores daily data, and produces a report.
- `messy_project`: a checkout service where repositories, domain events, and
	notifications form a cross-layer cycle.

Run the CLI from the repository root:

```bash
depcycle examples/clean_project -f html -o /tmp/clean-project.html
depcycle examples/pipeline_project -f dot -o /tmp/pipeline-project.dot
depcycle examples/messy_project -f json -o /tmp/messy-project.json
```
