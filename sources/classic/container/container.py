import inspect
from collections import defaultdict
from typing import Any, Dict

from .settings import Rule, FromContext
from .constants import SINGLETON

__all__ = ['Container', 'ResolutionError']


Rules = Dict[Any, Rule]


class ResolutionError(BaseException):
    pass


class Registration:

    def __init__(self, target: Any):
        self.target = target
        self._factories = []

    def add_factory(self, factory):
        self._factories.append(factory)

    def find_factory(self, cls):
        for factory in self._factories:
            if factory == cls:
                return factory

    def get_factory(self, rules: Rules, ctx_name: str):
        if self.target in rules:
            params = rules[self.target]
            if params.replacement:
                factory = self.find_factory(params.replacement)
                if factory is None:
                    raise ResolutionError(
                        f"Can't resolve replacement {params.replacement} "
                        f"for class {self.target} in context {ctx_name}"
                    )

                return factory

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

    def get(self, target):
        return self._registrations.get(target)

    def create(self, target):
        registration = Registration(target)
        self._registrations[target] = registration
        return registration

    def get_or_create(self, target):
        registration = self.get(target)
        if registration is None:
            registration = self.create(target)

        return registration

    def add(self, cls, factory=None):
        registration = self.get_or_create(cls)
        if factory is not None:
            registration.add_factory(factory)

    def get_factory(self, cls, rules: Rules, ctx_name: str):
        registration = self.get(cls)
        if registration is None:
            raise ResolutionError(f"Class {cls} don't registered in container")

        return registration.get_factory(rules, ctx_name)


class Container:

    def __init__(self):
        self._registrations = Registrations()
        self._contexts = {
            'default': {},
        }
        self._instances = defaultdict(dict)

    def rules(self, *new_rules: Rule, context: str = 'default'):
        rules = self._contexts.get(context, {})
        rules.update({
            rule.cls: rule
            for rule in new_rules
        })
        self._contexts[context] = rules

    @staticmethod
    def _get_interfaces_for_cls(target):
        for cls in target.__mro__:
            if cls != object:
                yield cls

    def register(self, *targets):
        for target in targets:
            if inspect.isabstract(target):
                self._registrations.add(target)
            else:
                for cls in self._get_interfaces_for_cls(target):
                    self._registrations.add(cls, target)

    def resolve(self, cls, context='default'):
        return self._get_instance(cls, context)

    def _get_instance(self, cls, ctx_name):
        if cls in self._instances[ctx_name]:
            return self._instances[ctx_name][cls]
        return self._create_instance(cls, ctx_name)

    def _create_instance(self, cls, ctx_name):
        rules = self._contexts[ctx_name]

        factory = self._registrations.get_factory(cls, rules, ctx_name)
        rule = rules.get(cls, Rule(cls))
        kwargs = {}

        signature = inspect.signature(cls)
        for parameter in signature.parameters.values():
            if parameter.annotation is inspect.Parameter.empty:
                raise ResolutionError(
                    f"Constructor for class {cls} don't have "
                    f"annotation for parameter {parameter.name}"
                )

            if parameter.name in rule.init_kwargs:
                value = rule.init_kwargs[parameter.name]
                if isinstance(value, FromContext):
                    resolved_instance = self._get_instance(
                        parameter.annotation, value.context_name,
                    )
                else:
                    resolved_instance = value
            else:
                resolved_instance = self._get_instance(
                    parameter.annotation, ctx_name,
                )

            kwargs[parameter.name] = resolved_instance

        instance = factory(**kwargs)

        if rule.scope == SINGLETON:
            self._instances[ctx_name][cls] = instance

        return instance
