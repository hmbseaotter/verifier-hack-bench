from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _run_from_repo_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI resolves `trajectories/` and `scorecard.json` from the working directory."""
    monkeypatch.chdir(ROOT)
