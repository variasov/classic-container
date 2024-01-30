from abc import ABC
from types import ModuleType
from typing import Any, Callable, Union, Type, Dict, List, Protocol


class RegisterCallable(Protocol):
    def __call__(self, *args: Any):
        pass


Factory = Union[Type[object], Callable[[Any], Any]]
Target = Union[Type[object], ABC]
Registerable = Union[Factory, Type[object], ABC]
Registry = Dict[Target, List[Factory]]

ModuleOrTarget = Union[Target, ModuleType]
AnyFunc = Callable[[Any], Any]

InstancesRegistry = Dict[str, Dict[Type, Any]]
