def save_daily_events(events: list[str], date: str) -> str:
    return f"warehouse://events/{date} ({len(events)} events)"
