"""Line-oriented parser for JSONL event files."""

from collections.abc import Iterator
from pathlib import Path

from streamstats.models import Event
from streamstats.parsers.common import (
    SkipCounter,
    event_from_json_line,
    iter_events,
)


def parse_jsonl(
    path: Path,
    *,
    skip_invalid: bool = False,
    skipped: SkipCounter | None = None,
) -> Iterator[Event]:
    """Yield events from a JSONL file, one JSON object per line."""
    with path.open(encoding="utf-8") as file:
        yield from iter_events(
            enumerate(file, start=1),
            event_from_json_line,
            file_name=str(path),
            skip_invalid=skip_invalid,
            skipped=skipped,
        )
