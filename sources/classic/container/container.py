import threading
from collections import defaultdict

from .registrator import Registrator
from .resolver import Resolver
from .types import Registry


class Container:
    registry: Registry

    def __init__(self):
        """

        """
        self._registry = defaultdict(list)
        self._settings = dict()
        self._lock = threading.Lock() # базовая потокобезопасность

        self.register = Registrator(self._registry, self._lock)
        self.resolve = Resolver(self._registry, self._settings, self._lock)

    def add_settings(self, settings):
        """

        :param settings:
        :return:
        """
        self._settings.update(settings)
        self.register(*settings.keys())
