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


class Composition:

    def __init__(self, impl: Interface):
        self.impl = impl


class NextLevelComposition:

    def __init__(self, obj: Composition):
        self.obj = obj


class SomeCls:
    pass


def composition_factory(obj: Interface) -> Composition:
    return Composition(obj)


@dataclass
class AnotherCls:
    some: SomeCls


@dataclass
class YetAnotherCls:
    some: SomeCls
    another: AnotherCls