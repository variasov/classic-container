import inspect
import threading
from typing import Callable

from .exceptions import ResolutionError
from .constants import SINGLETON, SIMPLE_TYPES
from .settings import Settings, empty_settings
from .types import Factory, Target, Registry, InstancesRegistry


class Resolve:
    step_template = (
        'Target: {cls_module}.{cls}, Factory: {fctr_module}.{fctr}, Arg: {arg}'
    )

    def __init__(self):
        self._stack = []

    def add_target(self, target) -> None:
        self._stack.append({
            'cls_module': target.__module__,
            'cls': target.__qualname__,
            'fctr_module': '-',
            'fctr': '-',
            'arg': '-'
        })

    def add_factory(self, factory) -> None:
        self._stack[-1]['fctr_module'] = factory.__module__
        self._stack[-1]['fctr'] = factory.__qualname__

    def add_arg(self, arg_name) -> None:
        self._stack[-1]['arg'] = arg_name

    def pop(self) -> None:
        self._stack.pop()

    def render(self):
        return '\n'.join((
            self.step_template.format_map(step)
            for step in self._stack
        ))



class Resolver:
    """
    Класс производит разрешение зависимостей компонентов приложения.

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

    def __call__(self, cls: Target) -> object:
        """
        Разрешает зависимости для указанной реализации,
        создает и возвращает инстанс класса.

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
        Во всех этих случаях контейнер выкидывает ResolutionError.

        Все ошибки состоят из двух частей. Первая часть уникальна для ошибки
        и объясняет причину, во второй части описано,
        что и в каком порядке пытался построить контейнер.
        Она состоит из строк, по три элемента в каждой:
         - Target: полное имя класса (some.module.SomeClass);
         - Factory: полное имя фабрики (another.module.SomeFactory);
         - Arg: имя аргумента фабрики.

        Пример:
        >>> from abc import ABC, abstractmethod
        ... from classic import container
        ...
        ... class Interface(ABC):
        ...
        ...     @abstractmethod
        ...     def method(self): ...
        ...
        ... class Implementation(Interface):
        ...
        ...     def __init__(self):
        ...         raise NotImplemented
        ...
        ...     def method(self):
        ...         return 1
        ...
        ... class Composition:
        ...
        ...     def __init__(self, impl: Interface):
        ...         self.impl = impl
        ...
        ... class SomeClass:
        ...
        ...     def __init__(self, obj: Composition):
        ...         self.obj = obj
        ...
        ...
        ... container.register(Interface, Implementation, SomeClass, Composition)
        ... container.resolve(SomeClass)
        ...
        classic.container.exceptions.ResolutionError: Class \
        <class 'example.Interface'> do not have registered implementations.
        Resolve chain:
        Target: app.SomeClass, Factory: app.SomeClass, Arg: obj
        Target: app.Composition, Factory: app.Composition, Arg: impl
        Target: app.Interface, Factory: app.Implementation, Arg: -

        """
        with self._lock:
            stack = Resolve()
            return self._get_instance(cls, stack)

    def reset(self):
        self._settings = dict()
        self._instances = dict()

    def _get_instance(self, cls: Target, stack: Resolve) -> object:
        stack.add_target(cls)
        if cls in self._instances:
            return self._instances[cls]
        instance = self._create_instance(cls, stack)
        stack.pop()
        return instance

    def _get_factory_for(self, cls: Target, stack: Resolve) -> Factory:
        factories = self._registry[cls]

        if not factories:
            raise ResolutionError(
                f'Class {cls} do not have registered implementations.\n'
                f'Resolve chain: \n{stack.render()}'
            )

        if len(factories) > 1:
            raise ResolutionError(
                f'Can not to resolve {cls}, '
                f'implementations are: {factories}\n'
                f'Resolve chain: \n{stack.render()}'
            )

        return factories[0]

    def _call_factory(self, factory: Factory, stack: Resolve) -> object:
        settings = self._settings.get(factory, empty_settings)
        kwargs = self._resolve_kwargs_for_factory(factory, settings, stack)

        try:
            return factory(**kwargs)
        except TypeError as exc:
            raise ResolutionError(
                f'Call of {factory} failed with {exc}\n'
                f'Resolve chain: \n{stack.render()}'
            )

    def _create_instance(self, cls: Target, stack: Resolve) -> object:
        settings = self._settings.get(cls, empty_settings)
        if settings.instance_:
            return settings.instance_

        factory = settings.factory_ or self._get_factory_for(cls, stack)
        instance = self._call_factory(factory, stack)

        if instance and settings.scope_ == SINGLETON:
            self._instances[cls] = instance

        return instance

    def _resolve_kwargs_for_factory(
        self, factory: Factory, settings: Settings, stack: Resolve
    ) -> dict[str, object]:
        kwargs = {}

        stack.add_factory(factory)
        signature = inspect.signature(factory)
        for parameter in signature.parameters.values():
            stack.add_arg(parameter.name)
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

            instance = self._get_instance(parameter.annotation, stack)
            if instance is not None:
                kwargs[parameter.name] = instance

            elif parameter.default is inspect.Parameter.empty:
                raise ResolutionError(
                    f"Can't resole attribute {parameter.name} "
                    f"for {factory}, attribute don't have default value "
                    f"and {factory} has returned None \n"
                    f"Resolve chain: \n{stack.render()}"
                )

        return kwargs
