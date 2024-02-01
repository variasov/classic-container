from abc import ABC
from types import ModuleType
from typing import Protocol, TypeAlias


class RegisterCallable(Protocol):

    def __call__(self, *args: object) -> None:
        pass


class AnyFunc(Protocol):

    def __call__(self, *args: object, **kwargs: object) -> object:
        pass


Factory: TypeAlias = type | AnyFunc
Target: TypeAlias = type | ABC
Registerable: TypeAlias = Factory | type | ABC
Registry: TypeAlias = dict[Target, list[Factory]]
ModuleOrTarget: TypeAlias = Target | ModuleType
InstancesRegistry: TypeAlias = dict[Target, object]
