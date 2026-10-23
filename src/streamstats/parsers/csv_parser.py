"""Line-oriented parser for CSV event files."""

import csv
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

from streamstats.models import Event
from streamstats.parsers.common import (
    SkipCounter,
    event_from_mapping,
    iter_events,
)


def parse_csv(
    path: Path,
    *,
    skip_invalid: bool = False,
    skipped: SkipCounter | None = None,
) -> Iterator[Event]:
    """Yield events from a CSV file that has a header row."""
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        yield from iter_events(
            _numbered_rows(reader),
            event_from_mapping,
            file_name=str(path),
            skip_invalid=skip_invalid,
            skipped=skipped,
        )


def _numbered_rows(
    reader: csv.DictReader[Any],
) -> Iterator[tuple[int, dict[str, object]]]:
    """Pair each CSV record with the line number it was read from."""
    for row in reader:
        yield reader.line_num, _row_payload(row)


def _row_payload(row: Mapping[Any, Any]) -> dict[str, object]:
    """Drop the unnamed rest key and keep named CSV fields."""
    return {str(key): value for key, value in row.items() if key is not None}
