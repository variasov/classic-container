from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional


class Interface(ABC):

    @abstractmethod
    def method(self): ...


class Implementation1(Interface):

    def method(self):
        return 1


# TODO: Заюзать или выпилить
class AnyImplementation:

    def method(self):
        return 1


class Implementation2(Interface):

    def method(self):
        return 2


# TODO: Заюзать или выпилить
class ErrorImplementation(Interface):

    def __init__(self, some_str: str):
        self.some_int = some_str + 'test'

    def method(self):
        return 2


class Composition:

    def __init__(self, impl: Interface):
        self.impl = impl


# TODO: Заюзать или выпилить
class ManyImplComposition(Composition):

    def __init__(self, any_impl: AnyImplementation, impl: Interface):
        super().__init__(impl)
        self.any_impl = any_impl


class ManyTypedComposition:
    # TODO Должны ли мы обрабатывать такие случаи перебором?
    def __init__(self, impl: Implementation1 | Implementation2 | None):
        self.impl = impl


class NextLevelComposition:

    def __init__(self, obj: Composition):
        self.obj = obj


class SomeCls:
    pass


def empty_factory() -> object:
    return None


def composition_factory(obj: Interface) -> Composition:
    return Composition(obj)


def some_func(some_arg: object) -> object:
    return some_arg


@dataclass
class AnotherCls:
    some: SomeCls


@dataclass
class YetAnotherCls:
    some: SomeCls
    another: AnotherCls


@dataclass
class CycledA:
    instance: 'CycledB'


@dataclass
class CycledB:
    instance: CycledA


@dataclass
class SelfReferenced:
    instance: 'SelfReferenced'


T = TypeVar('T')
class SomeGeneric(Generic[T]):
    pass


@dataclass
class DependsFromGeneric:
    dep: SomeGeneric[int]


@dataclass
class DependsFromOptionalGeneric:
    dep: Optional[SomeGeneric[int]] = None


class ClsWithArgs:

    def __init__(self, *args):
        self.args = args


class ClsWithKwargs:

    def __init__(self, **kwargs):
        self.kwargs = kwargs
