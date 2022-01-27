import inspect
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Any, List, Dict

from .context import Context, FromContext, default_params
from .constants import Scope

__all__ = ['Container', 'ResolutionError']


class ResolutionError(BaseException):
    pass


@dataclass
class Registration:
    target: Any
    factories: List[Any] = field(default_factory=list)

    def add_factory(self, factory):
        self.factories.append(factory)

    def find_factory(self, cls):
        for factory in self.factories:
            if factory == cls:
                return factory

    def get_factory(self, context):
        if self.target in context.rules:
            params = context.rules[self.target]
            if params.replace:
                factory = self.find_factory(params.replace)
                if factory is None:
                    raise ResolutionError(
                        f"Can't resolve replacement {params.replace} "
                        f"for class {self.target} in context {context.name}"
                    )

                return factory

        if not self.factories:
            raise ResolutionError(f'Class {self.target} do not have '
                                  f'registered implementations')

        if len(self.factories) > 1:
            raise ResolutionError(f'Can not to resolve {self.target}, '
                                  f'implementations are: {self.factories}')

        return self.factories[0]


@dataclass
class Registrations:
    registrations: Dict[Any, Registration] = field(default_factory=dict)

    def get(self, target):
        return self.registrations.get(target)

    def create(self, target):
        registration = Registration(target)
        self.registrations[target] = registration
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

    def get_factory(self, cls, context: Context):
        registration = self.get(cls)

        if registration is None:
            raise ResolutionError(f"Class {cls} don't registered in container")

        return registration.get_factory(context)


class Container:

    def __init__(self):
        self.registrations = Registrations()
        self.contexts = {
            'default': Context('default'),
        }
        self.instances = defaultdict(dict)

    def settings(self, settings: Dict[Any, Any], context='default'):
        context_obj = self.contexts.get(context)
        if context_obj is None:
            context_obj = Context(context)
            self.contexts[context] = context_obj

        context_obj.update(settings)

    @staticmethod
    def _get_interfaces_for_cls(target):
        for cls in target.__mro__:
            if cls != object:
                yield cls

    def register(self, *targets):
        for target in targets:
            if inspect.isabstract(target):
                self.registrations.add(target)
            else:
                for cls in self._get_interfaces_for_cls(target):
                    self.registrations.add(cls, target)

    def resolve(self, cls, context='default'):
        return self._get_instance(cls, self.contexts[context])

    def _get_instance(self, cls, context):
        if cls in self.instances[context]:
            return self.instances[context][cls]
        return self._create_instance(cls, context)

    def _create_instance(self, cls, context):
        rule = context.rules.get(cls, default_params)

        factory = self.registrations.get_factory(cls, context)
        kwargs = {}

        signature = inspect.signature(cls)
        for parameter in signature.parameters.values():
            if parameter.annotation is inspect.Parameter.empty:
                raise ResolutionError(
                    f"Constructor for class {cls} don't have "
                    f"annotation for parameter {parameter.name}"
                )

            if parameter.name in rule.init:
                value = rule.init[parameter.name]
                if isinstance(value, FromContext):
                    new_context = self.contexts[value.context_name]
                    resolved_instance = self._get_instance(
                        parameter.annotation, new_context,
                    )
                else:
                    resolved_instance = value
            else:
                resolved_instance = self._get_instance(
                    parameter.annotation, context,
                )

            kwargs[parameter.name] = resolved_instance

        instance = factory(**kwargs)

        if rule.scope == Scope.SINGLETON:
            self.instances[context][cls] = instance

        return instance
