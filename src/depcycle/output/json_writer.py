"""JSON output writer for dependency graphs."""

from __future__ import annotations

import json
from pathlib import Path

from .base import GraphExport, IOutputWriter


class JsonWriter(IOutputWriter):
    """Serialize a dependency graph to JSON."""

    def write(
        self,
        export: GraphExport,
        dest: Path | None = None,
    ) -> None:
        payload = {
            "schema_version": 1,
            "project": export.project,
            "summary": export.summary,
            "nodes": export.nodes,
            "edges": export.edges,
            "cycles": export.cycles,
        }

        text = json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )

        if dest is None:
            print(text)
            return

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
