"""Tests for the CSV event parser."""

from collections.abc import Callable
from pathlib import Path

import pytest

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import Event
from streamstats.parsers import SkipCounter, parse_csv
from tests.fixtures import (
    BAD_TIMESTAMP_CSV,
    EMPTY_FILE,
    INVALID_CSV,
    MIXED_CSV,
    UNICODE_CSV,
    VALID_CSV,
)


class TestParseCsv:
    """Unit tests for ``parse_csv``."""

    def test_valid(self, make_file: Callable[[str, str], Path]) -> None:
        """A header and two data rows become two events."""
        file = make_file("events.csv", VALID_CSV)
        results = list(parse_csv(file))

        assert len(results) == 2
        assert all(isinstance(item, Event) for item in results)
        assert results[1].level == "ERROR"
        assert results[1].source == "database"

    def test_empty_file(self, make_file: Callable[[str, str], Path]) -> None:
        """An empty CSV yields no events."""
        file = make_file("empty.csv", EMPTY_FILE)
        assert list(parse_csv(file)) == []

    def test_invalid_line_stops(
        self,
        make_file: Callable[[str, str], Path],
    ) -> None:
        """A bad level stops parsing and names the file and line."""
        file = make_file("events.csv", INVALID_CSV)

        with pytest.raises(InvalidEventError) as caught:
            list(parse_csv(file))

        assert caught.value.file_name == str(file)
        assert caught.value.line_number == 2

    def test_invalid_line_can_be_skipped(
        self,
        make_file: Callable[[str, str], Path],
    ) -> None:
        """Skip mode keeps the valid rows and counts the broken one."""
        file = make_file("events.csv", MIXED_CSV)
        skipped = SkipCounter()

        results = list(parse_csv(file, skip_invalid=True, skipped=skipped))

        assert [event.source for event in results] == ["api", "auth"]
        assert skipped.count == 1

    def test_invalid_timestamp(
        self,
        make_file: Callable[[str, str], Path],
    ) -> None:
        """A timestamp that is not ISO 8601 raises InvalidTimestampError."""
        file = make_file("events.csv", BAD_TIMESTAMP_CSV)

        with pytest.raises(InvalidTimestampError) as caught:
            list(parse_csv(file))

        assert caught.value.line_number == 2
        assert caught.value.timestamp == "not-a-timestamp"

    def test_unicode(self, make_file: Callable[[str, str], Path]) -> None:
        """Unicode in the source and message is preserved."""
        file = make_file("events.csv", UNICODE_CSV)
        results = list(parse_csv(file))

        assert results[0].source == "сервис"
        assert results[0].message == "Привет"
