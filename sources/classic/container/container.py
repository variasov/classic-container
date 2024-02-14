import threading
from typing import TypeVar, Optional

from .registry import Registry
from .resolver import Resolver
from .settings import Settings


Object = TypeVar('Object', bound=object)


class Container:
    """
    Классический IoC-контейнер.

    Предоставляет четыре метода - register, resolve, add_settings и reset.
    register нужен для регистрации классов, интерфейсов, функций и даже модулей.
    resolve принимает какой-либо класс (интерфейс), и возвращает инстанс
    указанного интерфейс с разрешенными зависимостями.
    """

    _registry: Registry
    _settings: dict[type[Object], Object]
    _cache: dict[type[Object], Object]
    _lock: threading.RLock
    _current_resolve: Optional[Resolver]

    def __init__(self):
        self._lock = threading.RLock()
        self._registry = Registry()
        self._settings = {}
        self._cache = {}
        self._current_resolve = None

    def register(self, *args: object) -> None:
        """
        При обращении принимает список компонентов.
        Определяет тип, заносит в реестр, каждому типу сопоставляет
        список фабрик, способных построить указанный тип.

        Элементами списка могут быть: абстрактные классы, классы,
        фабрики (функции, возвращающие один инстанс любого класса) и модули.

        - Абстрактные классы регистрируется в реестре только как ключи,
          без фабрик.
        - Нормальные классы регистрируются как ключ и соответсвующая ему
          фабрика - конструктор самого класса.
        - Фабрики регистрируются сложнее, ключом будет являться результат из
          аннотации функции, а значением сама фабрика. Пример:
          >>> def some_factory() -> SomeClass:
          ...     # будет зарегистрировано как SomeClass: [some_factory]
          ...     pass

        - Модули не регистрируются напрямую. Регистратор рекурсивно обходит
          указанный модуль и все его дочерние модули, и регистрирует в реестре
          все классы и фабрики из каждого модуля.
          >>> import os
          ... # будут зарегистрированы os и os.path
          ... # но не sys
          ... container.register(os)

        """
        with self._lock:
            self._registry.register(*args)

    def resolve(
        self, target: type[Object],
        settings: dict[type[object], Settings] = None,
    ) -> Object:
        """
        Разрешает зависимости для указанной реализации,
        создает и возвращает инстанс класса.

        Рекурсивно обходит дерево зависимостей, начиная с указанного класса.
        На каждый шаг рекурсии для указанного класса ищется фабрика в реестре.
        Далее для найденной фабрики собираются аргументы,
        чтобы вызвать фабрику и построить объект.
        При этом:
         - пропускаются аргументы простых типов, аргументы без аннотаций
           и функции;
         - подставляются значения из init для аргументов,
           указанных в этом же init;
         - для аргументов, проаннотированных классами, повторяется рекурсия.

        В процессе разрешения могут возникать ситуации, когда:
         - для интерфейса (абстрактного класса) не нашлось реализации;
         - для класса нашлось больше 1 фабрики
           и ни одна не указана в настройках для этого класса;
         - фабрика для аргумента вернула None
           и для аргумента не указан значение по умолчанию;
         - при вызове фабрики не был указан обязательный аргумент.
        Во всех этих случаях контейнер выкидывает ResolutionError.

        Все ошибки состоят из двух частей. Первая часть уникальна для ошибки
        и объясняет причину, во второй части описано,
        что и в каком порядке пытался построить контейнер.
        Она состоит из строк, по три элемента в каждой:
         - Target: полное имя класса (some.module.SomeClass);
         - Factory: полное имя фабрики (another.module.SomeFactory);
         - Arg: имя аргумента фабрики.

        Пример:
        >>> from abc import ABC, abstractmethod
        ... from classic.container import container
        ...
        ... class Interface(ABC):
        ...
        ...     @abstractmethod
        ...     def method(self): ...
        ...
        ... class Implementation(Interface):
        ...
        ...     def __init__(self):
        ...         raise NotImplemented
        ...
        ...     def method(self):
        ...         return 1
        ...
        ... class Composition:
        ...
        ...     def __init__(self, impl: Interface):
        ...         self.impl = impl
        ...
        ... class SomeClass:
        ...
        ...     def __init__(self, obj: Composition):
        ...         self.obj = obj
        ...
        ...
        ... container.register(Interface, Implementation, SomeClass, Composition)
        ... container.resolve(SomeClass)
        ...
        classic.container.exceptions.ResolutionError: Class \
        <class 'example.Interface'> do not have registered implementations.
        Resolve chain:
        Target: app.SomeClass, Factory: app.SomeClass, Arg: obj
        Target: app.Composition, Factory: app.Composition, Arg: impl
        Target: app.Interface, Factory: app.Implementation, Arg: -

        """

        with self._lock:
            # Ссылка на предыдущий резолвер нужно запомнить,
            # чтобы после завершения resolve можно было
            # восстановить ссылку в _current_resolve
            previous = self._current_resolve

            self._current_resolve = Resolver(
                registry=self._registry,
                settings=self._settings if not previous else settings or {},
                cache=self._cache if not previous else {},
                previous=previous,
            )
            result = self._current_resolve.resolve(target)

            self._current_resolve = previous

        return result

    def add_settings(self, settings: dict[type[object], Settings]) -> None:
        """
        Добавляет или обновляет настройки контейнера.

        Ключом является класс, значение - настройки.
        """
        with self._lock:
            self._settings.update(settings)
            self.register(*settings.keys())

    def reset(self):
        """
        Удаляет добавленные настройки контейнера и ссылки на инстансы уже
        созданных классов
        """
        assert self._current_resolve is None

        with self._lock:
            self._settings.clear()
            self._cache.clear()
