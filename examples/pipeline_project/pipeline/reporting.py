from pathlib import Path

from pipeline.storage import save_daily_events
from pipeline.transform import normalize


def daily_summary(date: str) -> str:
    events = normalize(Path("events.jsonl"))
    return save_daily_events(events, date)
