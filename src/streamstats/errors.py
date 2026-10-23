"""Errors raised while reading events and building a report."""


class StreamStatsError(Exception):
    """Base error for every expected streamstats failure."""


class UnsupportedFormatError(StreamStatsError):
    """Raised when the requested input format is not csv or jsonl."""

    def __init__(self, format_name: str) -> None:
        """Store the rejected format name in the error message."""
        self.format_name = format_name
        super().__init__(f"Unsupported format: {format_name}")


class InvalidEventError(StreamStatsError):
    """Raised when a line is not a valid event."""

    def __init__(self, error_message: str, file_name: str, line_number: int) -> None:
        """Remember the file and line so the CLI can point at the bad record."""
        self.error_message = error_message
        self.file_name = file_name
        self.line_number = line_number
        super().__init__(
            f"Invalid event in {file_name}, line {line_number}: {error_message}"
        )


class InvalidTimestampError(StreamStatsError):
    """Raised when a timestamp is not timezone-aware ISO 8601."""

    def __init__(
        self,
        timestamp: str,
        file_name: str | None = None,
        line_number: int | None = None,
    ) -> None:
        """Remember the raw timestamp and, when known, where it was read."""
        self.timestamp = timestamp
        self.file_name = file_name
        self.line_number = line_number
        if file_name is None or line_number is None:
            message = f"Invalid timestamp: {timestamp}"
        else:
            message = (
                f"Invalid timestamp in {file_name}, line {line_number}: {timestamp}"
            )
        super().__init__(message)


class CLIConfigError(StreamStatsError):
    """Raised when the command line does not describe a runnable analysis."""

    def __init__(self, error_message: str) -> None:
        """Store a short explanation of the configuration problem."""
        self.error_message = error_message
        super().__init__(f"Invalid CLI configuration: {error_message}")
