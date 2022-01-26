from abc import ABC, abstractmethod
from dataclasses import dataclass

import pytest
from classic.container import Container, ResolutionError


class Interface(ABC):

    @abstractmethod
    def method(self): ...


class Implementation1(Interface):

    def method(self):
        return 1


class Implementation2(Interface):

    def method(self):
        return 2


class SomeCls:
    pass


@dataclass
class AnotherCls:
    some: SomeCls


@dataclass
class YetAnotherCls:
    some: SomeCls
    another: AnotherCls


def test_simple_resolving():
    container = Container()
    container.register(SomeCls)
    container.register(AnotherCls)
    container.register(YetAnotherCls)

    instance = container.resolve(YetAnotherCls)

    assert instance is not None
    assert isinstance(instance.some, SomeCls)
    assert isinstance(instance.another, AnotherCls)
    assert instance.some is instance.another.some


def test_resolve_with_abc():
    container = Container()
    container.register(Interface)
    container.register(Interface, Implementation1)

    instance = container.resolve(Interface)

    assert instance is not None
    assert isinstance(instance, Implementation1)


def test_raise_when_many_implementations():
    container = Container()
    container.register(Interface)
    container.register(Interface, Implementation1)
    container.register(Interface, Implementation2)

    with pytest.raises(ResolutionError):
        container.resolve(Interface)


def test_resolve_implementation_in_context():
    container = Container()
    container.register(Interface)
    container.register(Interface, Implementation1)
    container.register(Interface, Implementation2)

    container.register_context(
        default={
            Interface: Implementation1
        }
    )

    instance = container.resolve(Interface)

    assert instance is not None
    assert isinstance(instance, Implementation1)
