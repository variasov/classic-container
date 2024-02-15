import threading
from typing import TypeVar, Optional

from .registry import Registry
from .builder import Builder
from .settings import Settings


Object = TypeVar('Object', bound=object)


class Container:
    """
    Классический IoC-контейнер.

    """

    _registry: Registry
    _settings: dict[type[Object], Object]
    _cache: dict[type[Object], Object]
    _lock: threading.RLock
    _current_builder: Optional[Builder]

    def __init__(self):
        self._lock = threading.RLock()
        self._registry = Registry()
        self._settings = {}
        self._cache = {}
        self._current_builder = None

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
          аннотации функции, а значением сама фабрика.
          Пример:
          >>> def some_factory() -> SomeClass:  # NOQA
          ...     # будет зарегистрировано как SomeClass: [some_factory]
          ...     pass

        - Модули не регистрируются напрямую. Регистратор рекурсивно обходит
          указанный модуль и все его дочерние модули, и регистрирует в реестре
          все классы и фабрики из каждого модуля.
          >>> import os
          ... # будут зарегистрированы os и os.path
          ... # но не sys
          ... container.register(os)  # NOQA

        """
        with self._lock:
            self._registry.register(*args)

    def resolve(
        self, target: type[Object],
        settings: dict[type[object], Settings] = None,
    ) -> Object:
        """
        Собирает объект с его деревом зависимостей для указанной реализации.

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
        Во всех этих случаях контейнер выкидывает ValueError с описанием ошибки.
        """

        with self._lock:

            # Ссылку на предыдущий сборщик нужно запомнить,
            # чтобы после завершения resolve можно было
            # восстановить ссылку в _current_resolve
            previous = self._current_builder

            self._current_builder = Builder(
                registry=self._registry,
                settings=self._settings if not previous else settings or {},
                cache=self._cache if not previous else {},
                previous=previous,
            )
            result = self._current_builder.build(target)

            self._current_builder = previous

        return result

    def add_settings(self, settings: dict[type[object], Settings]) -> None:
        """
        Добавляет или обновляет настройки контейнера.

        Принимает словарь, в котором ключи - классы,
        значения - объекты Settings.
        """
        with self._lock:
            self._settings.update(settings)

            # Логично предположить, что если для классов указано что-либо
            # в настройках, то можно это автоматически регистрировать
            self.register(*settings.keys())

    def reset(self):
        """
        Удаляет добавленные настройки контейнера и ссылки на инстансы ранее
        созданных классов. Не должен вызываться во время resolve.
        """

        # В случае, если reset запрошен во время resolve,
        # дешевле выбросить исключение, чем разгребать
        # очень странные ошибки
        assert self._current_builder is None

        with self._lock:
            self._settings.clear()
            self._cache.clear()
