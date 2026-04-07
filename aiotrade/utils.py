"""General purpose utilities for aiotrade."""

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from decimal import Decimal
from typing import Any, TypeVar, overload


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


def float_to_str(val: float, *, use_exp: bool = False) -> str:
    """
    Convert a float to string, optionally using exponential (scientific) notation.

    Args:
        val (float): The float value to convert.
        use_exp (bool): If True, use exponential notation (str(val)).
            If False, convert to maximum available precision, avoiding scientific
            notation where possible.

    Returns:
        str: The float as a string, in the requested format.

    Notes:
        - When use_exp is False, this function uses `repr(val)` for as much precision
          as possible with machine representation.
        - If the repr is in scientific notation, convert to a decimal string
          with 17 digits (max safe double precision), avoiding scientific notation.
        - Removes unnecessary trailing zeros and periods.
        - Handles edge cases such as zero values.
    """
    if use_exp:
        return str(val)
    # Use repr to avoid rounding (almost full machine precision as str)
    s = repr(val)
    # Only switch to non-scientific if present, else leave as-is
    if "e" in s or "E" in s:
        # Convert to decimal with max double precision, avoid scientific
        # 17 digits are usually the max guaranteed precision for a double
        s = format(val, ".17f").rstrip("0").rstrip(".")
        if s == "":
            s = "0"
        elif "." in s and s[-1] == ".":
            s += "0"
    return s


@overload
def to_str_fields(
    d: Mapping[str, Any], fields: Iterable[str], use_exp: bool = False
) -> dict[str, Any]: ...
@overload
def to_str_fields(
    d: Sequence[Mapping[str, Any]], fields: Iterable[str], use_exp: bool = False
) -> list[dict[str, Any]]: ...


def to_str_fields(
    d: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    fields: Iterable[str],
    use_exp: bool = False,
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Convert specified fields to string in a params.

    Args:
        d: The original dict, TypedDict, or sequence thereof (not mutated).
        fields: Iterable of field names to be converted.
        use_exp: If True, allow string conversion of floats to use
            scientific notation when needed.
            If False (default), force decimal string with no scientific notation.

    Returns:
        A new dict with specified fields converted to strings,
        or a list of such dicts if given a sequence.
    """
    str_fields = set(fields)

    def convert_dict(obj: Mapping[str, Any]) -> dict[str, Any]:
        res: dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(v, Mapping):
                res[k] = convert_dict(v)  # pyright: ignore[reportUnknownArgumentType]
            elif isinstance(v, Sequence) and not isinstance(v, (str, bytes)):
                # If value is a sequence of mappings, recursively remap each
                res[k] = [convert_dict(item) for item in v]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
            if k in str_fields and isinstance(v, float):
                res[k] = float_to_str(v, use_exp=use_exp)
            elif k in str_fields and isinstance(v, int):
                res[k] = str(v)
            else:
                res[k] = v
        return res

    if isinstance(d, Mapping):
        return convert_dict(d)
    return [convert_dict(item) for item in d]


@overload
def remap(d: Mapping[str, Any], mapping: Mapping[str, str]) -> dict[str, Any]: ...
@overload
def remap(
    d: Sequence[Mapping[str, Any]], mapping: Mapping[str, str]
) -> list[dict[str, Any]]: ...


def remap(
    d: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    mapping: Mapping[str, str],
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Recursively remap fields in dict(s) according to a mapping.

    For each {src: dst} in mapping, move value
    from src to dst in the dict if src exists.
    If a value is itself a mapping, recursively apply remap with the same mapping.

    Args:
        d: The original dict, TypedDict, or sequence thereof (not mutated).
        mapping: Mapping of source fields to target fields.

    Returns:
        A new dict with remapped keys,
        or a list of such dicts if given a sequence.
    """

    def remap_dict(obj: Mapping[str, Any]) -> dict[str, Any]:
        res: dict[str, Any] = {}
        # First pass: recursive descend into sub-mappings
        for k, v in obj.items():
            # Only recursively remap if v is a mapping (but not a string)
            if isinstance(v, Mapping):
                res[k] = remap_dict(v)  # pyright: ignore[reportUnknownArgumentType]
            elif isinstance(v, Sequence) and not isinstance(v, (str, bytes)):
                # If value is a sequence of mappings, recursively remap each
                res[k] = [remap_dict(item) for item in v]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
            else:
                res[k] = v
        # Second pass: rename according to mapping
        for src, dst in mapping.items():
            if src in res:
                res[dst] = res.pop(src)
        return res

    if isinstance(d, Mapping):
        return remap_dict(d)
    return [remap_dict(item) for item in d]


def join_iterable_field(val: str | Iterable[str]) -> str:
    """
    Join an iterable values.

    Args:
        val: A string or any iterable of values.

    Returns:
        Comma-separated string of values, or the original
            string if a single string was provided.
    """
    if isinstance(val, str):
        return val
    return ",".join(str(v) for v in val)


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
    if isinstance(val, float):
        return Decimal(float_to_str(val))
    return Decimal(val)


def parse_float(val: Any) -> float | None:
    """
    Parse a value into a float if valid, else return None.

    Bybit sometimes returns floats as strings, empty strings for missing data,
    or "0.00" for zero values to be ignored.

    Args:
        val (Any): The input value to parse as float.

    Returns:
        float | None: Float value if successfully parsed, otherwise None.
    """
    if val is None or val in {"", "0.00"}:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
