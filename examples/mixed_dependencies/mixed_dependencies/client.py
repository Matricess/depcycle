# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""A small client wrapper showing a third-party dependency."""

import requests

from mixed_dependencies.settings import API_TIMEOUT_SECONDS


def fetch_status(url: str) -> int:
    """Fetch a URL and return its HTTP status code."""
    response = requests.get(url, timeout=API_TIMEOUT_SECONDS)
    return response.status_code
