import importlib
import inspect
import pkgutil
import types
from collections.abc import Sequence
from typing import Any, Literal, TypedDict

from rich.console import Console
from rich.tree import Tree

import aiotrade

console = Console()

MEMBER_KINDS = ("METHOD", "FUNC", "VAR", "CLASS", "PROPERTY")
MEMBER_KINDS_TO_SHOW: Sequence[str] = ("FUNC", "VAR", "CLASS", "PROPERTY")


class MethodMeta(TypedDict):
    kind: Literal["METHOD"]
    name: str
    qualname: str


class FuncMeta(TypedDict):
    kind: Literal["FUNC"]
    name: str
    qualname: str


class VarMeta(TypedDict):
    kind: Literal["VAR"]
    name: str
    qualname: str


class ClassMeta(TypedDict):
    kind: Literal["CLASS"]
    name: str
    qualname: str
    methods: list["MethodMeta"]
    properties: list["PropertyMeta"]


class PropertyMeta(TypedDict):
    kind: Literal["PROPERTY"]
    name: str
    qualname: str


MemberMeta = MethodMeta | FuncMeta | VarMeta | ClassMeta | PropertyMeta


def is_public(name: str) -> bool:
    return not name.startswith("_")


def is_public_module(modname: str) -> bool:
    """
    Returns True if the module name does not include any private (underscore-prefixed) packages or submodules.
    For example:
        aiotrade.unified.clients  -> True
        aiotrade.unified._clients.okx -> False
        aiotrade.__main__ -> False
        aiotrade._foo.bar -> False
    """
    return all(part and not part.startswith("_") for part in modname.split("."))


def is_my_object(module: types.ModuleType, obj: object) -> bool:
    """
    Accepts exported public objects from aiotrade modules even if originally
    defined in internal submodules (for example, UnifiedBinanceClient defined in _clients but exported in aiotrade.unified).
    Rationale: if it's public at the API package/module, and its __module__ starts with aiotrade, it's considered user-accessible.
    """
    modname = getattr(obj, "__module__", None)
    if not modname:
        return False
    if not modname.startswith("aiotrade"):
        return False
    # Accept objects even if their __module__ points to an internal/private submodule as long as they are reachable from a public module!
    try:
        mod = importlib.import_module(modname)
        modfile = getattr(mod, "__file__", "")
        return "aiotrade" in modfile
    except Exception as exc:
        console.print(f"[yellow]Warning: Exception in is_my_object: {exc}[/]")
        return True  # best effort fallback


