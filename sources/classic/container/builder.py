import inspect
from typing import Callable, Optional

from .exceptions import ResolutionError
from .constants import SINGLETON, SIMPLE_TYPES
from .settings import Settings, EMPTY_SETTINGS
from .registry import Registry
from .types import Target


class Builder:
    _registry: Registry
    _settings: dict[type[Target], Settings]
    _cache: dict[type[Target], Target]
    _previous: 'Builder'

    def __init__(
        self,
        registry: Registry,
        settings: dict[type[Target], Settings],
        cache: dict[type[Target], Target],
        previous: 'Builder' = None,
    ):
        self._registry = registry
        self._settings = settings
        self._cache = cache
        self._previous = previous

    def get_settings(self, cls: Target) -> tuple[Settings, 'Builder']:
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

    def build(self, cls: type[Target]) -> Target:

        # Это "предварительные" версии значений,
        # нужные для того, чтобы в случае ошибки можно было собрать
        # весь контекст в ошибку, вне зависимости от того, были ли
        # объявлены переменные, или нет
        factory = None
        factory_settings = None
        factory_kwargs = {}
        cls_settings = None
        cls_settings_layer = None
        parameter = None

        try:
            # Если объект уже есть в кеше, то можно просто его отдать
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

                instance = self.build(parameter.annotation)
                if instance is not None:
                    factory_kwargs[parameter.name] = instance

                elif parameter.default is inspect.Parameter.empty:
                    raise ValueError(
                        f"Can't resole attribute {parameter.name} "
                        f"for {factory}, attribute don't have default value "
                        f"and {factory} has returned None \n"
                    )

            instance = factory(**factory_kwargs)

            if instance and cls_settings.scope_ == SINGLETON:
                cls_settings_layer.cache_instance(cls, instance)

            return instance
        except Exception as exception:
            if isinstance(exception, ResolutionError):
                accumulator = exception
            else:
                accumulator = ResolutionError()

            accumulator.add(
                cls=cls,
                cls_settings=cls_settings,
                factory=factory,
                factory_settings=factory_settings,
                factory_kwargs=factory_kwargs,
                parameter=parameter
            )

            raise accumulator
