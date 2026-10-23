"""JSON report built from collected event statistics."""

import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from streamstats.analysis import Statistics
from streamstats.enums import Level


class ErrorSourceEntry(TypedDict):
    """One row of the top error-source list."""

    source: str
    count: int


class Report(TypedDict):
    """JSON object written for an analysis run."""

    total_events: int
    levels: dict[str, int]
    sources: dict[str, int]
    top_error_sources: list[ErrorSourceEntry]
    first_timestamp: str | None
    last_timestamp: str | None
    skipped_lines: int


def build_report(stats: Statistics) -> Report:
    """Convert counters into a JSON-ready report."""
    return Report(
        total_events=stats.total_events,
        levels={level.value: stats.levels[level.value] for level in Level},
        sources=dict(sorted(stats.sources.items())),
        top_error_sources=[
            ErrorSourceEntry(source=source, count=count)
            for source, count in stats.top_error_sources()
        ],
        first_timestamp=_format_timestamp(stats.first_timestamp),
        last_timestamp=_format_timestamp(stats.last_timestamp),
        skipped_lines=stats.skipped_lines,
    )


def render_report(stats: Statistics) -> str:
    """Serialize a report as indented UTF-8 JSON."""
    return json.dumps(build_report(stats), ensure_ascii=False, indent=2) + "\n"


def write_report(stats: Statistics, output: Path) -> None:
    """Write a report to ``output``."""
    output.write_text(render_report(stats), encoding="utf-8")


def _format_timestamp(value: datetime | None) -> str | None:
    """Format a datetime as ISO 8601, or return None when it is missing."""
    if value is None:
        return None
    return value.isoformat()
