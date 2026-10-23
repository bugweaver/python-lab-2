"""Event record read from a CSV or JSONL stream."""

from pydantic import BaseModel, ConfigDict

from streamstats.validation import EventLevel, Source, Timestamp


class Event(BaseModel):
    """One validated log event."""

    model_config = ConfigDict(strict=True, extra="ignore")

    timestamp: Timestamp
    level: EventLevel
    source: Source
    message: str
