"""Aggregate statistics from one or more event streams."""

from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol

from streamstats.constants import ERROR_LEVELS, TOP_ERROR_SOURCE_LIMIT
from streamstats.errors import StreamStatsError, UnsupportedFormatError
from streamstats.models import Event
from streamstats.parsers import SkipCounter, parse_csv, parse_jsonl


class EventParser(Protocol):
    """A streaming parser selected by an input format name."""

    def __call__(
        self,
        path: Path,
        *,
        skip_invalid: bool = False,
        skipped: SkipCounter | None = None,
    ) -> Iterator[Event]:
        """Read one file as a stream of events."""
        ...


_PARSERS: dict[str, EventParser] = {}


@dataclass
class Statistics:
    """Counters collected from a stream of valid events."""

    total_events: int = 0
    levels: Counter[str] = field(default_factory=Counter)
    sources: Counter[str] = field(default_factory=Counter)
    error_sources: Counter[str] = field(default_factory=Counter)
    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None
    skipped_lines: int = 0

    def add(self, event: Event) -> None:
        """Update every counter with one valid event."""
        level_name = str(event.level)
        self.total_events += 1
        self.levels[level_name] += 1
        self.sources[event.source] += 1
        if level_name in ERROR_LEVELS:
            self.error_sources[event.source] += 1
        self._include_timestamp(event.timestamp)

    def top_error_sources(
        self,
        limit: int = TOP_ERROR_SOURCE_LIMIT,
    ) -> list[tuple[str, int]]:
        """Return the sources with the most ERROR and CRITICAL events."""
        return self.error_sources.most_common(limit)

    def _include_timestamp(self, timestamp: datetime) -> None:
        """Expand the observed time range with one event timestamp."""
        if self.first_timestamp is None or timestamp < self.first_timestamp:
            self.first_timestamp = timestamp
        if self.last_timestamp is None or timestamp > self.last_timestamp:
            self.last_timestamp = timestamp


def analyze_files(
    paths: Sequence[Path],
    input_format: str,
    *,
    skip_invalid: bool = False,
) -> Statistics:
    """Merge event statistics from every path.

    Files are read one after another into the same counters. Invalid lines
    stop the analysis unless ``skip_invalid`` is set.
    """
    parser = _parser_for(input_format)
    stats = Statistics()
    skipped = SkipCounter()
    for path in paths:
        for event in parser(path, skip_invalid=skip_invalid, skipped=skipped):
            stats.add(event)
    stats.skipped_lines = skipped.count
    return stats


def register_parser(format_name: str, parser: EventParser) -> None:
    """Register a streaming parser under ``format_name``.
    """
    if not format_name.strip():
        raise StreamStatsError("Parser name must not be empty")
    _PARSERS[format_name] = parser


def unregister_parser(format_name: str) -> None:
    """Remove a parser from the registry if it is present."""
    _PARSERS.pop(format_name, None)


def registered_formats() -> tuple[str, ...]:
    """Return registered input format names in registration order."""
    return tuple(_PARSERS)


def _parser_for(input_format: str) -> EventParser:
    """Return the streaming parser registered for ``input_format``."""
    try:
        return _PARSERS[input_format]
    except KeyError as exc:
        raise UnsupportedFormatError(input_format) from exc


register_parser("csv", parse_csv)
register_parser("jsonl", parse_jsonl)
