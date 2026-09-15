import time
from typing import Callable, TypeVar

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# Shared by every hosted media backend (fal/gemini/higgsfield/leonardo/openai/*_video) so a
# transient network/5xx error doesn't fail a whole post generation.
DEFAULT_RETRY = retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)


def download_bytes(url: str, timeout: int = 60, headers: dict | None = None) -> bytes:
    """GET a URL and return its body — the common last step of every backend that returns a
    result as a hosted file URL rather than inline bytes (fal, higgsfield, leonardo, video jobs)."""
    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()
    return response.content


T = TypeVar("T")


def poll_until(check: Callable[[], T | None], timeout_s: int, interval_s: int) -> T | None:
    """
    Calls `check()` every `interval_s` seconds until it returns a non-None result, or gives up and
    returns None once `timeout_s` has elapsed — the caller raises its own backend-specific timeout
    error. `check` may itself raise for a hard failure status (e.g. a job's FAILED state); that
    propagates immediately instead of waiting out the timeout.
    """
    deadline = time.monotonic() + timeout_s
    while True:
        time.sleep(interval_s)
        result = check()
        if result is not None:
            return result
        if time.monotonic() >= deadline:
            return None
