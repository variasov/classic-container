import threading
from collections import defaultdict

from .registrator import Registrator
from .resolver import Resolver
from .settings import Settings
from .types import Registry, RegisterCallable


class Container:
    """
    Классический IoC-контейнер.

    Предоставляет два метода - register и resolve.
    register нужен для регистрации классов, интерфейсов, функций и даже модулей.
    resolve принимает какой-либо класс (интерфейс), и возвращает инстанс
    указанного интерфейс с разрешенными зависимостями.
    """

    _registry: Registry
    register: RegisterCallable
    resolve: Resolver

    def __init__(self):
        self._registry = defaultdict(list)
        self._settings = dict()
        self._lock = threading.RLock()

        self.register = Registrator(self._registry, self._lock)
        self.resolve = Resolver(self._registry, self._settings, self._lock)

    def add_settings(self, settings: dict[type, Settings]):
        """
        Добавляет или обновляет настройки контейнера.

        Ключем является класс, значение - настройки.
        """
        self._settings.update(settings)
        self.register(*settings.keys())

    def reset(self):
        with self._lock:
            self._settings = dict()
            self.resolve.reset()
