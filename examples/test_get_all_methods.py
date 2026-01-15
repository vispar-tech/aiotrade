"""List all implemented public methods on aiotrade client classes."""

import ast
import inspect
from contextlib import suppress
from typing import Any, List

from aiotrade import BingxClient, BybitClient


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
            import textwrap

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


def implemented_methods(client_cls: type) -> List[str]:
    """List implemented public method names of class, skipping non-implemented ones."""
    methods: List[str] = []
    for name, _member in inspect.getmembers(client_cls, predicate=is_method):
        if name.startswith("_"):
            continue
        with suppress(Exception):
            func = getattr(client_cls, name)
            if is_effectively_not_implemented(func):
                continue
            methods.append(name)
    excluded = {"close", "get", "post", "put", "delete", "set_recv_window", "set_dcp"}
    filtered_methods = [m for m in methods if m not in excluded]
    return sorted(set(filtered_methods))


def main() -> None:
    """Print all implemented BybitClient and BingxClient public method names."""
    print("Implemented BybitClient methods:")
    for method in implemented_methods(BybitClient):
        print(f" - {method}")
    print("\nImplemented BingxClient methods:")
    for method in implemented_methods(BingxClient):
        print(f" - {method}")


if __name__ == "__main__":
    main()
