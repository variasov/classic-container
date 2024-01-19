from typing import Any, Dict

from .constants import SINGLETON, SCOPES
from .types import Factory


class Settings:

    def __init__(
        self, init: Dict[str, Any] = None, factory: Factory = None,
        scope: str = None, instance: Any = None,
    ):
        """

        :param init:
        :param factory:
        :param scope:
        :param instance:
        """
        assert scope is None or scope in SCOPES, \
            f'Scope name must be SINGLETON or TRANSIENT. Current is "{scope}"'

        self.scope_ = scope or SINGLETON
        self.init_ = init or {}
        self.factory_ = factory
        self.instance_ = instance

    def init(self, **kwargs: Any) -> 'Settings':
        """

        :param kwargs:
        :return:
        """
        self.init_ = kwargs
        return self

    def factory(self, factory: Factory) -> 'Settings':
        """

        :param factory:
        :return:
        """
        self.factory_ = factory
        return self

    def scope(self, name: str) -> 'Settings':
        """

        :param name:
        :return:
        """
        assert name in SCOPES, (
            f'Scope name must be SINGLETON or TRANSIENT. Current is "{name}"'
        )
        self.scope_ = name
        return self


settings = Settings
empty_settings = Settings()


def init(**kwargs: Any) -> Settings:
    return Settings(init=kwargs)


def factory(factory: Factory) -> Settings:
    return Settings(factory=factory)


def scope(name: str) -> Settings:
    return Settings(scope=name)


def instance(obj: Any) -> Settings:
    return Settings(instance=obj)
