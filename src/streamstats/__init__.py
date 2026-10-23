"""Streaming statistics for CSV and JSONL event logs."""

from streamstats.analysis import (
    EventParser,
    Statistics,
    analyze_files,
    register_parser,
    registered_formats,
)
from streamstats.errors import (
    CLIConfigError,
    InvalidEventError,
    InvalidTimestampError,
    StreamStatsError,
    UnsupportedFormatError,
)
from streamstats.models import Event

__all__ = (
    "CLIConfigError",
    "Event",
    "EventParser",
    "InvalidEventError",
    "InvalidTimestampError",
    "Statistics",
    "StreamStatsError",
    "UnsupportedFormatError",
    "analyze_files",
    "register_parser",
    "registered_formats",
)

__version__ = "0.1.0"
