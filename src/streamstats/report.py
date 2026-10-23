"""JSON and CSV reports built from collected event statistics."""

import csv
import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import TypedDict

from streamstats.analysis import Statistics
from streamstats.enums import Level
from streamstats.errors import UnsupportedFormatError


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
    """Convert counters into one report structure shared by every output format."""
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


def render_report(stats: Statistics, report_format: str = "json") -> str:
    """Serialize one already collected report as JSON or CSV.

    Both formats render the same ``build_report`` result, so the events are
    not read or counted again.
    """
    return render_built_report(build_report(stats), report_format)


def render_built_report(report: Report, report_format: str) -> str:
    """Serialize a report structure without touching the original events."""
    if report_format == "json":
        return json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if report_format == "csv":
        return _render_csv(report)
    raise UnsupportedFormatError(report_format)


def write_report(
    stats: Statistics,
    output: Path,
    report_format: str = "json",
) -> None:
    """Write a report to ``output`` in ``report_format``."""
    output.write_text(
        render_report(stats, report_format),
        encoding="utf-8",
    )


def _render_csv(report: Report) -> str:
    """Write the shared report structure as section, name, and value rows."""
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(("section", "name", "value"))
    writer.writerow(("summary", "total_events", report["total_events"]))
    writer.writerow(("summary", "skipped_lines", report["skipped_lines"]))
    writer.writerow(("summary", "first_timestamp", report["first_timestamp"] or ""))
    writer.writerow(("summary", "last_timestamp", report["last_timestamp"] or ""))
    for level, count in report["levels"].items():
        writer.writerow(("level", level, count))
    for source, count in report["sources"].items():
        writer.writerow(("source", source, count))
    for entry in report["top_error_sources"]:
        writer.writerow(("top_error_source", entry["source"], entry["count"]))
    return buffer.getvalue()


def _format_timestamp(value: datetime | None) -> str | None:
    """Format a datetime as ISO 8601, or return None when it is missing."""
    if value is None:
        return None
    return value.isoformat()
