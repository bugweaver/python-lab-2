"""Allowed event severity levels."""

from enum import StrEnum


class Level(StrEnum):
    """Severity of one log event."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
