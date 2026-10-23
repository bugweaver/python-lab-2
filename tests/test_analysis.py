"""Tests for merged statistics."""

from collections.abc import Callable
from pathlib import Path

import pytest

from streamstats.analysis import analyze_files
from streamstats.errors import InvalidEventError, UnsupportedFormatError
from streamstats.report import build_report
from tests.fixtures import MIXED_JSONL, UNICODE_JSONL, VALID_CSV, VALID_JSONL


def test_empty_file(make_file: Callable[[str, str], Path]) -> None:
    """An empty input produces an empty report."""
    file = make_file("empty.jsonl", "")
    report = build_report(analyze_files([file], "jsonl"))

    assert report["total_events"] == 0
    assert report["first_timestamp"] is None
    assert report["last_timestamp"] is None
    assert report["skipped_lines"] == 0
    assert report["levels"]["ERROR"] == 0


def test_invalid_line_stops(make_file: Callable[[str, str], Path]) -> None:
    """The default mode stops at the first broken line."""
    file = make_file("events.jsonl", MIXED_JSONL)

    with pytest.raises(InvalidEventError) as caught:
        analyze_files([file], "jsonl")

    assert caught.value.line_number == 2


def test_invalid_line_is_skipped(make_file: Callable[[str, str], Path]) -> None:
    """Skip mode counts the broken line and keeps the valid events."""
    file = make_file("events.jsonl", MIXED_JSONL)
    stats = analyze_files([file], "jsonl", skip_invalid=True)

    assert stats.total_events == 2
    assert stats.skipped_lines == 1
    assert stats.levels["INFO"] == 1
    assert stats.levels["ERROR"] == 1
    assert stats.error_sources["database"] == 1


def test_multiple_files(make_file: Callable[[str, str], Path]) -> None:
    """Counters and timestamps are merged across files."""
    first = make_file("one.csv", VALID_CSV)
    second = make_file(
        "two.csv",
        "timestamp,level,source,message\n"
        "2026-10-19T09:00:00Z,CRITICAL,auth,Expired\n"
        "2026-10-21T09:00:00Z,DEBUG,api,Done\n",
    )

    stats = analyze_files([first, second], "csv")

    assert stats.total_events == 4
    assert stats.sources["api"] == 2
    assert stats.levels["CRITICAL"] == 1
    assert stats.first_timestamp is not None
    assert stats.last_timestamp is not None
    assert stats.first_timestamp.isoformat().startswith("2026-10-19T09:00:00")
    assert stats.last_timestamp.isoformat().startswith("2026-10-21T09:00:00")


def test_top_error_sources_ignore_other_levels(
    make_file: Callable[[str, str], Path],
) -> None:
    """Only ERROR and CRITICAL events compete for the top five sources."""
    lines = ["timestamp,level,source,message"]
    counts = (6, 5, 4, 3, 2, 1)
    for index, count in enumerate(counts, start=1):
        for copy in range(count):
            lines.append(
                f"2026-10-20T10:{index:02d}:{copy:02d}Z,ERROR,source-{index},failed"
            )
    lines.append("2026-10-20T11:00:00Z,INFO,noisy,ok")
    file = make_file("errors.csv", "\n".join(lines) + "\n")

    report = build_report(analyze_files([file], "csv"))
    ranking = report["top_error_sources"]

    assert [(item["source"], item["count"]) for item in ranking] == [
        ("source-1", 6),
        ("source-2", 5),
        ("source-3", 4),
        ("source-4", 3),
        ("source-5", 2),
    ]


def test_unicode(make_file: Callable[[str, str], Path]) -> None:
    """Unicode source names survive analysis and the JSON report."""
    file = make_file("events.jsonl", UNICODE_JSONL)
    report = build_report(analyze_files([file], "jsonl"))

    assert report["sources"]["сервис"] == 1
    assert report["levels"]["WARNING"] == 1


def test_unsupported_format(make_file: Callable[[str, str], Path]) -> None:
    """An unknown format is rejected before any file is read."""
    file = make_file("events.csv", VALID_CSV)

    with pytest.raises(UnsupportedFormatError):
        analyze_files([file], "xml")


def test_jsonl_and_counts(make_file: Callable[[str, str], Path]) -> None:
    """A valid JSONL file fills the level and source counters."""
    file = make_file("events.jsonl", VALID_JSONL)
    stats = analyze_files([file], "jsonl")

    assert stats.total_events == 1
    assert stats.sources["api"] == 1
    assert stats.levels["INFO"] == 1
