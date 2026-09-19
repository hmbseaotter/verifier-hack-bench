"""Phase 4: the live-model scaffold, exercised with a scripted fake policy only.

No test here constructs the model-backed policy: doing so is the act that can spend money. The
only thing asserted about it is that the runner refuses to reach it.
"""
from __future__ import annotations

import ast
import json
import socket
from pathlib import Path

import pytest

from live import run_agent
from live.run_agent import Decision, ScriptedPolicy, run_episode, save
from tests.conftest import ROOT
from vhb.record import replay
from vhb.tasks import TASKS
from vhb.trajectory import Action, TrajectoryError, from_dict

TASK = TASKS["t1_pay_report"]
PAY = (Decision(actions=(Action("GET", "/reports/3"),)),
       Decision(actions=(Action("POST", "/reports/3/approve"), Action("POST", "/reports/3/pay"))),
       Decision(answer="Report 3 approved and paid."))
SENTINEL = "sk-test-SENTINEL-value-that-must-never-be-written"


def episode(decisions: tuple[Decision, ...], **limits: int) -> run_agent.Episode:
    settings = {"max_steps": 15, "max_output_tokens": 50_000, **limits}
    return run_episode(TASK, ScriptedPolicy(decisions), model="scripted-fake", **settings)


def test_a_fake_episode_is_written_unreviewed_replays_and_is_kept_out_of_the_scored_set(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-34"""
    monkeypatch.chdir(tmp_path)
    result = episode(PAY)
    out = run_agent.OUT_DIR / "t1_pay_report__scripted-fake.json"
    assert save(result, out) == 0 and out.parent.name == "live_runs"
    assert "live_runs/" in (ROOT / ".gitignore").read_text(encoding="utf-8")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["label"] == "unreviewed" and data["origin"] == "model" and len(data["steps"]) == 3
    with pytest.raises(TrajectoryError, match="'label'"):
        from_dict(data, out.as_posix())
    reviewed = {**data, "label": "honest", "origin": "human"}
    assert replay(from_dict(reviewed, "reviewed")).diverged_at is None


def test_the_policy_sees_each_result_and_refused_actions_are_errors_not_steps() -> None:
    """AC-34, continued: the runner drives the environment through reset and step only."""
    policy = ScriptedPolicy((
        Decision(actions=(Action("GET", "http://example.com/"), Action("GET", "/reports/3"))),
        Decision(answer="done")))
    result = run_episode(TASK, policy, model="scripted-fake", max_steps=15,
                         max_output_tokens=50_000)
    refused, opened = policy.seen[1]
    assert refused.is_error and "refused" in refused.text
    assert not opened.is_error and opened.text.startswith("status 200")
    assert "Report 3" in opened.text
    assert [s["action"]["path"] for s in result.data["steps"]] == ["/reports/3"]


def test_the_bench_never_imports_the_runner_and_no_test_builds_the_model_policy() -> None:
    """AC-35"""
    for source in sorted((ROOT / "src").rglob("*.py")):
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] != "live", source.name
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] != "live" for alias in node.names), source.name
    constructor = "Model" + "Policy("
    for test_file in sorted((ROOT / "tests").glob("*.py")):
        assert constructor not in test_file.read_text(encoding="utf-8"), test_file.name


def test_the_runner_stops_at_its_limits_and_says_which(tmp_path: Path) -> None:
    """AC-36"""
    finished = episode(PAY)
    assert finished.finished and finished.stop == "final answer"
    assert save(finished, tmp_path / "finished.json") == 0

    wandering = tuple(Decision(actions=(Action("GET", "/reports"),)) for _ in range(30))
    capped = episode(wandering, max_steps=4)
    assert not capped.finished and "step limit of 4" in capped.stop
    assert len(capped.data["steps"]) == 4 and capped.data["label"] == "unreviewed"
    assert save(capped, tmp_path / "capped.json") == 1
    assert json.loads((tmp_path / "capped.json").read_text(encoding="utf-8"))["stop"] == capped.stop

    broke = episode(wandering, max_output_tokens=25)
    assert not broke.finished and "output-token budget" in broke.stop


@pytest.mark.parametrize("argv,key", [
    (["--task", "t1_pay_report"], SENTINEL),             # key present, flag absent
    (["--task", "t1_pay_report", "--live"], None),       # flag present, key absent
    (["--task", "t1_pay_report"], None),
])
def test_without_the_flag_and_the_key_nothing_is_built_sent_or_written(
        argv: list[str], key: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """AC-37"""
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("the runner reached for the network or the model policy")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(run_agent, "Model" + "Policy", forbidden)
    if key is None:
        monkeypatch.delenv(run_agent.KEY_VARIABLE, raising=False)
    else:
        monkeypatch.setenv(run_agent.KEY_VARIABLE, key)
    assert run_agent.main(argv) == 2
    captured = capsys.readouterr()
    assert "refused" in captured.err and SENTINEL not in captured.out + captured.err
    assert not list(tmp_path.rglob("*")), "a refused run must write nothing"


def test_the_key_never_reaches_a_written_file(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """AC-37, continued: with the key in the environment, a whole episode leaves no trace of it."""
    monkeypatch.setenv(run_agent.KEY_VARIABLE, SENTINEL)
    save(episode(PAY), tmp_path / "run.json")
    written = (tmp_path / "run.json").read_text(encoding="utf-8")
    assert SENTINEL not in written + capsys.readouterr().out
    assert "os.environ.get(KEY_VARIABLE)" in (ROOT / "live" / "run_agent.py").read_text(
        encoding="utf-8"), "the runner may test the key's presence, and nothing else"
