from abc import ABC
from collections import defaultdict
from functools import lru_cache
from itertools import chain
import inspect
from types import ModuleType
from typing import Optional, Callable

from .types import Factory, Registerable, ModuleOrTarget, Target

from . import utils


class Registry:
    """
    Хранит в себе информацию о классах, их фабриках и их зависимостях.

    Предполагается что этот объект инстанцируется контейнером
    и используется только "под капотом".
    """

    _storage = dict[Target, list[Factory[Target]]]

    def __init__(self):
        self._storage = defaultdict(list)
        self._signatures_cache = {}

    @lru_cache(1000)
    def signature(self, cls: Target) -> inspect.Signature:
        return inspect.signature(cls)

    def get(self, target: Target) -> Factory[Target]:
        factories = self._storage.get(target)

        if not factories:
            raise ValueError(
                f'Class {target} do not have registered implementations.\n'
            )

        if len(factories) > 1:
            raise ValueError(
                f'Can not to resolve {target}, '
                f'implementations are: {factories}\n'
            )

        return factories[0]

    def register(self, *targets: ModuleOrTarget) -> None:
        for target in targets:
            if self._register(target) is None:
                raise ValueError(
                    f'Registration target must be class, '
                    f'function or module, {target} is {type(target)}'
                )

    def _register(self, target: ModuleOrTarget) -> Optional[str]:
        result = None

        if inspect.ismodule(target):
            self._register_module(target)
            result = 'module'

        elif inspect.isabstract(target):
            self._register_interface(target)
            result = 'interface'

        elif inspect.isfunction(target):
            self._register_function(target)
            result = 'function'

        elif inspect.isclass(target):
            self._register_class(target)
            result = 'class'

        return result

    def _register_interface(self, interface: ABC) -> None:
        self._add_entry(interface)

    def _register_class(self, cls: type[object]) -> None:
        self._add_entry(cls, cls)
        for ancestor in utils.get_interfaces_for_cls(cls):
            self._add_entry(ancestor, cls)

    def _register_function(self, func: Callable) -> None:
        factory_returns = utils.get_factory_result(func)
        if not inspect.isclass(factory_returns):
            return

        self._add_entry(factory_returns, func)

    def _register_module(self, module: ModuleType) -> None:
        targets, submodules = utils.get_members(module)
        for target in chain(targets, submodules):
            self._register(target)

    def _add_entry(
        self, cls: Registerable,
        factory: Optional[Factory[Target]] = None,
    ) -> None:
        factories = self._storage[cls]
        if factory is not None and factory not in factories:
            factories.append(factory)
