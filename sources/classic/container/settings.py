from typing import Any, Dict

from .constants import SINGLETON, SCOPES
from .types import Factory


class Settings:

    def __init__(
        self, init: Dict[str, Any] = None, factory: Factory = None,
        group: str = None, scope: str = None, instance: Any = None,
    ):
        assert scope is None or scope in SCOPES, \
            f'Scope name must be SINGLETON or TRANSIENT. Current is "{scope}"'

        self.scope_ = scope or SINGLETON
        self.init_ = init or {}
        self.factory_ = factory
        self.group_ = group
        self.instance_ = instance

    def init(self, **kwargs: Any) -> Settings:
        self.init_ = kwargs
        return self

    def factory(self, factory: Factory) -> Settings:
        self.factory_ = factory
        return self

    def group(self, name: str) -> Settings:
        self.group_ = name
        return self

    def scope(self, name: str) -> Settings:
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


def group(name: str) -> Settings:
    return Settings(group=name)


def scope(name: str) -> Settings:
    return Settings(scope=name)


def instance(obj: Any) -> Settings:
    return Settings(instance=obj)
