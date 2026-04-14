"""Date and time utilities for aiotrade."""

from collections.abc import Generator
from typing import Any


def iter_periods(
    start_ts: int, end_ts: int, period_ms: int
) -> Generator[tuple[int, int], Any, None]:
    """Yield intervals of period_ms between start_ts and end_ts, all in ms."""
    ts = start_ts
    while ts < end_ts:
        window_end = min(ts + period_ms, end_ts)
        yield ts, window_end
        ts += period_ms
