"""Streaming statistics for CSV and JSONL event logs."""

from streamstats.analysis import Statistics, analyze_files
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
    "InvalidEventError",
    "InvalidTimestampError",
    "Statistics",
    "StreamStatsError",
    "UnsupportedFormatError",
    "analyze_files",
)

__version__ = "0.1.0"
