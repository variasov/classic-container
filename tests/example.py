from abc import ABC, abstractmethod
from dataclasses import dataclass

class Interface(ABC):

    @abstractmethod
    def method(self): ...


class Implementation1(Interface):

    def method(self):
        return 1


class Implementation2(Interface):

    def method(self):
        return 2


class ErrorImplementation(Interface):

    def __init__(self, some_str: str):
        self.some_int = some_str + 'test'

    def method(self):
        return 2


class Composition:

    def __init__(self, impl: Interface):
        self.impl = impl


class ManyTypedComposition:
    # TODO Должны ли мы обрабатывать такие случаи перебором?
    def __init__(self, impl: Implementation1 | Implementation2 | None):
        self.impl = impl


class NextLevelComposition:

    def __init__(self, obj: Composition):
        self.obj = obj


def empty_factory() -> object:
    return None


def composition_factory(obj: Interface) -> Composition:
    return Composition(obj)


def some_func(some_arg: object) -> object:
    return some_arg


class SomeCls:
    pass


@dataclass
class AnotherCls:
    some: SomeCls


@dataclass
class YetAnotherCls:
    some: SomeCls
    another: AnotherCls
