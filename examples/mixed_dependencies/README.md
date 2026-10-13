# Mixed dependencies — intermediate

This project imports modules from three categories:

- local: `mixed_dependencies.settings`
- standard library: `json`, `pathlib`
- third-party: `requests`, `rich`

The root `pyproject.toml` declares `requests` and `rich`, allowing DepCycle to classify these imports using package metadata. The example is intended for static analysis; its third-party packages do not need to be installed just to parse the files.

Run:

```bash
depcycle analyze examples/mixed_dependencies --format json -o -
```
