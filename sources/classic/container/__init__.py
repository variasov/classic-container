from .constants import SINGLETON, TRANSIENT
from .exceptions import RegistrationError, ResolutionError
from .settings import Settings, settings, init, group, scope, factory, instance
from .container import Container


container = Container()
