from typing import Any, Dict

from .constants import SINGLETON, SCOPES
from .types import Factory


class Settings:
    """
    Класс настроек для контейнра. Предпологается, что этот объект инстанцируется
    контейнером или специальными методами и используется только "под капотом"
    """
    def __init__(
        self, init: Dict[str, Any] = None, factory: Factory = None,
        scope: str = None, instance: Any = None,
    ):
        assert scope is None or scope in SCOPES, \
            f'Scope name must be SINGLETON or TRANSIENT. Current is "{scope}"'

        self.scope_ = scope or SINGLETON
        self.init_ = init or {}
        self.factory_ = factory
        self.instance_ = instance

    def init(self, **kwargs: Any) -> 'Settings':
        self.init_ = kwargs
        return self

    def factory(self, factory: Factory) -> 'Settings':
        self.factory_ = factory
        return self

    def scope(self, name: str) -> 'Settings':
        assert name in SCOPES, (
            f'Scope name must be SINGLETON or TRANSIENT. Current is "{name}"'
        )
        self.scope_ = name
        return self


settings = Settings
empty_settings = Settings()


def init(**kwargs: Any) -> Settings:
    """
    Подразумевает использование только для добавления настроек компонентов
    в контейнер.

    Позволяет передать инстансы зависимостей в явном виде.
    Значения ожидает в виде словаря, где ключ имя ожидаемого параметра,
    а значение его реализация.

    Самое частое использование - передача простых объектов (чисел, строк).
    """
    return Settings(init=kwargs)


def factory(factory: Factory) -> Settings:
    """
    Подразумевает использование только для добавления настроек компонентов
    в контейнер.

    """
    return Settings(factory=factory)


def scope(name: str) -> Settings:
    """
    Подразумевает использование только для добавления настройки scope для
    компонента в контейнере. Для каждого компонента настройка scope
    добавляется отдельно!

    По умолчанию наш контейнер использует 'SINGLETON' для компонентов.
    При такой настройке объект создается при первом обращении к нему,
    все последующие запросы используют один и тот же ранее созданный
    объект сервиса

    Так же существует возможность использовать 'TRANSIENT' для компонента.
    При каждом обращении к сервису создается новый объект сервиса.
    """
    return Settings(scope=name)


def instance(obj: Any) -> Settings:
    """
    Подразумевает использование только для добавления настроек компонентов
    в контейнер.

    Используется для передачи готовых объектов для ручного разрешения
    зависимостей.
    """
    return Settings(instance=obj)
