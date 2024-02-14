import inspect
from typing import Callable, Optional

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

    def build(self, target: type[Target]) -> Target:
        # Если объект уже есть в кеше, то можно просто его отдать
        if cached := self.get_cached(target):
            return cached

        # Ищем настройки для указанного класса
        target_settings, target_settings_layer = self.get_settings(target)

        # Инстанс, заданный в настройках возвращается как есть
        if target_settings.instance_:
            return target_settings.instance_

        # Выбираем фабрику для указанного класса
        factory = target_settings.factory_ or self._registry.get(target)
        factory_settings = self.get_settings(factory)[0]

        # Фабрика выбрана, далее нужно собрать аргументы.
        # Нужно получаем сигнатуру для фабрики,
        # чтобы по ней построить аргументы для вызова фабрики
        factory_kwargs = {}
        signature = self._registry.signature(factory)
        for parameter in signature.parameters.values():

            # Если для параметра в init было указанно значение,
            # то берем значение "как есть".
            if parameter.name in factory_settings.init_:
                factory_kwargs[parameter.name] = (
                    factory_settings.init_[parameter.name]
                )
                continue

            # Параметры без аннотации пропускаются
            if parameter.annotation is inspect.Parameter.empty:
                continue

            # Для аргументов простых типов контейнер не ищет фабрики
            if parameter.annotation in SIMPLE_TYPES:
                continue

            # Инстанцирование аргумента
            if inspect.isclass(parameter.annotation):
                instance = self.build(parameter.annotation)
                if instance is not None:
                    factory_kwargs[parameter.name] = instance

                # Странный случай, когда фабрика вернула None
                elif parameter.default is inspect.Parameter.empty:
                    raise ValueError(
                        f"Can't resole attribute {parameter.name} "
                        f"for {factory}, attribute don't have default value "
                        f"and {factory} has returned None. "
                        f"Maybe you have forgot to add 'return' "
                        f"to the end of your factory?"
                    )

        # Постройка инстанса указанного класса
        instance = factory(**factory_kwargs)

        # TRANSIENT объекты не кешируются,
        # чтобы контейнер при каждом запросе строил их заново
        if instance and target_settings.scope_ == SINGLETON:
            target_settings_layer.cache_instance(target, instance)

        return instance
