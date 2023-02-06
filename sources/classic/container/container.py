from collections import defaultdict

from .registrator import Registrator
from .resolver import Resolver
from .types import Registry, SettingsGroup, SettingsRegistry


class Container:
    settings: SettingsRegistry
    registry: Registry

    def __init__(self):
        self.registry = defaultdict(list)
        self.settings = defaultdict(dict)

        self.register = Registrator(self.registry)
        self.resolve = Resolver(self.registry, self.settings)

    def add_settings(self, settings: SettingsGroup, group: str = 'default'):
        self.settings[group].update(settings)
        self.register(*settings.keys())
