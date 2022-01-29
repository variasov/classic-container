import inspect
from collections import defaultdict
from typing import Any, Dict, Type

from .rules import Rule, FromGroup
from .constants import SINGLETON
from .types import Factory, Target


Rules = Dict[Any, Rule]


class RegistrationError(BaseException):
    pass


class ResolutionError(BaseException):
    pass


class Registration:

    def __init__(self, target: Target):
        self.target = target
        self._factories = []

    def add_factory(self, factory: Factory):
        self._factories.append(factory)

    def find_factory(self, cls: Factory):
        for factory in self._factories:
            if factory == cls:
                return factory

    def get_factory(self, rules: Rules, group: str) -> Factory:
        if self.target in rules:
            params = rules[self.target]
            if params.replacement:
                factory = self.find_factory(params.replacement)
                if factory is None:
                    raise ResolutionError(
                        f"Can't resolve replacement {params.replacement} "
                        f"for class {self.target} in group {group}"
                    )

                return factory

        if inspect.isfunction(self.target):
            return self.target

        if not self._factories:
            raise ResolutionError(f'Class {self.target} do not have '
                                  f'registered implementations')

        if len(self._factories) > 1:
            raise ResolutionError(f'Can not to resolve {self.target}, '
                                  f'implementations are: {self._factories}')

        return self._factories[0]


class Registrations:

    def __init__(self):
        self._registrations = {}

    def get(self, target: Target) -> Registration:
        return self._registrations.get(target)

    def create(self, target: Target) -> Registration:
        registration = Registration(target)
        self._registrations[target] = registration
        return registration

    def get_or_create(self, target: Target) -> Registration:
        registration = self.get(target)
        if registration is None:
            registration = self.create(target)

        return registration

    def add(self, cls: Target, factory=None):
        registration = self.get_or_create(cls)
        if factory is not None:
            registration.add_factory(factory)

    def get_factory(self, cls: Target, rules: Rules, group: str) -> Factory:
        registration = self.get(cls)
        if registration is None:
            raise ResolutionError(f"Class {cls} don't registered in container")

        return registration.get_factory(rules, group)


class Container:

    def __init__(self):
        self._registrations = Registrations()
        self._rules = {
            'default': {},
        }
        self._instances = defaultdict(dict)

    def rules(self, *new_rules: Rule, group: str = 'default'):
        rules = self._rules.get(group, {})
        rules.update({
            rule.cls: rule
            for rule in new_rules
        })
        self._rules[group] = rules

        for rule in new_rules:
            if rule.replacement:
                registration = self._registrations.get_or_create(rule.cls)
                registration.add_factory(rule.replacement)

    @staticmethod
    def _get_interfaces_for_cls(target: Type):
        for cls in target.__mro__:
            if cls != object:
                yield cls

    @staticmethod
    def _factory_target(factory):
        signature = inspect.signature(factory)
        target = signature.return_annotation
        if target == inspect.Parameter.empty:
            raise RegistrationError()

        return target

    def register(self, *targets: Target):
        for target in targets:
            if inspect.isfunction(target):

                for cls in self._get_interfaces_for_cls(self._factory_target(target)):
                    self._registrations.add(cls, target)

            elif inspect.isabstract(target):
                self._registrations.add(target)

            elif inspect.isclass(target):
                for cls in self._get_interfaces_for_cls(target):
                    self._registrations.add(cls, target)
            else:
                raise RegistrationError(
                    f'Registration target must be class or function. '
                    f'{target} is {type(target)}'
                )

    def resolve(self, cls: Type, group='default') -> Any:
        return self._get_instance(cls, group)

    def _get_instance(self, cls: Type, group: str) -> Any:
        if inspect.isfunction(cls):
            cls = self._factory_target(cls)

        if cls in self._instances[group]:
            return self._instances[group][cls]
        return self._create_instance(cls, group)

    def _create_instance(self, cls: Type, group: str) -> Any:
        rules = self._rules[group]

        factory = self._registrations.get_factory(cls, rules, group)
        rule = rules.get(cls, Rule(cls))
        kwargs = {}

        if inspect.isfunction(cls):
            return cls

        signature = inspect.signature(factory)
        for parameter in signature.parameters.values():
            if parameter.annotation is inspect.Parameter.empty:
                raise ResolutionError(
                    f"Constructor for class {cls} don't have "
                    f"annotation for parameter {parameter.name}"
                )

            if parameter.name in rule.init_kwargs:
                value = rule.init_kwargs[parameter.name]
                if isinstance(value, FromGroup):
                    resolved_instance = self._get_instance(
                        parameter.annotation, value.group,
                    )
                else:
                    resolved_instance = value
            else:
                resolved_instance = self._get_instance(
                    parameter.annotation, group,
                )

            kwargs[parameter.name] = resolved_instance

        instance = factory(**kwargs)

        if rule.scope == SINGLETON:
            self._instances[group][cls] = instance

        return instance
