import enum


class Scope(enum.Enum):
    SINGLETON = enum.auto()
    TRANSIENT = enum.auto()
