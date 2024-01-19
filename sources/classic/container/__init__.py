from .constants import SINGLETON, TRANSIENT
from .exceptions import RegistrationError, ResolutionError
from .settings import Settings, settings, init, scope, factory, instance
from .container import Container


# Дефолтный контейнер, сделан ради удобства,
# чтобы не инстанцировать каждый раз в ручную.
# Конечно, вы можете создавать свои инстансы контейнера, когда вам нужно.

container = Container()
