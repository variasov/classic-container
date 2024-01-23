from unittest.mock import Mock

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


def check_class_resolve(container):

    resolved = container.resolve(YetAnotherCls)

    assert resolved is not None
    assert isinstance(resolved, YetAnotherCls)
    assert isinstance(resolved.some, SomeCls)
    assert isinstance(resolved.another, AnotherCls)
    assert isinstance(resolved.another.some, SomeCls)
    assert resolved.some is resolved.another.some


def check_resolve_impl(container):
    resolved = container.resolve(Interface)

    assert isinstance(resolved, Implementation1)


def check_next_level_composition_resolve(container):
    resolved = container.resolve(NextLevelComposition)

    assert isinstance(resolved, NextLevelComposition)
    assert isinstance(resolved.obj, Composition)
    assert isinstance(resolved.obj.impl, Implementation1)


def test_simple_resolving():
    container = Container()
    container.register(SomeCls, AnotherCls, YetAnotherCls)

    check_class_resolve(container)


def test_resolve_with_abc():
    container = Container()
    container.register(Interface, Implementation1)

    check_resolve_impl(container)


def test_resolve_without_implementation():
    container = Container()
    container.register(Interface)

    with pytest.raises(ResolutionError):
        container.resolve(Interface)


def test_resolve_with_abc_implicit():
    container = Container()
    container.register(Implementation1)

    check_resolve_impl(container)


def test_resolve_module_1():
    container = Container()
    container.register(example)

    container.add_settings({
        Interface: factory(Implementation1),
        Composition: factory(composition_factory)
    })

    check_next_level_composition_resolve(container)


def test_resolve_module_2():
    container = Container()
    container.register(example)

    check_class_resolve(container=container)


def test_resolve_instance():
    container = Container()
    implementation = Implementation1()

    container.add_settings({
        Implementation1: instance(implementation),
    })
    resolved = container.resolve(Implementation1)

    assert resolved is implementation


def test_factory_calling():
    container = Container()
    container.register(Implementation1, composition_factory)

    container.add_settings({
        Composition: factory(composition_factory),
    })

    resolved = container.resolve(Composition)

    assert isinstance(resolved, Composition)
    assert isinstance(resolved.impl, Implementation1)


def test_factory_is_create_objects():
    container = Container()
    container.register(Implementation1, composition_factory,
                       Composition, NextLevelComposition)
    container.add_settings({
        Composition: factory(composition_factory)
    })

    check_next_level_composition_resolve(container)


def test_resolve_init():
    container = Container()
    impl = Implementation1()

    container.add_settings({
        Composition: init(impl=impl),
    })
    resolved = container.resolve(Composition)

    assert isinstance(resolved, Composition)
    assert resolved.impl is impl


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

    check_resolve_impl(container)


def test_singleton_scope():
    container = Container()
    container.register(Implementation1)

    resolved_1 = container.resolve(Implementation1)
    resolved_2 = container.resolve(Implementation1)

    assert resolved_1 is resolved_2


def test_transient_scope():
    container = Container()
    container.register(Implementation1)

    container.add_settings({
        Implementation1: scope(TRANSIENT)
    })

    resolved_1 = container.resolve(Implementation1)
    resolved_2 = container.resolve(Implementation1)

    assert resolved_1 is not resolved_2


def test_lock():
    container = Container()
    impl = Implementation1()
    impl_factory = Mock(return_value=impl)

    container.add_settings({
        Implementation1: factory(impl_factory)
    })
    resolved = container.resolve(Implementation1)

    impl_factory.assert_called_once()
    assert resolved is impl
