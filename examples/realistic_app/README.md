# Realistic app — advanced

A compact order-processing application demonstrating a multi-package layout, a service/repository/model flow, standard-library imports, declared third-party packages, excluded directories, and one intentional architectural cycle.

The intended main flow is:

```text
realistic_app.main → realistic_app.api.routes
realistic_app.api.routes → realistic_app.services.orders
realistic_app.services.orders → realistic_app.repositories.orders
realistic_app.services.orders → realistic_app.models.order
realistic_app.repositories.orders → realistic_app.models.order
```

There is also an intentional cycle:

```text
realistic_app.services.orders ↔ realistic_app.notifications.sender
```

`tests/` and `scripts/` contain fixture files that should be skipped by DepCycle's default exclusion patterns. `pyproject.toml` declares the `requests` and `rich` distributions for third-party classification.

Run:

```bash
depcycle analyze examples/realistic_app --format html -o realistic-report.html
depcycle inspect examples/realistic_app --cycles
```

The example uses package-qualified imports because the current analyzer does not yet resolve relative imports such as `from .orders import ...` into their full local module names.
