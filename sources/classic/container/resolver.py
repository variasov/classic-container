import inspect
import threading
from typing import Any, Dict, Callable

from .exceptions import ResolutionError
from .constants import SINGLETON, SIMPLE_TYPES
from .settings import Settings, empty_settings
from .types import Factory, Target, Registry, InstancesRegistry


class Resolver:
    """
    Класс производит разрешение зависимостей компонентов приложеия.

    Объект этого класса нужен для разрешения зависимостей в контейнере
    компонентов приложения. Предполагается что этот объект инстанцируется
    контейнером и используется только "под капотом".
    Выглядит как метод resolve у контейнера.
    """

    _instances: InstancesRegistry

    def __init__(self, registry: Registry, settings, lock: threading.RLock):
        self._registry = registry
        self._settings = settings
        self._instances = dict()
        self._lock = lock

    def __call__(self, cls: Target) -> Any:
        """
        При обращении разрешает зависимости, используя указанную реализацию,
        создает и возвращает инстанс класса.

        Принимать в себя абстрактный класс или класс.
        При создании объектов

        """
        with self._lock:
            return self._get_instance(cls)

    def reset(self):
        self._settings = dict()
        self._instances = dict()

    def _get_instance(self, cls: Target) -> Any:
        if cls in self._instances:
            return self._instances[cls]
        return self._create_instance(cls)

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

    def _call_factory(self, factory: Factory) -> Any:
        settings = self._settings.get(factory, empty_settings)
        kwargs = self._resolve_kwargs_for_factory(factory, settings)

        try:
            return factory(**kwargs)
        except TypeError as exc:
            raise ResolutionError(f'Call of {factory} failed with {exc}')

    def _create_instance(self, cls: Target) -> Any:
        settings = self._settings.get(cls, empty_settings)
        if settings.instance_:
            return settings.instance_

        factory = settings.factory_ or self._get_factory_for(cls)
        instance = self._call_factory(factory)

        if instance and settings.scope_ == SINGLETON:
            self._instances[cls] = instance

        return instance

    def _resolve_kwargs_for_factory(
        self, factory: Factory, settings: Settings,
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

            instance = self._get_instance(parameter.annotation)
            if instance is not None:
                kwargs[parameter.name] = instance

            elif parameter.default is not inspect.Parameter.empty:
                raise ResolutionError(
                    f"Can't resole attribute {parameter.name} "
                    f"for {factory}, attribute don't have default value "
                    f"and {factory} has returned None"
                )

        return kwargs
