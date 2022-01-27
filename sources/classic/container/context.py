from typing import Union, Dict, Optional, Any

from .constants import Scope


class Params:

    def __init__(self, init: Optional[Dict[str, Any]] = None,
                 replace: Optional[Any] = None,
                 scope: Optional[Scope] = Scope.SINGLETON):
        self.init = init
        self.replace = replace
        self.scope = scope


class FromContext:

    def __init__(self, context_name: str):
        self.context_name = context_name


class Replace:

    def __init__(self, replacement: Any):
        self.replacement = replacement


# Aliases
params = Params
default_params = Params(
    init={},
    scope=Scope.SINGLETON,
)

from_context = FromContext

Clauses = Union[Params, FromContext, Replace]


class Context:

    def __init__(self, name: str,
                 rules: Dict[str, Clauses] = None):
        self.name = name
        self.rules = rules or {}

    def update(self, rules: Dict[str, Clauses]):
        self.rules.update(rules)

    def merge(self, context: 'Context'):
        self.rules.update(context.rules)

    def params_for_target(self, target: str) -> Params:
        target_params = self.rules.get(target)

        if target_params is None:
            target_params = Params()
            self.rules[target] = target_params

        return target_params
