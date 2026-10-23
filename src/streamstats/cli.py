"""Command-line parsing and process exit codes for streamstats."""

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn, cast

from loguru import logger

from streamstats.analysis import analyze_files
from streamstats.constants import EXIT_CODE_ERROR
from streamstats.errors import CLIConfigError, StreamStatsError
from streamstats.report import render_report, write_report


@dataclass(frozen=True, slots=True)
class _AnalyzeCommand:
    """Typed arguments of the analyze command."""

    inputs: list[Path]
    input_format: str
    output: Path | None
    skip_invalid: bool


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments, analyze the input files, and write the report."""
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(None if argv is None else list(argv))
    try:
        _execute(_command(args))
    except UnicodeDecodeError as exc:
        _fail(f"Input is not valid UTF-8: {exc.reason}")
    except OSError as exc:
        _fail(f"Cannot read input: {exc}")
    except StreamStatsError as exc:
        _fail(str(exc))


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser used by ``python -m streamstats``."""
    parser = argparse.ArgumentParser(
        prog="streamstats",
        description="Build a statistics report from CSV and JSONL event streams.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze event files and write a JSON report.",
    )
    analyze.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="One or more input files.",
    )
    analyze.add_argument(
        "--format",
        required=True,
        dest="input_format",
        help="Input format for every file: csv or jsonl.",
    )
    analyze.add_argument(
        "--output",
        type=Path,
        help="JSON report path. The report is printed when this is omitted.",
    )
    analyze.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Skip invalid lines, log a warning, and record how many were skipped.",
    )
    return parser


def configure_logging() -> None:
    """Send warnings and errors to stderr without a stack trace."""
    logger.remove()
    logger.add(sys.stderr, format="{level} | {message}", level="WARNING")


def _execute(command: _AnalyzeCommand) -> None:
    """Run a validated analyze command."""
    stats = analyze_files(
        command.inputs,
        command.input_format,
        skip_invalid=command.skip_invalid,
    )
    if command.output is None:
        sys.stdout.write(render_report(stats))
        return
    write_report(stats, command.output)


def _command(args: argparse.Namespace) -> _AnalyzeCommand:
    """Copy argparse values into a typed command."""
    if args.command != "analyze":
        raise CLIConfigError(f"Unknown command: {args.command}")
    return _AnalyzeCommand(
        inputs=_input_paths(args.inputs),
        input_format=_input_format(args.input_format),
        output=_output_path(args.output),
        skip_invalid=bool(args.skip_invalid),
    )


def _input_paths(values: object) -> list[Path]:
    """Check that every CLI input is an existing file."""
    if not isinstance(values, list):
        raise CLIConfigError("Input files must be a list of paths")
    paths = [_as_path(item) for item in cast(list[object], values)]
    for path in paths:
        if not path.is_file():
            raise CLIConfigError(f"Input file does not exist: {path}")
    return paths


def _output_path(value: object) -> Path | None:
    """Check that the report path is a file inside an existing directory."""
    if value is None:
        return None
    path = _as_path(value)
    if path.is_dir():
        raise CLIConfigError(f"Output path is a directory: {path}")
    if not path.parent.exists():
        raise CLIConfigError(f"Output directory does not exist: {path.parent}")
    return path


def _as_path(value: object) -> Path:
    """Convert one CLI value into a path."""
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    raise CLIConfigError(f"Expected a file path, got {type(value).__name__}")


def _input_format(value: object) -> str:
    """Return the format name passed on the command line."""
    if isinstance(value, str) and value:
        return value
    raise CLIConfigError("Input format must be a non-empty string")


def _fail(message: str) -> NoReturn:
    """Log an expected failure and stop the process with the error code."""
    logger.error("{}", message)
    sys.exit(EXIT_CODE_ERROR)
