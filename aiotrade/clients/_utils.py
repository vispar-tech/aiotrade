from collections.abc import Iterable, Mapping, Sequence
from typing import Any, overload


def _float_to_str(val: float, use_exp: bool) -> str:
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
                res[k] = _float_to_str(v, use_exp)
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
