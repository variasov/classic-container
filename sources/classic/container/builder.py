import inspect

from .constants import SINGLETON, SIMPLE_TYPES
from .settings import Settings, EMPTY_SETTINGS
from .registry import Registry, _is_generic
from .types import Target


class Builder:
    _registry: Registry
    _settings: dict[type[Target], Settings]
    _cache: dict[type[Target], Target]
    _previous: 'Builder'
    _classes: set[type[Target]]

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
        self._classes = set()

    def get_settings(self, target: Target) -> tuple[Settings, 'Builder']:
        """
        Ищет настройку в кеше, если не находит, рекурсивно обращается к предкам,
        ища настройку у них. Если не находит, возвращает пустые настройки.

        Возвращает настройку вместе с объектом-сборщиком,
        чтобы потом можно было поместить созданный инстанс в кеш того же слоя,
        с которого использовались настройки.
        """
        if cls_settings := self._settings.get(target):
            return cls_settings, self

        if self._previous:
            return self._previous.get_settings(target)
        else:
            return EMPTY_SETTINGS, self

    def get_cached(self, target: Target) -> Target | None:
        """
        Ищет инстанс для указанного класса в кеше.
        Если не находит, рекурсивно обращается к предкам,
        ища настройку у них.
        Возвращает None, если инстанс для класса не найден.
        """
        if cached := self._cache.get(target):
            return cached

        if self._previous:
            return self._previous.get_cached(target)
        else:
            return None

    def cache_instance(self, target: type[Target], instance: Target) -> None:
        """
        Помещает инстанс в кеш.
        """
        self._cache[target] = instance

    def detect_cycle(self, target: Target) -> None:
        """
        Проверка на цикл в графе зависимостей.

        Должно проверяться при каждом вызове build,
        для всех сборщиков одновременно. Для этого контейнер создает множество,
        которое затем передает каждому сборщику. Это проверка помещает
        указанный класс в множество.
        Если указанный класс встретится во множестве, значит, в графе есть цикл.
        """
        if target in self._classes:
            raise ValueError(f'Cycle reference detected on class {target}')

        self._classes.add(target)

    def build(self, target: type[Target]) -> Target:
        """
        Собирает объект указанного класса.

        Рекурсивно вызывается для каждого аргумент фабрики,
        найденной для указанного класса.
        """

        # Если объект уже есть в кеше, то можно просто его отдать
        if cached := self.get_cached(target):
            return cached

        # Ищем настройки для указанного класса
        target_settings, target_settings_layer = self.get_settings(target)

        # Инстанс, заданный в настройках возвращается как есть
        if target_settings.instance_:
            return target_settings.instance_

        self.detect_cycle(target)

        # Выбираем фабрику для указанного класса
        factory = target_settings.factory_ or self._registry.get(target)
        factory_settings = self.get_settings(factory)[0]

        # Фабрика выбрана, далее нужно собрать аргументы.
        # Нужно получаем сигнатуру для фабрики,
        # чтобы по ней построить аргументы для вызова фабрики
        factory_kwargs = {}
        for name, param in self._registry.signature(factory).items():

            # Если для параметра в init было указанно значение,
            # то берем значение "как есть".
            if name in factory_settings.init_:
                factory_kwargs[name] = factory_settings.init_[name]
                continue

            # Для аргументов простых типов контейнер не ищет фабрики
            if param.annotation in SIMPLE_TYPES:
                continue

            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue

            # Инстанцирование аргумента
            if (
                inspect.isclass(param.annotation)
                or _is_generic(param.annotation)
            ):
                try:
                    instance = self.build(param.annotation)
                except ValueError:
                    if param.default is None:
                        continue
                    else:
                        raise

                if instance is not None:
                    factory_kwargs[name] = instance

                # Случай, когда нечего указать в обязательный аргумент
                elif param.default is inspect.Parameter.empty:
                    raise ValueError(
                        f"Can't resole attribute {name} "
                        f"for {factory}, attribute don't have default value "
                        f"and {factory} has returned None. "
                        f"Maybe you have forgot to add 'return' "
                        f"to the end of your factory?"
                    )

                factory_kwargs[name] = instance

        # Постройка инстанса указанного класса
        instance = factory(**factory_kwargs)

        # TRANSIENT объекты не кешируются,
        # чтобы контейнер при каждом запросе строил их заново
        if instance and target_settings.scope_ == SINGLETON:
            target_settings_layer.cache_instance(target, instance)

        return instance
