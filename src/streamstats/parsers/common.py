"""Shared parsing helpers for CSV and JSONL event files."""

import json
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass

from loguru import logger
from pydantic import ValidationError

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import Event


@dataclass
class SkipCounter:
    """Mutable count of invalid lines ignored in skip mode."""

    count: int = 0


def iter_events[Record](
    records: Iterable[tuple[int, Record]],
    parse_record: Callable[[Record, str, int], Event],
    *,
    file_name: str,
    skip_invalid: bool,
    skipped: SkipCounter | None,
) -> Iterator[Event]:
    """Yield events from numbered records.

    A bad record stops the iterator unless ``skip_invalid`` is set, in which
    case the line is logged and counted.
    """
    for line_number, record in records:
        try:
            yield parse_record(record, file_name, line_number)
        except (InvalidEventError, InvalidTimestampError) as exc:
            _skip_or_raise(exc, skip_invalid=skip_invalid, skipped=skipped)


def event_from_mapping(
    payload: Mapping[str, object],
    file_name: str,
    line_number: int,
) -> Event:
    """Validate one CSV row."""
    return _load_event(lambda: Event.model_validate(payload), file_name, line_number)


def event_from_json_line(line: str, file_name: str, line_number: int) -> Event:
    """Validate one JSONL line."""
    payload = line.strip()
    if not payload:
        raise InvalidEventError("Line is empty", file_name, line_number)
    return _load_event(
        lambda: Event.model_validate_json(payload),
        file_name,
        line_number,
    )


def _skip_or_raise(
    exc: InvalidEventError | InvalidTimestampError,
    *,
    skip_invalid: bool,
    skipped: SkipCounter | None,
) -> None:
    """Stop on a bad line, or log it and keep reading."""
    if not skip_invalid:
        raise exc
    logger.warning("Skipped invalid line: {}", exc)
    if skipped is not None:
        skipped.count += 1


def _load_event(
    load: Callable[[], Event],
    file_name: str,
    line_number: int,
) -> Event:
    """Run a parser and attach the file location to a validation error."""
    try:
        return load()
    except InvalidTimestampError as exc:
        raise InvalidTimestampError(exc.timestamp, file_name, line_number) from exc
    except json.JSONDecodeError as exc:
        raise InvalidEventError(exc.msg, file_name, line_number) from exc
    except ValidationError as exc:
        timestamp_error = _timestamp_error(exc)
        if timestamp_error is not None:
            raise InvalidTimestampError(
                timestamp_error.timestamp,
                file_name,
                line_number,
            ) from exc
        raise InvalidEventError(
            _validation_message(exc),
            file_name,
            line_number,
        ) from exc


def _timestamp_error(error: ValidationError) -> InvalidTimestampError | None:
    """Return a timestamp error hidden inside a pydantic ValidationError."""
    cause = error.__cause__
    if isinstance(cause, InvalidTimestampError):
        return cause
    for item in error.errors():
        context = item.get("ctx")
        if not isinstance(context, dict):
            continue
        nested = context.get("error")
        if isinstance(nested, InvalidTimestampError):
            return nested
    return None


def _validation_message(error: ValidationError) -> str:
    """Format the first pydantic error as a single readable sentence."""
    details = error.errors()
    if not details:
        return "Invalid event"
    first = details[0]
    location = ".".join(str(part) for part in first.get("loc", ()))
    message = str(first.get("msg", "Invalid event"))
    if location:
        return f"{location}: {message}"
    return message
