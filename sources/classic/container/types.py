from typing import Any, Callable, Union, Type

Factory = Callable[[Any], Any]
Target = Union[Factory, Type]
