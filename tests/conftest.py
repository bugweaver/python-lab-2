from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def make_file(tmp_path: Path) -> Callable[[str, str], Path]:
    def _make_file(name: str, content: str) -> Path:
        file = tmp_path / name
        file.write_text(content, encoding="utf-8")
        return file

    return _make_file
