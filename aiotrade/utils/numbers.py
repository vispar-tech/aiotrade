"""Utility functions for robust conversion and parsing of numerical values."""

from decimal import Decimal
from typing import Any

from .formatters import float_to_str


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
