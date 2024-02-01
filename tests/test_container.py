import pytest
from classic.container import (
    Container, RegistrationError, ResolutionError, Settings,
    TRANSIENT, factory, scope, instance, init,
)

import example
from example import (
    AnotherCls, Implementation1, Implementation2, Interface,
    SomeCls, YetAnotherCls, Composition, composition_factory,
    NextLevelComposition, ErrorImplementation, empty_factory, some_func
)


@pytest.fixture
def container():
    return Container()

@pytest.fixture
def settings():
    return Settings()


@pytest.mark.parametrize('obj', [
    (1,),
    (Implementation1(),),
])
def test_registration_error(obj, container):

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


def test_simple_resolving(container):
    container.register(SomeCls, AnotherCls, YetAnotherCls)

    check_class_resolve(container)


def test_resolve_with_abc(container):
    container.register(Interface, Implementation1)

    check_resolve_impl(container)


def test_resolve_without_implementation(container):
    container.register(Interface)

    with pytest.raises(ResolutionError):
        container.resolve(Interface)


def test_resolve_without_registration(container):
    with pytest.raises(ResolutionError):
        container.resolve(Interface)


def test_resolve_with_type_error(container):
    container.add_settings({Interface: factory(some_func)})
    with pytest.raises(ResolutionError):
        container.resolve(Interface)


def test_resolve_empty_factory(container):
    container.register(Composition)
    container.add_settings({
        Interface: factory(empty_factory)
    })
    with pytest.raises(ResolutionError):
        container.resolve(Composition)


def test_message_resolve_chain(container):
    container.register(
        ErrorImplementation, Composition,
        NextLevelComposition
    )

    container.add_settings({
        ErrorImplementation: init(some_str=[1,2,3])
    })
    with pytest.raises(ResolutionError) as ext:
        container.resolve(NextLevelComposition)

    error = (
        'Call of <class \'example.ErrorImplementation\'> failed with can only concatenate list (not "str") to list\n'
        'Resolve chain: \n'
        'Target: example.NextLevelComposition, Factory: example.NextLevelComposition, Arg: obj\n'
        'Target: example.Composition, Factory: example.Composition, Arg: impl\n'
        'Target: example.Interface, Factory: example.ErrorImplementation, Arg: some_str'
    )
    assert error == str(ext.value)


def test_resolve_with_abc_implicit(container):
    container.register(Implementation1)

    check_resolve_impl(container)


def test_resolve_module_1(container):
    container.register(example)

    container.add_settings({
        Interface: factory(Implementation1),
        Composition: factory(composition_factory)
    })

    check_next_level_composition_resolve(container)


def test_resolve_module_2(container):
    container.register(example)

    check_class_resolve(container=container)


def test_resolve_instance(container):
    implementation = Implementation1()

    container.add_settings({
        Implementation1: instance(implementation),
    })
    resolved = container.resolve(Implementation1)

    assert resolved is implementation


def test_factory_calling(container):
    container.register(Implementation1, composition_factory)

    container.add_settings({
        Composition: factory(composition_factory),
    })

    resolved = container.resolve(Composition)

    assert isinstance(resolved, Composition)
    assert isinstance(resolved.impl, Implementation1)


def test_factory_is_create_objects(container):
    container.register(Implementation1, composition_factory,
                       Composition, NextLevelComposition)
    container.add_settings({
        Composition: factory(composition_factory)
    })

    check_next_level_composition_resolve(container)


def test_resolve_init(container):
    impl = Implementation1()

    container.add_settings({
        Composition: init(impl=impl),
    })
    resolved = container.resolve(Composition)

    assert isinstance(resolved, Composition)
    assert resolved.impl is impl


def test_raise_when_many_implementations(container):
    container.register(Interface, Implementation1, Implementation2)

    with pytest.raises(ResolutionError):
        container.resolve(Interface)


def test_resolve_with_replacement(container):
    container.register(Interface, Implementation1, Implementation2)

    container.add_settings({
        Interface: factory(Implementation1),
    })

    check_resolve_impl(container)


def test_singleton_scope(container):
    container.register(Implementation1)

    resolved_1 = container.resolve(Implementation1)
    resolved_2 = container.resolve(Implementation1)

    assert resolved_1 is resolved_2


def test_transient_scope(container):
    container.register(Implementation1)

    container.add_settings({
        Implementation1: scope(TRANSIENT)
    })

    resolved_1 = container.resolve(Implementation1)
    resolved_2 = container.resolve(Implementation1)

    assert resolved_1 is not resolved_2


def test_reset_resolved_instances(container):
    container.register(example)

    # Проверка разрешения зависимостей без ошибок до reset-a.
    container.add_settings({Interface: factory(Implementation1)})
    container.resolve(Interface)

    result_1 = container.resolve(YetAnotherCls)
    container.reset()
    result_2 = container.resolve(YetAnotherCls)

    assert result_1 is not result_2
    with pytest.raises(ResolutionError):
        container.resolve(Interface)


def test_setting_raise_error(container):

    with pytest.raises(AssertionError):
        container.add_settings({
            Implementation1: Settings(
                instance=Implementation1(), factory=Implementation1
            ),
        })

    with pytest.raises(AssertionError):
        container.add_settings({
            Implementation1: Settings().instance(Implementation1()).factory(
                Implementation1
            ),
        })

    with pytest.raises(AssertionError):
        container.add_settings({
            Implementation1: Settings().instance(
                Implementation1()
            ).init(some=1),
        })

    with pytest.raises(AssertionError):
        container.add_settings({
            Implementation1: Settings().instance(Implementation1()).scope(
                TRANSIENT
            ),
        })

    with pytest.raises(AssertionError):
        container.add_settings({
            Implementation1: Settings().factory(Implementation1).instance(
                Implementation1()
            ).scope(TRANSIENT),
        })


def test_chain_responsibility_factory(settings):
    factory_settings = settings.factory(Implementation1)
    assert settings is factory_settings


def test_chain_responsibility_init(settings):
    init_settings = settings.init(some=1)
    assert settings is init_settings


def test_chain_responsibility_scope(settings):
    scope_settings = settings.scope(name=TRANSIENT)
    assert settings is scope_settings


def test_chain_responsibility_instance(settings):
    impl = Implementation1()
    impl_settings = settings.instance(instance=impl)
    assert settings is impl_settings


def test_chain_of_responsibility(settings):
    many_settings = settings.factory(
        Implementation1
    ).init(some=1).scope(name=TRANSIENT)
    assert settings is many_settings
