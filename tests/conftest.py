import pytest
from classic.container import Container


@pytest.fixture
def container():
    return Container()
