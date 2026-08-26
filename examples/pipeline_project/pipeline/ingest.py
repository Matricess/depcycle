from pathlib import Path


def read_events(source: Path) -> list[dict[str, str]]:
    return [{"source": source.name, "event": "purchase"}]
