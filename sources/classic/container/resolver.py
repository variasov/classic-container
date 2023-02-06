import inspect
from collections import defaultdict
from typing import Any, Dict, Callable

from .exceptions import ResolutionError
from .constants import SINGLETON, SIMPLE_TYPES
from .settings import Settings, empty_settings
from .types import (
    Factory, Target, Registry,
    SettingsRegistry, InstancesRegistry,
)


class Resolver:
    _instances: InstancesRegistry

    def __init__(self, registry: Registry, settings: SettingsRegistry):
        self._registry = registry
        self._settings = settings
        self._instances = defaultdict(dict)

    def __call__(self, cls: Target, group: str = 'default') -> Any:
        return self._get_instance(cls, group)

    def _get_instance(self, cls: Target, group: str) -> Any:
        if cls in self._instances[group]:
            return self._instances[group][cls]
        settings = self._settings[group].get(cls, empty_settings)
        return self._create_instance(cls, settings.group_ or group)

    def _get_factory_for(self, cls: Target) -> Factory:
        factories = self._registry[cls]
        if factories is None:
            raise ResolutionError(
                f"Class {cls} don't registered in container"
            )

        if not factories:
            raise ResolutionError(
                f'Class {cls} do not have registered implementations'
            )

        if len(factories) > 1:
            raise ResolutionError(
                f'Can not to resolve {cls}, '
                f'implementations are: {factories}',
            )

        return factories[0]

    def _call_factory(self, factory: Factory, group: str) -> Any:
        settings = self._settings[group].get(factory, empty_settings)
        factory = settings.factory_ or factory
        kwargs = self._resolve_kwargs_for_factory(factory, settings, group)

        try:
            return factory(**kwargs)
        except TypeError as exc:
            raise ResolutionError(f'Call of {factory} failed with {exc}')

    def _create_instance(self, cls: Target, group: str) -> Any:
        settings = self._settings[group].get(cls, empty_settings)
        if settings.instance_:
            return settings.instance_

        factory = settings.factory_ or self._get_factory_for(cls)
        instance = self._call_factory(factory, group)

        if instance and settings.scope_ == SINGLETON:
            self._instances[group][cls] = instance

        return instance

    def _resolve_kwargs_for_factory(
        self, factory: Factory,
        settings: Settings, group: str
    ) -> Dict[str, Any]:
        kwargs = {}

        signature = inspect.signature(factory)
        for parameter in signature.parameters.values():
            if parameter.name in settings.init_:
                kwargs[parameter.name] = settings.init_[parameter.name]
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

            instance = self._get_instance(parameter.annotation, group)
            if instance is not None:
                kwargs[parameter.name] = instance

            elif parameter.default is not inspect.Parameter.empty:
                raise ResolutionError(
                    f"Can't resole attribute {parameter.name} "
                    f"for {factory}, attribute don't have default value "
                    f"and {factory} has returned None"
                )

        return kwargs
