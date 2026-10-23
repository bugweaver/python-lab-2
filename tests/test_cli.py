"""Integration tests for the streamstats command."""

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from streamstats.__main__ import main
from tests.fixtures import MIXED_CSV, UNICODE_JSONL, VALID_CSV, VALID_JSONL


def test_help() -> None:
    """``python -m streamstats --help`` exits successfully."""
    result = subprocess.run(
        [sys.executable, "-m", "streamstats", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "analyze" in result.stdout


def test_analyze_writes_report(
    make_file: Callable[[str, str], Path],
    tmp_path: Path,
) -> None:
    """The CLI writes a JSON report for a valid JSONL file."""
    source = make_file("events.jsonl", VALID_JSONL)
    report_path = tmp_path / "report.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(source),
            "--format",
            "jsonl",
            "--output",
            str(report_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 1
    assert report["sources"]["api"] == 1
    assert report["skipped_lines"] == 0


def test_invalid_line_exits_with_code_2(
    make_file: Callable[[str, str], Path],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A broken line stops the CLI and prints the file and line number."""
    source = make_file("events.csv", MIXED_CSV)
    report_path = tmp_path / "report.json"

    with pytest.raises(SystemExit) as caught:
        main(
            [
                "analyze",
                str(source),
                "--format",
                "csv",
                "--output",
                str(report_path),
            ]
        )

    assert caught.value.code == 2
    error_output = capsys.readouterr().err
    assert str(source) in error_output
    assert "line 3" in error_output
    assert not report_path.exists()


def test_skip_invalid_records_skipped_lines(
    make_file: Callable[[str, str], Path],
    tmp_path: Path,
) -> None:
    """``--skip-invalid`` writes the report and a warning."""
    source = make_file("events.csv", MIXED_CSV)
    report_path = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(source),
            "--format",
            "csv",
            "--output",
            str(report_path),
            "--skip-invalid",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "WARNING" in result.stderr
    assert "line 3" in result.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 2
    assert report["skipped_lines"] == 1


def test_multiple_files(
    make_file: Callable[[str, str], Path],
    tmp_path: Path,
) -> None:
    """Several files are combined into one report."""
    first = make_file("one.csv", VALID_CSV)
    second = make_file(
        "two.csv",
        "timestamp,level,source,message\n"
        "2026-10-21T09:00:00Z,CRITICAL,auth,Expired\n",
    )
    report_path = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(first),
            str(second),
            "--format",
            "csv",
            "--output",
            str(report_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["total_events"] == 3
    assert report["levels"]["CRITICAL"] == 1
    assert {item["source"] for item in report["top_error_sources"]} == {
        "database",
        "auth",
    }


def test_unicode_report(
    make_file: Callable[[str, str], Path],
    tmp_path: Path,
) -> None:
    """Unicode text is stored in the report as itself, not as escapes."""
    source = make_file("events.jsonl", UNICODE_JSONL)
    report_path = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(source),
            "--format",
            "jsonl",
            "--output",
            str(report_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    raw_report = report_path.read_text(encoding="utf-8")
    assert "сервис" in raw_report
    report = json.loads(raw_report)
    assert report["sources"]["сервис"] == 1


def test_missing_input_is_a_configuration_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A missing input file is reported as a CLI configuration error."""
    with pytest.raises(SystemExit) as caught:
        main(
            [
                "analyze",
                str(tmp_path / "missing.csv"),
                "--format",
                "csv",
                "--output",
                str(tmp_path / "report.json"),
            ]
        )

    assert caught.value.code == 2
    assert "Invalid CLI configuration" in capsys.readouterr().err


def test_unsupported_format_on_the_command_line(
    make_file: Callable[[str, str], Path],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unknown --format value exits with the unsupported-format error."""
    source = make_file("events.csv", VALID_CSV)

    with pytest.raises(SystemExit) as caught:
        main(
            [
                "analyze",
                str(source),
                "--format",
                "xml",
                "--output",
                str(tmp_path / "report.json"),
            ]
        )

    assert caught.value.code == 2
    assert "Unsupported format: xml" in capsys.readouterr().err
