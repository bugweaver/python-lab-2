"""Tests for the JSONL event parser."""

from collections.abc import Callable
from pathlib import Path

import pytest

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import Event
from streamstats.parsers import SkipCounter, parse_jsonl
from tests.fixtures import (
    BAD_TIMESTAMP_JSONL,
    EMPTY_FILE,
    INVALID_JSONL,
    MIXED_JSONL,
    UNICODE_JSONL,
    VALID_JSONL,
)


class TestParseJsonl:
    """Unit tests for ``parse_jsonl``."""

    def test_valid(self, make_file: Callable[[str, str], Path]) -> None:
        """One JSON object becomes one event."""
        file = make_file("events.jsonl", VALID_JSONL)
        results = list(parse_jsonl(file))

        assert len(results) == 1
        assert isinstance(results[0], Event)
        assert results[0].source == "api"

    def test_empty_file(self, make_file: Callable[[str, str], Path]) -> None:
        """An empty JSONL file yields no events."""
        file = make_file("empty.jsonl", EMPTY_FILE)
        assert list(parse_jsonl(file)) == []

    def test_invalid_line_stops(
        self,
        make_file: Callable[[str, str], Path],
    ) -> None:
        """A bad level stops parsing and names the file and line."""
        file = make_file("events.jsonl", INVALID_JSONL)

        with pytest.raises(InvalidEventError) as caught:
            list(parse_jsonl(file))

        assert caught.value.file_name == str(file)
        assert caught.value.line_number == 1

    def test_invalid_line_can_be_skipped(
        self,
        make_file: Callable[[str, str], Path],
    ) -> None:
        """Skip mode keeps the valid objects and counts the broken line."""
        file = make_file("events.jsonl", MIXED_JSONL)
        skipped = SkipCounter()

        results = list(parse_jsonl(file, skip_invalid=True, skipped=skipped))

        assert [event.level for event in results] == ["INFO", "ERROR"]
        assert skipped.count == 1

    def test_invalid_timestamp(
        self,
        make_file: Callable[[str, str], Path],
    ) -> None:
        """A timestamp that is not ISO 8601 raises InvalidTimestampError."""
        file = make_file("events.jsonl", BAD_TIMESTAMP_JSONL)

        with pytest.raises(InvalidTimestampError) as caught:
            list(parse_jsonl(file))

        assert caught.value.timestamp == "yesterday"

    def test_unicode(self, make_file: Callable[[str, str], Path]) -> None:
        """Unicode in the source and message is preserved."""
        file = make_file("events.jsonl", UNICODE_JSONL)
        results = list(parse_jsonl(file))

        assert results[0].source == "сервис"
        assert results[0].message == "Привет"
