import pytest
from classic.container import Settings, TRANSIENT

from example import Implementation1


@pytest.fixture
def settings():
    return Settings()


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
