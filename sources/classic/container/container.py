import inspect
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Any, List, Optional, Dict, Union

from classic.components import registry


__all__ = ['Container', 'ResolutionError', 'params', 'replace', 'from_context']


SINGLETON = 'SINGLETON'
TRANSIENT = 'TRANSIENT'


# Helpers

class Params:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FromContext:

    def __init__(self, context):
        self.context = context


class Replace:

    def __init__(self, replacement):
        self.replacement = replacement


class ResolutionError(BaseException):
    pass


# Aliases
params = Params
from_context = FromContext
replace = Replace

Clauses = Union[Params, FromContext, Replace]


class Context:

    def __init__(self,
                 name: str,
                 rules: Dict[str, Clauses] = None):
        self.name = name
        self.rules = rules or {}

    def update(self, rules: Dict[str, Clauses]):
        self.rules.update(rules)

    def merge(self, context: 'Context'):
        self.rules.update(context.rules)

    def params_for_target(self, target: str) -> Params:
        target_params = self.rules.get(target)

        if target_params is None:
            target_params = Params()
            self.rules[target] = target_params

        return target_params


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
            if params.implementation:
                factory = self.find_factory(params.implementation)
                if factory is None:
                    raise ValueError()

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


def make_defaultdict(factory):
    def wrapper():
        return defaultdict(factory)
    return wrapper


@dataclass
class Instances:
    registrations: Registrations
    instances: Dict[Context, Dict[Any, Any]] = field(
        default_factory=make_defaultdict(dict)
    )

    def get(self, cls, context):
        if cls in self.instances[context]:
            return self.instances[context][cls]
        return self.create(cls, context)

    def create(self, cls, context):
        factory = self.registrations.get_factory(cls, context)
        kwargs = {}

        signature = inspect.signature(cls)
        for parameter in signature.parameters.values():
            if parameter.annotation is inspect.Parameter.empty:
                raise ResolutionError(
                    f"Constructor for class {cls} don't have "
                    f"annotation for parameter {parameter.name}"
                )

            kwargs[parameter.name] = self.get(parameter.annotation, context)

        instance = factory(**kwargs)
        self.instances[context][cls] = instance
        return instance


class Container:

    def __init__(self):
        self.registrations = Registrations()
        self.instances = Instances(self.registrations)
        self.contexts = {
            'default': Context('default'),
        }

    def register_context(self, **contexts):
        for name, rules in contexts.items():
            context = self.contexts.get(name)
            if context is None:
                context = Context(name)
                self.contexts[name] = context

            context.update(rules)

    def register(self, target, factory=None):
        self.registrations.add(target, factory)

        # Every non-abstract is a factory for self
        if not inspect.isabstract(target):
            self.registrations.add(target, target)

    def resolve(self, cls, context='default'):
        return self.instances.get(cls, self.contexts[context])

    # def resolve(self, cls, in_context='default'):
    #     current_context = self.contexts[in_context]
    #     params_for_resolve = current_context.params_for_target(cls)
    #
    #     if params_for_resolve.replace:
    #         registration = self.get(params_for_resolve.replace)
    #     else:
    #         registration = self.get(cls)
    #
    #     if registration is None:
    #         raise ValueError
    #
    #     kwargs = {}
    #
    #     for name, attribute in attr.fields_dict(cls).items():
    #         resolve_option = params_for_resolve.kwargs.get(name)
    #
    #         dependency = attribute.type
    #
    #         context_for_resolve = current_context
    #         if isinstance(resolve_option, FromContext):
    #             context_for_resolve = self.contexts[dependency.context]
    #
    #         kwargs[name] = self.resolve(dependency,
    #                                     context_for_resolve.name)
    #
    #     factory = registration.get_factory(current_context)
    #     return factory(**kwargs)


class AutoContainer(Container):

    def __init__(self):
        super().__init__()

        for cls in registry.classes:
            for interface in self._interfaces_for(cls):
                self.register(interface, cls)
            self.register(cls, cls)

    def _interfaces_for(self, cls):
        if cls.__bases__ == (object,):
            return
        return cls.__bases__
