from .constants import SINGLETON, TRANSIENT
from .settings import Settings, settings, init, scope, factory, instance
from .container import Container


# Дефолтный контейнер, сделан ради удобства,
# чтобы не инстанцировать каждый раз вручную.
# Конечно, вы можете создавать свои инстансы контейнера, когда вам нужно.
container = Container()
