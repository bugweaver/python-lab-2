"""Field validators used by the event model."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator

from streamstats.enums import Level
from streamstats.errors import InvalidTimestampError


def _validate_source(value: str) -> str:
    """Reject a source that is empty or made only of whitespace."""
    if not value.strip():
        raise ValueError("Source must not be empty")
    return value


Source = Annotated[str, AfterValidator(_validate_source)]


def _parse_level(value: object) -> Level:
    """Convert a level name into the Level enum."""
    if isinstance(value, Level):
        return value
    if not isinstance(value, str):
        raise ValueError("Level must be a string")
    try:
        return Level(value)
    except ValueError as err:
        raise ValueError("Unknown event level") from err


EventLevel = Annotated[Level, BeforeValidator(_parse_level)]


def _parse_timestamp(value: object) -> datetime:
    """Parse a timezone-aware ISO 8601 timestamp and convert it to UTC."""
    if isinstance(value, datetime):
        parsed = value
        raw = value.isoformat()
    elif isinstance(value, str):
        raw = value
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as err:
            raise InvalidTimestampError(value) from err
    else:
        raise InvalidTimestampError(str(value))

    if parsed.tzinfo is None:
        raise InvalidTimestampError(raw)
    return parsed.astimezone(UTC)


Timestamp = Annotated[datetime, BeforeValidator(_parse_timestamp)]
