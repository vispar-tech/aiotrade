"""Retry utilities for aiotrade."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar


class RetryConditionNotMetError(Exception):
    """Retry attempts exceeded."""


T = TypeVar("T")


async def retry_async_function(
    async_func: Callable[..., Awaitable[T | None]],
    condition: Callable[[T | None], bool] = lambda result: result is not None,
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Retry an async function until a condition is met or the max attempts are reached.

    Args:
        condition: Function that determines if the result is acceptable.
        async_func: Async function to call, may return None.
        max_attempts: Maximum number of attempts.
        delay_seconds: Time to wait between attempts in seconds.
        *args, **kwargs: Arguments to pass to async_func.

    Returns:
        The result from async_func that satisfies the condition.

    Raises:
        RetryConditionNotMetError: If max attempts are exceeded without satisfying
            condition.
    """
    for attempt in range(max_attempts):
        result = await async_func(*args, **kwargs)
        if condition(result):
            return result  # type: ignore
        if attempt < max_attempts - 1:
            await asyncio.sleep(delay_seconds)
    raise RetryConditionNotMetError("Condition not met after maximum retries")
