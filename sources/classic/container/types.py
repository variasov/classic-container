from abc import ABC
from types import ModuleType
from typing import Any, Callable, Union, Type, Dict, List


Factory = Callable[[Any], Any]
Target = Union[Factory, Type[object], ABC]
Registry = Dict[Target, List[Factory]]

SettingsGroup = Dict[Factory, 'Settings']
SettingsRegistry = Dict[str, SettingsGroup]

ModuleOrTarget = Union[Target, ModuleType]
AnyFunc = Callable[[Any], Any]

InstancesRegistry = Dict[str, Dict[Type, Any]]