def collect_public_members(
    module: types.ModuleType,
    seen: set[int] | None = None,
    prefix: str = "",
    member_kinds: Sequence[str] = MEMBER_KINDS_TO_SHOW,
) -> dict[str, list[MemberMeta]]:
    """
    Recursively collects all public aiotrade objects as {kind: [meta, ...]}.
    Only collects those member kinds listed in `member_kinds`.

    FIX: Accept public members that are re-exported by the public module/package,
    even if originally defined in a private/internal aiotrade submodule (just as __init__.py does).
    """
    if seen is None:
        seen = set()

    members: dict[str, list[MemberMeta]] = {k: [] for k in MEMBER_KINDS}
    # Only process modules that are aiotrade or submodules of aiotrade, and are public.
    if not (
        hasattr(module, "__name__")
        and module.__name__.startswith("aiotrade")
        and is_public_module(module.__name__)
    ):
        return {k: v for k, v in members.items() if k in member_kinds}

    module_name = getattr(module, "__name__", prefix)

    try:
        all_members = dir(module)
    except Exception as err:
        console.print(f"[yellow]Warning: Could not dir module {module}: {err}[/]")
        return {k: v for k, v in members.items() if k in member_kinds}

    for name in all_members:
        if not is_public(name):
            continue
        obj = getattr(module, name, None)
        if id(obj) in seen:
            continue
        # Only skip if the object looks non-aiotrade or is built-in/external
        if not is_my_object(module, obj):
            continue
        seen.add(id(obj))
        qualname = f"{module_name}.{name}"

        try:
            if (
                inspect.ismodule(obj)
                and getattr(obj, "__name__", "").startswith("aiotrade")
                and is_public_module(getattr(obj, "__name__", ""))
            ):
                submodule_name = getattr(obj, "__name__", f"{prefix}{name}")
                sub_members = collect_public_members(
                    obj,
                    seen=seen,
                    prefix=f"{submodule_name}.",
                    member_kinds=member_kinds,
                )
                for k in MEMBER_KINDS:
                    if k in member_kinds:
                        members[k].extend(sub_members.get(k, []))
            elif inspect.isclass(obj):
                if "CLASS" in member_kinds:
                    class_methods: list[MethodMeta] = []
                    class_properties: list[PropertyMeta] = []
                    for cls_member_name, cls_member in inspect.getmembers(obj):
                        if is_public(cls_member_name):
                            qual_cls_member = f"{qualname}.{cls_member_name}"
                            # Accept methods/properties if they look like aiotrade.* and
                            # are accessible via this class, even if defined on an internal/private aiotrade module.
                            if (
                                inspect.isfunction(cls_member)
                                or inspect.ismethod(cls_member)
                            ) and (is_my_object(module, cls_member)):
                                if "METHOD" in member_kinds:
                                    method_meta: MethodMeta = {
                                        "kind": "METHOD",
                                        "name": cls_member_name,
                                        "qualname": qual_cls_member,
                                    }
                                    class_methods.append(method_meta)
                            elif isinstance(cls_member, property):
                                fget = getattr(cls_member, "fget", None)
                                owner_module = (
                                    getattr(type(fget), "__module__", None)
                                    if fget
                                    else None
                                )
                                # Accept all property objects for aiotrade classes
                                if (
                                    owner_module
                                    and owner_module.startswith("aiotrade")
                                    and "PROPERTY" in member_kinds
                                ):
                                    prop_meta: PropertyMeta = {
                                        "kind": "PROPERTY",
                                        "name": cls_member_name,
                                        "qualname": qual_cls_member,
                                    }
                                    class_properties.append(prop_meta)
                    class_meta: ClassMeta = {
                        "kind": "CLASS",
                        "name": name,
                        "qualname": qualname,
                        "methods": class_methods,
                        "properties": class_properties,
                    }
                    members["CLASS"].append(class_meta)
            elif (
                inspect.isfunction(obj) or inspect.isbuiltin(obj)
            ) and "FUNC" in member_kinds:
                func_meta: FuncMeta = {
                    "kind": "FUNC",
                    "name": name,
                    "qualname": qualname,
                }
                members["FUNC"].append(func_meta)
            elif (
                not inspect.ismodule(obj)
                and not inspect.isclass(obj)
                and "VAR" in member_kinds
            ):
                var_meta: VarMeta = {
                    "kind": "VAR",
                    "name": name,
                    "qualname": qualname,
                }
                members["VAR"].append(var_meta)
        except Exception as exc:
            console.print(
                f"[yellow]Warning: Exception collecting member {qualname}: {exc}[/]"
            )
            continue

    return {k: v for k, v in members.items() if k in member_kinds}


