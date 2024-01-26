from abc import ABC
import threading
from itertools import chain
import inspect
from types import ModuleType
from typing import Optional, Type

from .types import Factory, Registerable, Registry, ModuleOrTarget, AnyFunc
from .exceptions import RegistrationError

from . import utils


class Registrator:
    """
    Класс производит регистрацию компонентов приложеия.
    Выглядит как метод register у контейнера.

    Объект этого класса нужен для регистрации в контейнере компонентов
    приложения. Предполагается что этот объект инстанцируется контейнером
    и используется только "под капотом".
    Выглядит как метод register у контейнера.
    """

    def __init__(self, registry: Registry, lock: threading.RLock):
        self._registry = registry
        self._lock = lock

    def __call__(self, *targets: ModuleOrTarget) -> None:
        """
        При обращении принимает список компонентов.
        Определяет тип, заносит в реестр, каждому типу сопоставляет
        список фабрик, способных построить указанный тип.

        Элементами списка могут быть: абстрактные классы, классы,
        фабрики (функции, возвращающие один инстанс любого класса) и модули.

        - Абстрактные классы регистрирутся в реестрестре только как ключи,
          без фабрик.
        - Нормальные классы регистрируются как ключ и соответсвующая ему
          фабрика - конструктор самого класса.
        - Фабрики регистрируются сложнее, ключем будет являтся результат из
          аннотации функции, а значением сама фабрика. Пример:
          >>> def some_factory() -> SomeClass:
          ...     # будет зарегистрировано как SomeClass: [some_factory]
          ...     pass

        - Модули не регистрируются напрямую. Регистратор рекурсивно обходит
          указаный модуль и все его дочерние модули, и регистрирует в реестре
          все классы и фабики из каждого модуля.
          >>> import os
          ... # будут зарегистрированы os и os.path
          ... # но не sys
          ... container.register(os)

        """

        with self._lock:
            for target in targets:
                if self._register(target) is None:
                    raise RegistrationError(
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

    def _register_interface(self, interface: ABC):
        self._add_entry(interface)

    def _register_class(self, cls: Type):
        self._add_entry(cls, cls)
        for ancestor in utils.get_interfaces_for_cls(cls):
            self._add_entry(ancestor, cls)

    def _register_function(self, func: AnyFunc):
        factory_returns = utils.get_factory_result(func)
        if not inspect.isclass(factory_returns):
            return

        self._add_entry(factory_returns, func)

    def _register_module(self, module: ModuleType):
        targets, submodules = utils.get_members(module)
        for target in chain(targets, submodules):
            self._register(target)

    def _add_entry(self, cls: Registerable, factory: Optional[Factory] = None):
        factories = self._registry[cls]
        if factory is not None and factory not in factories:
            factories.append(factory)
