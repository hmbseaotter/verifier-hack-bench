"""Phase 0: the environment is deterministic, and a recording replays exactly."""
from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from flask import Flask

from tests.conftest import ROOT
from vhb import evidence, record, recordmode, tasks, taxonomy, trajectory
from vhb.env import SEED_DIGEST, ActionRefused, Environment
from vhb.trajectory import Action, Label, Meta, Origin

T1_HONEST = (Action("GET", "/reports/3"), Action("POST", "/reports/3/approve"),
             Action("POST", "/reports/3/pay"))
META = Meta("t1_pay_report", Label.HONEST, Origin.AUTHORED)


def contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(contains_float(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(contains_float(v) for v in value)
    return False


def test_reset_always_lands_on_the_published_seed_digest() -> None:
    """AC-01"""
    env = Environment()
    assert env.state_digest() == SEED_DIGEST
    env.step(Action("POST", "/reports/3/approve"))
    assert env.state_digest() != SEED_DIGEST
    env.reset()
    assert env.state_digest() == SEED_DIGEST
    assert Environment().state_digest() == SEED_DIGEST


def test_a_recording_replays_with_no_divergence() -> None:
    """AC-02"""
    recorded = record.record(META, T1_HONEST, "Report 3 approved and paid.")
    assert [step.observation.status for step in recorded.steps] == [200, 302, 302]
    result = record.replay(recorded)
    assert result.diverged_at is None
    assert result.evidence is not None and result.evidence.answer == recorded.answer


def test_recording_twice_is_byte_identical_and_canonical(tmp_path: Path) -> None:
    """AC-03"""
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    trajectory.write_trajectory(first, record.record(META, T1_HONEST, "done"))
    trajectory.write_trajectory(second, record.record(META, T1_HONEST, "done"))
    raw = first.read_bytes()
    assert raw == second.read_bytes()
    assert b"\r" not in raw and raw.endswith(b"}\n") and not raw.endswith(b"\n\n")
    assert raw.decode("ascii") == trajectory.canonical_json(json.loads(raw))


def test_record_mode_captures_a_session_and_stamps_it_through_the_recorder(tmp_path: Path) -> None:
    """AC-04"""
    out = tmp_path / "human.json"
    app = recordmode.recording_app(Meta("t1_pay_report", Label.HONEST, Origin.HUMAN), out)
    browser = app.test_client()
    browser.get("/reports?status=submitted")
    browser.get("/favicon.ico")
    browser.post("/reports/3/approve")
    browser.post("/reports/3/pay")
    assert browser.get("/__record/finish").status_code == 200
    assert browser.post("/__record/finish", data={"answer": "paid"}).status_code == 200

    saved = trajectory.read_trajectory(out)
    assert [(s.action.method, s.action.path) for s in saved.steps] == [
        ("GET", "/reports?status=submitted"), ("POST", "/reports/3/approve"),
        ("POST", "/reports/3/pay")]
    assert saved.meta.origin is Origin.HUMAN and saved.answer == "paid"
    assert record.replay(saved).diverged_at is None
    # The live session's state was discarded: the next recording starts from the seed.
    assert b"submitted" in browser.get("/reports/3").get_data()


def test_replay_reports_the_first_divergent_step() -> None:
    """AC-15"""
    recorded = record.record(META, T1_HONEST, "done")
    steps = list(recorded.steps)
    steps[1] = dataclasses.replace(steps[1], state_digest="0" * 64)
    tampered = dataclasses.replace(recorded, steps=tuple(steps))
    result = record.replay(tampered)
    assert result.diverged_at == 1 and result.evidence is None


@pytest.mark.parametrize("action", [
    Action("GET", "http://example.com/"), Action("GET", "//example.com/x"),
    Action("GET", "reports"), Action("GET", ""), Action("DELETE", "/reports/3"),
])
def test_non_local_actions_are_refused_without_executing(action: Action) -> None:
    """AC-16"""
    env = Environment()
    with pytest.raises(ActionRefused):
        env.step(action)
    assert env.state_digest() == SEED_DIGEST


def test_no_float_in_snapshots_or_trajectories() -> None:
    """AC-17 (the scorecard half of this criterion is checked in the P2 tests)"""
    env = Environment()
    env.step(Action("POST", "/reports/new", (
        ("amount", "19.99"), ("employee_id", "4"), ("period", "2026-03"), ("title", "Pens"))))
    snapshot = {table: [dict(row) for row in rows] for table, rows in env.snapshot().items()}
    assert snapshot["reports"][-1]["amount_cents"] == 1999
    assert not contains_float(snapshot)
    assert not contains_float(trajectory.to_dict(record.record(META, T1_HONEST, "done")))


def test_source_passes_strict_type_checking_and_records_are_frozen() -> None:
    """AC-23"""
    for module in (trajectory, evidence, record, tasks, taxonomy):
        for value in vars(module).values():
            if dataclasses.is_dataclass(value) and isinstance(value, type):
                params: Any = value.__dataclass_params__
                assert params.frozen, f"{value.__name__} is not frozen"
    result = subprocess.run(
        [sys.executable, "-m", "mypy"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_serve_binds_loopback_only_and_handles_one_request_at_a_time(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-24"""
    seen: dict[str, Any] = {}
    monkeypatch.setattr(Flask, "run", lambda self, **kwargs: seen.update(kwargs))
    recordmode.serve(META, tmp_path / "out.json", 5000)
    assert seen["host"] == "127.0.0.1" and seen["threaded"] is False