def build_public_members_tree(
    module: types.ModuleType,
    seen: set[int] | None = None,
    prefix: str = "",
    member_kinds: Sequence[str] = MEMBER_KINDS_TO_SHOW,
) -> Any:
    """
    Return a rich.tree.Tree of all public aiotrade-defined objects, recursively.
    Only displays members listed in `member_kinds`.
    Accept exports from private/internal modules as long as they are imported on the public interface.
    """
    if seen is None:
        seen = set()
    if not (
        hasattr(module, "__name__")
        and module.__name__.startswith("aiotrade")
        and is_public_module(module.__name__)
    ):
        return None

    module_name = getattr(module, "__name__", prefix)
    tree = Tree(f"[bold blue]MODULE[/]: {module_name}")

    try:
        all_members = dir(module)
    except Exception as err:
        tree.add(f"[yellow]Warning: Could not dir module {module}: {err}[/]")
        return tree

    for name in all_members:
        if not is_public(name):
            continue
        obj = getattr(module, name, None)
        if id(obj) in seen:
            continue
        if not is_my_object(module, obj):
            continue
        seen.add(id(obj))
        try:
            if (
                inspect.ismodule(obj)
                and getattr(obj, "__name__", "").startswith("aiotrade")
                and is_public_module(getattr(obj, "__name__", ""))
            ):
                submodule_name = getattr(obj, "__name__", f"{prefix}{name}")
                sub_tree = build_public_members_tree(
                    obj,
                    seen=seen,
                    prefix=f"{submodule_name}.",
                    member_kinds=member_kinds,
                )
                if sub_tree:
                    tree.add(sub_tree)
            elif inspect.isclass(obj) and "CLASS" in member_kinds:
                class_branch = tree.add(f"[bold magenta]CLASS[/]: {prefix}{name}")
                for cls_member_name, cls_member in inspect.getmembers(obj):
                    if is_public(cls_member_name):
                        if (
                            (
                                inspect.isfunction(cls_member)
                                or inspect.ismethod(cls_member)
                            )
                            and is_my_object(module, cls_member)
                            and "METHOD" in member_kinds
                        ):
                            class_branch.add(
                                f"[green]METHOD[/]: {prefix}{name}.{cls_member_name}"
                            )
                        elif isinstance(cls_member, property):
                            fget = getattr(cls_member, "fget", None)
                            owner_module = (
                                getattr(type(fget), "__module__", None)
                                if fget
                                else None
                            )
                            if (
                                owner_module
                                and owner_module.startswith("aiotrade")
                                and "PROPERTY" in member_kinds
                            ):
                                class_branch.add(
                                    f"[yellow]PROPERTY[/]: "
                                    f"{prefix}{name}.{cls_member_name}"
                                )
            elif (
                inspect.isfunction(obj) or inspect.isbuiltin(obj)
            ) and "FUNC" in member_kinds:
                tree.add(f"[cyan]FUNC[/]: {prefix}{name}")
            elif (
                not inspect.ismodule(obj)
                and not inspect.isclass(obj)
                and "VAR" in member_kinds
            ):
                tree.add(f"[grey]VAR[/]: {prefix}{name}")
        except Exception as err:
            tree.add(f"[yellow]Exception on {name}: {err}[/]")
            continue
    return tree


def print_public_members(
    module: types.ModuleType,
    seen: set[int] | None = None,
    prefix: str = "",
    output_members: dict[str, list[MemberMeta]] | None = None,
    member_kinds: Sequence[str] = MEMBER_KINDS_TO_SHOW,
) -> None:
    """
    Pretty print public aiotrade objects as a tree.
    Print also the structured lists for selected member kinds.
    """
    tree = build_public_members_tree(
        module, seen=seen, prefix=prefix, member_kinds=member_kinds
    )
    if isinstance(tree, Tree):
        console.print(tree)

    if output_members is not None:
        meta = collect_public_members(
            module, seen=set(), prefix=prefix, member_kinds=member_kinds
        )
        for k in member_kinds:
            output_members[k].extend(meta.get(k, []))


def walk_and_import_submodules(
    package: types.ModuleType, prefix: str = "aiotrade."
) -> Any:
    """
    Yields all submodules of the package, imported, but only for aiotrade.* modules.
    Skips any modules that are private (have any _-prefixed component).
    """
    if (
        hasattr(package, "__name__")
        and package.__name__.startswith("aiotrade")
        and is_public_module(package.__name__)
    ):
        yield package
    pkg_path: list[str] = list(package.__path__) if hasattr(package, "__path__") else []
    for module_info in pkgutil.walk_packages(pkg_path, prefix):
        if not module_info.name.startswith("aiotrade"):
            continue
        if not is_public_module(module_info.name):
            continue
        try:
            mod = importlib.import_module(module_info.name)
            yield mod
        except Exception as e:
            console.print(f"[red]Could not import {module_info.name}: {e}[/]")


_header_text = (
    "[bold underline green]aiotrade:[/] [white]публичные доступные объекты для импорта "
    "(классы, методы, функции и переменные):[/]"
)

console.print(_header_text)

all_members: dict[str, list[MemberMeta]] = {k: [] for k in MEMBER_KINDS_TO_SHOW}

for mod in walk_and_import_submodules(aiotrade):
    print_public_members(
        mod, output_members=all_members, member_kinds=MEMBER_KINDS_TO_SHOW
    )
