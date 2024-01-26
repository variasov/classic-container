from typing import Any, Dict

from .constants import SINGLETON, SCOPES
from .types import Factory


class Settings:
    """
    Класс хранит настройки resolv-а.

    Используется для хранения способа создания объекта или самого объекта
    при разрешении зависимостей.
    """
    def __init__(
        self, init: Dict[str, Any] = None, factory: Factory = None,
        scope: str = None, instance: Any = None,
    ):
        assert scope is None or scope in SCOPES, \
            f'Scope name must be SINGLETON or TRANSIENT. Current is "{scope}"'

        self.scope_ = scope or SINGLETON
        self.init_ = init or {}
        self.factory_ = factory
        self.instance_ = instance

        assert self.instance_ is None or (
            not self.factory_ and
            not instance is None and
            not self.init_
        ), f'test'
        # assert instance is None or (
        #     len(self.init_) == 0 and self.factory_ is None
        # ), f'Container can use only instance or factory, init'
        assert instance is None or self.scope_ == SINGLETON, \
            f'When used instance scope can be only SINGLETON'

    def init(self, **kwargs: Any) -> 'Settings':
        """
        Позволяет установить значения аргументов для фабрики
        при построении объекта. Самое частое использование - передача
        простых объектов (чисел, строк).

        >>> from classic.container import container, Settings, init
        ...
        ... class SomeClass:
        ...     def __init__(self, some_value: int):
        ...         # Для int будет неудобно указывать фабрику,
        ...         # так как много у каких классов может быть параметр типа int
        ...         # (справедливо для любого простого типа), поэтому
        ...         # библиотека оставляет возможность
        ...         # указать параметр через init
        ...         self.some_value = some_value
        ...
        ... container.register(SomeClass)
        ...
        ... # Длинный способ через конструктор
        ... container.add_settings({
        ...     SomeClass: Settings(init=dict(some_value=2))
        ... })
        ...
        ... # Вызов "цепочкой"
        ... container.add_settings({
        ...     SomeClass: Settings().init(some_value=2)
        ... })
        ...
        ... # А можно через алиас
        ... container.add_settings({
        ...     SomeClass: init(some_value=2)
        ... })
        """
        self.init_ = kwargs
        return self

    def factory(self, factory: Factory) -> 'Settings':
        """
        Позволяет явно передать способ создания компонента системы.
        Значением может являться любой вызываемый объект возвращающий
        инстанс любого объекта, и имеющий аннотацию типов.

        >>> from abc import ABC, abstractmethod
        ... from classic.container import container, Settings, factory
        ...
        ... class Interface(ABC)
        ...
        ...     @abstractmethod
        ...     def method(self): ...
        ...
        ... class Implementation(Interface):
        ...
        ...     def method(self):
        ...         return 1
        ...
        ... class SomeClass:
        ...
        ...     def __init__(self, impl: Interface):
        ...         self.impl = impl
        ...
        ... def composition_factory(obj: Interface) -> SomeClass:
        ...     return SomeClass(obj)
        ...
        ... container.register(
        ...     Interface, Implementation, SomeClass, composition_factory
        ... )
        ...
        ... # Длинный способ через конструктор
        ... container.add_settings({
        ...     SomeClass: Settings(factory=composition_factory)
        ... })
        ...
        ... # Вызов "цепочкой"
        ... container.add_settings({
        ...     SomeClass: Settings().factory(factory=composition_factory)
        ... })
        ...
        ... # А можно через алиас
        ... container.add_settings({
        ...     SomeClass: factory(composition_factory)
        ... })
        """

        self.factory_ = factory
        return self

    def scope(self, name: str) -> 'Settings':
        """
        Данная настройка регулирует жизненны цикл объекта, который может быть
        SINGLETON и TRANSIENT.

        При значении SINGLETON контейнер создаст объект только один раз,
        все последующие запросы будут использовать тот же самый объект.
        Является значением по умолчанию.

        При TRANSIENT контейнер будет создавать новый объект при каждом resolve.

        Для каждого класса настройка scope добавляется отдельно!
        """
        assert name in SCOPES, (
            f'Scope name must be SINGLETON or TRANSIENT. Current is "{name}"'
        )
        self.scope_ = name
        return self


settings = Settings
empty_settings = Settings()


def init(**kwargs: Any) -> Settings:
    """
    Обертка для создания настроек компонентов с параметрами.
    Самое частое использование - передача простых объектов (чисел, строк).
    """
    return Settings(init=kwargs)


def factory(factory: Factory) -> Settings:
    """
    Обертка для создания настроек компонентов со способом получения объекта.
    Принимает способ создания объекта (фабрика, класс, абстрактный класс).
    """
    return Settings(factory=factory)


def scope(name: str) -> Settings:
    """
    Обертка для указания настройки scope у элемента приложения.
    Возможные значения указанны в константах текущего пакета:
    SINGLETON, TRANSIENT
    """
    return Settings(scope=name)


def instance(obj: Any) -> Settings:
    """
    Обертка для создания настроек с готовым объектом при разрешении
    зависимостей компонентов системы.
    """
    return Settings(instance=obj)
