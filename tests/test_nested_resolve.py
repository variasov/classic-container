from classic.container import factory, instance

from example import (
    Composition, Interface, Implementation1, Implementation2,
    NextLevelComposition,
)


def test_nested_resolve(container):
    container.register(
        Composition, Interface,
        Implementation1, Implementation2,
    )

    def make_obj() -> Interface:
        return container.resolve(Implementation1)

    container.add_settings({
        Interface: factory(make_obj),
    })

    obj = container.resolve(Composition)

    assert isinstance(obj, Composition)
    assert hasattr(obj, 'impl')
    assert isinstance(obj.impl, Implementation1)


def test_nested_resolve_with_settings(container):
    container.register(
        Composition, Interface,
        Implementation1, Implementation2,
    )

    def make_obj() -> Interface:
        return container.resolve(
            Interface, {Interface: factory(Implementation1)},
        )

    container.add_settings({
        Interface: factory(make_obj),
    })

    obj = container.resolve(Composition)

    assert isinstance(obj, Composition)
    assert hasattr(obj, 'impl')
    assert isinstance(obj.impl, Implementation1)


def test_nested_resolve_with_instance(container):
    container.register(
        Composition, Interface,
        Implementation1, Implementation2,
    )

    just_obj = object()

    def make_obj() -> Interface:
        return container.resolve(
            Interface, {Interface: instance(just_obj)},
        )

    container.add_settings({
        Interface: factory(make_obj),
    })

    obj = container.resolve(Composition)

    assert isinstance(obj, Composition)
    assert hasattr(obj, 'impl')
    assert obj.impl is just_obj


def test_nested_resolve_with_simple_instancing(container):
    container.register(
        Composition, Interface,
        Implementation1, Implementation2,
        NextLevelComposition,
    )

    def make_obj() -> Composition:
        return Composition(
            impl=container.resolve(Implementation1),
        )

    container.add_settings({
        Composition: factory(make_obj),
    })

    obj = container.resolve(NextLevelComposition)

    assert isinstance(obj, NextLevelComposition)
    assert isinstance(obj.obj, Composition)
    assert isinstance(obj.obj.impl, Implementation1)
