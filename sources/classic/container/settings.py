from .constants import SINGLETON, SCOPES
from .types import Factory


class Settings:
    """
    Класс хранит настройки resolv-а.

    Используется для хранения способа создания объекта или самого объекта
    при разрешении зависимостей.
    """
    def __init__(
        self, init: dict[str, object] = None, factory: Factory = None,
        scope: str = None, instance: object = None,
    ):
        assert scope is None or scope in SCOPES, \
            f'Scope name must be SINGLETON or TRANSIENT. Current is "{scope}"'

        assert instance is None or (
            instance is not None and
            not factory and
            not init and
            (scope is None or scope == 'SINGLETONE')
        ), (f'Container can use only instance or '
            f'factory, init and scope must be SINGLETON')

        self.scope_ = scope or SINGLETON
        self.init_ = init or {}
        self.factory_ = factory
        self.instance_ = instance

    def __repr__(self):
        rows = []
        if self.scope_:
            rows.append(f'scope={self.scope_}')
        if self.init_:
            rows.append(f'init={self.init_}')
        if self.factory_:
            rows.append(f'factory={self.factory_}')
        if self.instance_:
            rows.append(f'instance={self.instance_}')
        args = ', '.join(rows)
        return f'<container.Settings({args})>'

    def init(self, **kwargs: object) -> 'Settings':
        """
        Позволяет установить значения аргументов для фабрики
        при построении объекта. Самое частое использование - передача
        простых объектов (чисел, строк).

        >>> from classic.container import Container, Settings, init
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
        ... container = Container()
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
        ... container.add_settings({SomeClass: init(some_value=2)})
        """

        assert self.instance_ is None, (
            f'Container can use only instance or init'
        )
        self.init_ = kwargs
        return self

    def factory(self, factory: Factory) -> 'Settings':
        """
        Позволяет явно передать способ создания компонента системы.
        Значением может являться любой вызываемый объект возвращающий
        инстанс любого объекта, и имеющий аннотацию типов.

        >>> from abc import ABC, abstractmethod
        ... from classic.container import Container, Settings, factory
        ...
        ... class Interface(ABC):
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
        ... container = Container()
        ...
        ... container.register(Implementation, SomeClass, composition_factory)
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
        ... container.add_settings({SomeClass: factory(composition_factory)})
        """

        assert self.instance_ is None, (
            f'Container can use only instance or factory'
        )
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

        >>> from abc import ABC, abstractmethod
        ... from classic.container import Container, Settings, TRANSIENT, scope
        ...
        ... class Interface(ABC):
        ...
        ...     @abstractmethod
        ...     def method(self): ...
        ...
        ... class Implementation(Interface):
        ...
        ...     def method(self):
        ...         return 1
        ...
        ... container = Container()
        ...
        ... container.register(Interface, Implementation)
        ...
        ... # Длинный способ через конструктор
        ... container.add_settings({Implementation: Settings(scope=TRANSIENT)})
        ...
        ... # Вызов "цепочкой"
        ... container.add_settings({
        ...     Implementation: Settings().scope(name=TRANSIENT)
        ... })
        ...
        ... # А можно через алиас
        ... container.add_settings({Implementation: scope(TRANSIENT)})
        """
        assert name in SCOPES, (
            f'Scope name must be SINGLETON or TRANSIENT. Current is "{name}"'
        )
        assert self.instance_ is None or name == 'SINGLETON', (
            f'Scope name must be SINGLETON then used instance'
        )
        self.scope_ = name
        return self

    def instance(self, instance: object) -> 'Settings':
        """
        Настройка позволяет подать готовый инстанс класса.

        Подразумевается основное использование при потребности подачи
        в разные классы готовых объектов, но настроенных по-разному.

        Класс сделан для удобства, тоже самое можно сделать через фабрики.

        >>> from abc import ABC, abstractmethod
        ... from classic.container import Container, Settings, instance
        ...
        ... class Interface(ABC):
        ...     some_value: int
        ...
        ...     @abstractmethod
        ...     def method(self): ...
        ...
        ... class Implementation(Interface):
        ...
        ...     def __init__(self, some_value):
        ...         self.some_value = some_value
        ...
        ...     def method(self):
        ...         return 1
        ...
        ... class SomeClass:
        ...
        ...     def __init__(self, impl: Interface):
        ...         self.impl = impl
        ...
        ... container = Container()
        ...
        ... container.register(
        ...     Interface, Implementation, SomeClass,
        ... )
        ...
        ... impl = Implementation(1)
        ...
        ... # Длинный способ через конструктор
        ... container.add_settings({
        ...     SomeClass: Settings(instance=impl)
        ... })
        ...
        ... # Вызов "цепочкой"
        ... container.add_settings({
        ...     SomeClass: Settings().instance(instance=impl)
        ... })
        ...
        ... # А можно через алиас
        ... container.add_settings({SomeClass: instance(impl)})
        """
        assert (
            not self.init_ and
            not self.factory_ and
            self.scope_ == 'SINGLETON'
        ), (f'Container can use only instance or '
            f'factory, init and scope must be SINGLETON')
        self.instance_ = instance
        return self


settings = Settings
EMPTY_SETTINGS = Settings()


def init(**kwargs: object) -> Settings:
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


def instance(obj: object) -> Settings:
    """
    Обертка для создания настроек с готовым объектом при разрешении
    зависимостей.
    """
    return Settings(instance=obj)
