from abc import ABC, abstractmethod
from dataclasses import dataclass

import pytest
from classic.container import (
    Container, ResolutionError, TRANSIENT, cls, from_context
)


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
    assert isinstance(instance, YetAnotherCls)
    assert isinstance(instance.some, SomeCls)
    assert isinstance(instance.another, AnotherCls)
    assert isinstance(instance.another.some, SomeCls)
    assert instance.some is instance.another.some


def test_resolve_with_abc():
    container = Container()
    container.register(Interface)
    container.register(Implementation1)

    instance = container.resolve(Interface)

    assert instance is not None
    assert isinstance(instance, Implementation1)


def test_raise_when_many_implementations():
    container = Container()
    container.register(Interface)
    container.register(Implementation1)
    container.register(Implementation2)

    with pytest.raises(ResolutionError):
        container.resolve(Interface)


def test_resolve_with_replacement():
    container = Container()
    container.register(Interface)
    container.register(Implementation1)
    container.register(Implementation2)

    container.rules(
        cls(Interface).replace(Implementation1),
    )

    instance = container.resolve(Interface)

    assert instance is not None
    assert isinstance(instance, Implementation1)


def test_resolve_replace_from_context():
    container = Container()
    container.register(Interface)
    container.register(Implementation1)
    container.register(Implementation2)
    container.register(Composition)

    container.rules(
        cls(Interface).replace(Implementation1),
        context='ctx1'
    )

    container.rules(
        cls(Interface).replace(Implementation2),
        context='ctx2',
    )

    container.rules(
        cls(Composition).init(impl=from_context('ctx1')),
    )

    instance = container.resolve(Composition)

    assert instance is not None
    assert isinstance(instance, Composition)
    assert isinstance(instance.impl, Implementation1)


def test_singleton_scope():
    container = Container()
    container.register(Implementation1)

    instance = container.resolve(Implementation1)
    instance2 = container.resolve(Implementation1)

    assert instance is instance2


def test_transient_scope():
    container = Container()
    container.register(Implementation1)

    container.rules(
        cls(Implementation1).has_scope(TRANSIENT)
    )

    instance = container.resolve(Implementation1)
    instance2 = container.resolve(Implementation1)

    assert instance is not instance2
