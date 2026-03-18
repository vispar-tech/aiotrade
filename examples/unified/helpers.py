import asyncio
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any, TypeVar

from aiotrade import ExchangeLiteral

T = TypeVar("T")


class RetryConditionNotMetError(Exception):
    """Retry attempts exceeded."""


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


def parse_decimal(val: Any) -> Decimal:
    """
    Parse any value into a Decimal.

    Args:
        val (Any): Value to be parsed, typically a string, int, float, etc.

    Returns:
        Decimal: The value parsed as a Decimal.

    Raises:
        decimal.InvalidOperation: If the value cannot be converted.
    """
    return Decimal(str(val))


def parse_float(val: Any) -> float | None:
    """
    Parse a value into a float if valid, else return None.

    Bybit sometimes returns floats as strings, empty strings for missing data,
    or "0.00" for zero values to be ignored.

    Args:
        val (Any): The input value to parse as float.

    Returns:
        float | None: The parsed float, or None.
    """
    try:
        return float(val) if val not in (None, "", "0.00") else None
    except (TypeError, ValueError):
        return None


def extract_symbol_asset(symbol: str) -> str:
    """
    Extracts the base asset from a trading symbol.

    E.g., 'BTCUSDT' -> 'BTC', 'ETH_USDT' -> 'ETH'.
    Takes into account symbols like 'BTC-USDT-SWAP', 'ETHUSDT', etc.
    Removes trailing '-' or '_'.
    """
    # Handle most common quote assets
    quote_assets = [
        "-USDT-SWAP",
        "-USDUSD",
        "-USDT",
        "-USDC",
        "-USD",
        "USDT",
        "USDC",
        "USDUSD",
        "USD",
    ]

    # Search for the longest quote first
    for asset in sorted(quote_assets, key=len, reverse=True):
        if symbol.endswith(asset):
            base = symbol[: -len(asset)]
            # Remove any trailing '-' or '_' before returning
            return base.rstrip("-_")

    # If symbol contains '_', treat part before as base
    if "_" in symbol:
        return symbol.split("_")[0].rstrip("-_")

    # If symbol contains '-', get the first
    # part only if common in format like BTC-USDT-SWAP
    if "-" in symbol:
        return symbol.split("-")[0].rstrip("-_")

    # Otherwise, fallback to entire symbol, stripped
    return symbol.rstrip("-_").lstrip()


def to_exchange_symbol(exchange: ExchangeLiteral, symbol: str) -> str:
    """Convert a symbol to the exchange-specific format."""
    asset = extract_symbol_asset(symbol)
    if exchange == "bingx":
        return asset + "-USDT"
    if exchange in {"bybit", "bitget", "binance"}:
        return asset + "USDT"
    if exchange == "okx":
        return asset + "-USDT-SWAP"
    if exchange == "kucoin":
        if asset == "BTC":
            return "XBTUSDTM"
        return asset + "USDTM"
    raise NotImplementedError(f"Exchange {exchange} not implemented")
