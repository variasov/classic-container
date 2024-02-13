import inspect
from typing import Callable, Optional

from .exceptions import ResolutionError
from .constants import SINGLETON, SIMPLE_TYPES
from .settings import Settings, EMPTY_SETTINGS
from .registry import Registry
from .types import Target


class Resolver:
    _registry: Registry
    _settings: dict[type[Target], Settings]
    _cache: dict[type[Target], Target]
    _previous: 'Resolver'

    def __init__(
        self,
        registry: Registry,
        settings: dict[type[Target], Settings],
        cache: dict[type[Target], Target],
        previous: 'Resolver' = None,
    ):
        self._registry = registry
        self._settings = settings
        self._cache = cache
        self._previous = previous

    def get_settings(self, cls: Target) -> tuple[Settings, 'Resolver']:
        if cls_settings := self._settings.get(cls):
            return cls_settings, self

        if self._previous:
            return self._previous.get_settings(cls)
        else:
            return EMPTY_SETTINGS, self

    def get_cached(self, cls: Target) -> Optional[Target]:
        if cached := self._cache.get(cls):
            return cached

        if self._previous:
            return self._previous.get_cached(cls)
        else:
            return None

    def cache_instance(self, cls: type[Target], instance: Target) -> None:
        self._cache[cls] = instance

    def resolve(self, cls: type[Target]) -> Target:
        factory = None
        factory_settings = None
        factory_kwargs = {}
        cls_settings = None
        cls_settings_layer = None

        try:
            if cached := self.get_cached(cls):
                return cached

            cls_settings, cls_settings_layer = self.get_settings(cls)
            if cls_settings.instance_:
                return cls_settings.instance_

            factory = cls_settings.factory_ or self._registry.get(cls)
            factory_settings, __ = self.get_settings(factory)

            signature = self._registry.signature(factory)
            for parameter in signature.parameters.values():
                if parameter.name in factory_settings.init_:
                    factory_kwargs[parameter.name] = (
                        factory_settings.init_[parameter.name]
                    )
                    continue

                if parameter.annotation is inspect.Parameter.empty:
                    continue

                if parameter.annotation in SIMPLE_TYPES:
                    continue

                if (
                    isinstance(parameter.annotation, Callable)
                    and not inspect.isclass(parameter.annotation)
                ):
                    continue

                instance = self.resolve(parameter.annotation)
                if instance is not None:
                    factory_kwargs[parameter.name] = instance

                elif parameter.default is inspect.Parameter.empty:
                    raise ValueError(
                        f"Can't resole attribute {parameter.name} "
                        f"for {factory}, attribute don't have default value "
                        f"and {factory} has returned None \n"
                    )

            try:
                instance = factory(**factory_kwargs)
            except TypeError as exc:
                raise ValueError(f'Call of {factory} failed with {exc}\n')

            if instance and cls_settings.scope_ == SINGLETON:
                cls_settings_layer.cache_instance(cls, instance)

            return instance
        except ResolutionError as exception:
            exception.add(
                cls=cls,
                exception=exception,
                cls_settings=cls_settings,
                cls_settings_layer=cls_settings_layer,
                factory=factory,
                factory_settings=factory_settings,
                factory_kwargs=factory_kwargs,
            )
            raise exception
        except Exception as exception:
            raise ResolutionError from exception
