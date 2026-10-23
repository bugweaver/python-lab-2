"""Shared constants for the streamstats package."""

from typing import Final

EXIT_CODE_ERROR: Final = 2
TOP_ERROR_SOURCE_LIMIT: Final = 5
ERROR_LEVELS: Final[frozenset[str]] = frozenset({"ERROR", "CRITICAL"})
