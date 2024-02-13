import inspect
from types import ModuleType
from typing import Sequence, Tuple, Generator

from .types import Factory, Registerable, Target


def _is_submodule(submodule: ModuleType, module: ModuleType) -> bool:
    return submodule.__name__.startswith(module.__name__)


def get_members(module: ModuleType) -> Tuple[Sequence[Registerable],
                                             Sequence[ModuleType]]:
    submodules = []
    targets = []

    for name, member in module.__dict__.items():
        if name.startswith('_'):
            continue
        if isinstance(member, ModuleType) and _is_submodule(member, module):
            submodules.append(member)
        elif inspect.isclass(member):
            targets.append(member)

    return targets, submodules


def get_interfaces_for_cls(
    target: type[Target],
) -> Generator[type[object], None, None]:

    for cls in target.__mro__:
        if cls != object:
            yield cls


def get_factory_result(factory: Factory[Target]) -> type[Target] | None:
    if inspect.isclass(factory):
        return factory

    signature = inspect.signature(factory)
    result = signature.return_annotation
    if result == inspect.Parameter.empty:
        return None

    return result


def is_factory(obj: object) -> bool:
    return inspect.isclass(obj) or inspect.isfunction(obj)
