from abc import ABC
from collections import defaultdict
from functools import lru_cache
from itertools import chain
import inspect
from types import ModuleType
from typing import (
    Optional, Callable, get_type_hints, Tuple, Sequence, Generator, get_origin,
)

from .types import Factory, Registerable, ModuleOrTarget, Target


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
    def signature(self, cls: Target) -> dict[str, inspect.Parameter]:
        """
        Возвращает описание сигнатуры указанной фабрики.
        Отличается от обычного inspect.signature тем,
        что пытается разрешить ForwardReference.

        Например:
        >>> class Test:
        ...     field: 'Test'
        """
        hints = get_type_hints(cls)
        signature = inspect.signature(cls)

        result = {}
        for name, parameter in signature.parameters.items():
            if isinstance(parameter.annotation, str):
                hint = hints[name]
            else:
                hint = parameter.annotation

            result[name] = parameter.replace(annotation=hint)

        return result

    def get(self, target: Target) -> Factory[Target]:
        """
        Вернет фабрику для указанного класса.

        Выбросит исключение, если фабрики не нашлось, или ее больше одной.
        """
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
        """
        Запускает регистрацию указанного объекта.
        Выбрасывает ValueError, если указанный объект
        не является классом, функцией или модулем.
        """
        for target in targets:
            if self._register(target) is None:
                raise ValueError(
                    f'Registration target must be class, '
                    f'function or module, {target} is {type(target)}'
                )

    def _register(self, target: ModuleOrTarget) -> Optional[str]:
        """
        Идентификация объекта и регистрация в реестре.
        """
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

        elif _is_generic(target):
            self._register_interface(target)
            result = 'generic'

        return result

    def _register_interface(self, interface: ABC) -> None:
        """
        Регистрация интерфейса/абстрактного класса.
        ABC считаются классами без фабрики.
        """
        self._add_entry(interface)

    def _register_class(self, cls: type[object]) -> None:
        """
        Регистрация обычного класса.
        Обычный класс считается фабрикой для самого себя,
        и для каждого предка в MRO.
        """
        self._add_entry(cls, cls)
        for ancestor in _get_interfaces_for_cls(cls):
            self._add_entry(ancestor, cls)

    def _register_function(self, func: Callable) -> None:
        """
        Регистрация функции.
        Если в аннотации функции указано, что она возвращает инстанс
        какого-либо класса, то она считается фабрикой для этого класса.

        Остальные игнорируются.
        """
        factory_returns = _get_factory_result(func)
        if not inspect.isclass(factory_returns):
            return

        self._add_entry(factory_returns, func)

    def _register_module(self, module: ModuleType) -> None:
        """
        Регистрация модуля.

        Регистрируется содержимое модуля, вместе с дочерними модулями,
        рекурсивно, но не содержимое сторонних модулей.

        Ради примера представим себе содержимое __init__ у модуля example:
        >>> import functools
        ... from itertools import chain
        ... from . import child  # NOQA

        При регистрации:
        >>> from classic.container import container
        ... container.register(child)

        В реестр попадут example, example.child и chain, но не functools.
        """
        targets, submodules = _get_members(module)
        for target in chain(targets, submodules):
            self._register(target)

    def _add_entry(
        self, cls: Registerable,
        factory: Optional[Factory[Target]] = None,
    ) -> None:
        """
        Добавление записи в реестр.
        """
        factories = self._storage[cls]
        if factory is not None and factory not in factories:
            factories.append(factory)


def _is_submodule(submodule: ModuleType, module: ModuleType) -> bool:
    return submodule.__name__.startswith(module.__name__)


def _is_generic(target: type[object]) -> bool:
    return get_origin(target) is not None


def _get_members(module: ModuleType) -> Tuple[Sequence[Registerable],
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


def _get_interfaces_for_cls(
    target: type[Target],
) -> Generator[type[object], None, None]:

    for cls in target.__mro__:
        if cls != object:
            yield cls


def _get_factory_result(factory: Factory[Target]) -> type[Target] | None:
    if inspect.isclass(factory):
        return factory

    signature = inspect.signature(factory)
    result = signature.return_annotation
    if result == inspect.Parameter.empty:
        return None

    return result
