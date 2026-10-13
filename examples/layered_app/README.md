# Layered app — easy

A small layered application with API, service, repository, and model modules. Dependencies flow toward lower-level modules.

Expected relationships include:

```text
layered_app.api → layered_app.services
layered_app.services → layered_app.repositories
layered_app.services → layered_app.models
layered_app.repositories → layered_app.models
```

The model is used by both the service and repository, which gives it multiple dependents (fan-in).

Run:

```bash
depcycle analyze examples/layered_app --format dot -o -
```
