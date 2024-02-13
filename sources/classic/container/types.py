from abc import ABC
from types import ModuleType
from typing import TypeAlias, Callable, TypeVar


Target = TypeVar('Target', bound=object)
ModuleOrTarget: TypeAlias = Target | ModuleType
Factory: TypeAlias = type[Target] | Callable[[...], Target]
Registerable: TypeAlias = Factory | ABC
