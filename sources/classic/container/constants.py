from enum import Enum, IntEnum
from datetime import date, datetime
from uuid import UUID


SINGLETON = 'SINGLETON'
TRANSIENT = 'TRANSIENT'

SCOPES = (SINGLETON, TRANSIENT)
SIMPLE_TYPES = (
    int, str, float,
    Enum, IntEnum,
    UUID,
    date, datetime
)
