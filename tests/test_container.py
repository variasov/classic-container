import pytest
from classic.container import (
    Container, RegistrationError, ResolutionError,
    TRANSIENT, factory, scope, instance, init
)

import example
from example import (
    AnotherCls, Implementation1, Implementation2, Interface,
    SomeCls, YetAnotherCls, Composition, composition_factory,
    NextLevelComposition

)


@pytest.mark.parametrize('obj', [
    (1,),
    (Implementation1(),),
])
def test_registration_error(obj):
    container = Container()

    with pytest.raises(RegistrationError):
        container.register(obj)


def test_simple_resolving():
    container = Container()
    container.register(SomeCls, AnotherCls, YetAnotherCls)

    instance = container.resolve(YetAnotherCls)

    assert instance is not None
    assert isinstance(instance, YetAnotherCls)
    assert isinstance(instance.some, SomeCls)
    assert isinstance(instance.another, AnotherCls)
    assert isinstance(instance.another.some, SomeCls)
    assert instance.some is instance.another.some


def test_resolve_with_abc():
    container = Container()
    container.register(Interface, Implementation1)

    instance = container.resolve(Interface)

    assert isinstance(instance, Implementation1)


def test_resolve_without_implementation():
    container = Container()
    container.register(Interface)

    with pytest.raises(ResolutionError):
        container.resolve(Interface)


def test_resolve_with_abc_implicit():
    container = Container()
    container.register(Implementation1)

    instance = container.resolve(Interface)

    assert isinstance(instance, Implementation1)


# регистарция модуля
def test_resolve_model1():
    container = Container()
    container.register(example)

    container.add_settings({
        Interface: factory(Implementation1),
        Composition: factory(composition_factory)
    })

    instance = container.resolve(NextLevelComposition)

    assert isinstance(instance, NextLevelComposition)
    assert isinstance(instance.obj, Composition)
    assert isinstance(instance.obj.impl, Implementation1)


def test_resolve_model2():
    container = Container()
    container.register(example)

    instance = container.resolve(YetAnotherCls)

    assert instance is not None
    assert isinstance(instance, YetAnotherCls)
    assert isinstance(instance.some, SomeCls)
    assert isinstance(instance.another, AnotherCls)
    assert isinstance(instance.another.some, SomeCls)
    assert instance.some is instance.another.some


# проверить instance
def test_resolve_instance():
    container = Container()
    implementation = Implementation1()
    composition = Composition(implementation)

    container.add_settings({
        Composition: instance(composition),
    })
    composition_instance = container.resolve(Composition)

    assert isinstance(composition_instance, Composition)
    assert isinstance(composition_instance.impl, Implementation1)


def test_factory_calling():
    container = Container()
    container.register(Implementation1, composition_factory)

    container.add_settings({
        Composition: factory(composition_factory),
    })

    instance = container.resolve(Composition)

    assert isinstance(instance, Composition)
    assert isinstance(instance.impl, Implementation1)


def test_factory_is_create_objects():
    container = Container()
    container.register(Implementation1, composition_factory,
                       Composition, NextLevelComposition)
    container.add_settings({
        Composition: factory(composition_factory)
    })

    instance = container.resolve(NextLevelComposition)

    assert isinstance(instance, NextLevelComposition)
    assert isinstance(instance.obj, Composition)
    assert isinstance(instance.obj.impl, Implementation1)

# проверить init в настройка контейнера, подмешивает как есть

def test_raise_when_many_implementations():
    container = Container()
    container.register(Interface, Implementation1, Implementation2)

    with pytest.raises(ResolutionError):
        container.resolve(Interface)


def test_resolve_with_replacement():
    container = Container()
    container.register(Interface, Implementation1, Implementation2)

    container.add_settings({
        Interface: factory(Implementation1),
    })

    instance = container.resolve(Interface)

    assert isinstance(instance, Implementation1)


def test_singleton_scope():
    container = Container()
    container.register(Implementation1)

    instance = container.resolve(Implementation1)
    instance2 = container.resolve(Implementation1)

    assert instance is instance2


def test_transient_scope():
    container = Container()
    container.register(Implementation1)

    container.add_settings({
        Implementation1: scope(TRANSIENT)
    })

    instance = container.resolve(Implementation1)
    instance2 = container.resolve(Implementation1)

    assert instance is not instance2
