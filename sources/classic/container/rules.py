from typing import Any

from .constants import SINGLETON, SCOPES
from .types import Target, Factory


class Rule:

    def __init__(self, cls: Target):
        self.cls = cls
        self.init_kwargs = {}
        self.replacement = None
        self.scope = SINGLETON

    def init(self, **kwargs: Any) -> 'Rule':
        self.init_kwargs = kwargs
        return self

    def replace(self, replacement: Factory) -> 'Rule':
        self.replacement = replacement
        return self

    def has_scope(self, scope: str) -> 'Rule':
        if scope not in SCOPES:
            raise ValueError(
                f'Scope name must be SINGLETON or TRANSIENT. Current is {scope}'
            )
        self.scope = scope
        return self


class FromGroup:

    def __init__(self, group: str):
        self.group = group
