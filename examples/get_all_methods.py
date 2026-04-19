"""List all implemented public methods on aiotrade client classes."""

import ast
import inspect
import textwrap
from collections import Counter
from contextlib import suppress
from typing import Any

from aiotrade import (
    BinanceClient,
    BingxClient,
    BitgetClient,
    BybitClient,
    GateClient,
    KuCoinClient,
    OkxClient,
)


def is_method(obj: Any) -> bool:
    """Return True if the object is a function or method."""
    return inspect.isfunction(obj) or inspect.ismethod(obj)


def returns_none_annotation(func: Any) -> bool:
    """Return True if function's return annotation is None or type(None)."""
    try:
        sig = inspect.signature(func)
        return sig.return_annotation is None or sig.return_annotation is type(None)
    except Exception:
        return False


def raises_notimplemented_in_body(func: Any) -> bool:
    """Return True if body contains 'raise NotImplementedError'."""
    try:
        source = inspect.getsource(func)
        # Remove method indentation if present
        if source.startswith(" "):  # crude but fast check
            source = textwrap.dedent(source)
        module = ast.parse(source)
        for node in ast.walk(module):
            if isinstance(node, ast.Raise):
                exc = node.exc
                # Covers: raise NotImplementedError or raise NotImplemented
                if isinstance(exc, ast.Name) and exc.id in {
                    "NotImplementedError",
                    "NotImplemented",
                }:
                    return True
                # Covers: raise NotImplementedError() or raise NotImplemented()
                if (
                    isinstance(exc, ast.Call)
                    and isinstance(exc.func, ast.Name)
                    and exc.func.id in {"NotImplementedError", "NotImplemented"}
                ):
                    return True
        return False
    except (OSError, TypeError, IndentationError, SyntaxError):
        return False


def is_effectively_not_implemented(func: Any) -> bool:
    """Return True if returns None or raises NotImplemented in body."""
    return returns_none_annotation(func) or raises_notimplemented_in_body(func)


def implemented_methods(client_cls: type) -> list[str]:
    """
    List implemented public method names of class, skipping non-implemented ones.
    Contains possible duplicates for duplicate check.
    """
    methods: list[str] = []
    for name, _member in inspect.getmembers(client_cls, predicate=is_method):
        if name.startswith("_"):
            continue
        with suppress(Exception):
            func = getattr(client_cls, name)
            if is_effectively_not_implemented(func):
                continue
            methods.append(name)
    excluded = {
        "close",
        "get",
        "post",
        "put",
        "delete",
        "set_recv_window",
        "set_dcp",
        "broker",
    }
    return [m for m in methods if m not in excluded]


def pretty_print_methods(title: str, methods: list[str]) -> None:
    # Deduplicate for pretty print view
    methods = sorted(set(methods))
    print(f"\n{title}")
    if not methods:
        print("  (none found)")
        return

    # Make it look like a nice compact table: 3 columns if possible
    cols = 2
    rows = (len(methods) + cols - 1) // cols
    maxlen = max((len(m) for m in methods), default=0) + 2
    table: list[list[str]] = []
    for r in range(rows):
        row: list[str] = []
        for c in range(cols):
            idx = r + c * rows
            if idx < len(methods):
                row.append(methods[idx])
            else:
                row.append("")
        table.append(row)
    for row in table:
        print("    " + "".join(m.ljust(maxlen) for m in row))


def report_duplicates(client_name: str, methods: list[str]) -> None:
    """Check and print duplicate public methods for the client."""
    counter = Counter(methods)
    duplicates = [m for m, count in counter.items() if count > 1]
    if duplicates:
        print(
            f"WARNING: {client_name} has duplicate public methods: "
            f"{', '.join(sorted(duplicates))}"
        )


def main() -> None:
    """Print all implemented public method names in a nice table."""
    client_data = [
        ("BybitClient", BybitClient),
        ("BingxClient", BingxClient),
        ("OkxClient", OkxClient),
        ("BitgetClient", BitgetClient),
        ("BinanceClient", BinanceClient),
        ("KuCoinClient", KuCoinClient),
        ("GateClient", GateClient),
    ]
    for client_name, client_cls in client_data:
        methods = implemented_methods(client_cls)
        report_duplicates(client_name, methods)
        # remove utility method
        if "decode_str" in methods:
            methods.remove("decode_str")
        pretty_print_methods(f"{client_name} methods ({len(set(methods))}):", methods)


if __name__ == "__main__":
    main()
