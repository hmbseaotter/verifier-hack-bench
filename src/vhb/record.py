"""Recorder and replayer.

Recording executes an action list on a freshly reset environment and stamps every step with what
came back and with a digest of the whole database. Replaying does the same again and compares:
if every stamp matches, the trajectory is deterministic, and the evidence handed to the verifiers
is exactly what the recording saw.
"""
from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from vhb.env import Environment
from vhb.evidence import Evidence
from vhb.tasks import TASKS
from vhb.trajectory import (
    Action,
    Meta,
    Step,
    Trajectory,
    action_from_dict,
    meta_from_dict,
    write_trajectory,
)


@dataclass(frozen=True)
class Replay:
    """`diverged_at` is the index of the first step that did not match, or None."""
    diverged_at: int | None
    evidence: Evidence | None


def record(meta: Meta, actions: Sequence[Action], answer: str) -> Trajectory:
    env = Environment()
    steps = []
    for action in actions:
        observation, _body = env.step(action)
        steps.append(Step(action, observation, env.state_digest()))
    return Trajectory(meta, tuple(steps), answer)


def replay(trajectory: Trajectory) -> Replay:
    env = Environment()
    initial = env.snapshot()
    for index, step in enumerate(trajectory.steps):
        observation, _body = env.step(step.action)
        if observation != step.observation or env.state_digest() != step.state_digest:
            return Replay(index, None)
    task = TASKS[trajectory.meta.task]
    return Replay(None, Evidence(
        task, initial, env.snapshot(), trajectory.steps, trajectory.answer))


def stamp_file(path: Path) -> Trajectory:
    """(Re)record a trajectory file in place: keep its authored fields and actions, replace
    every observation and digest with what the environment produces now."""
    data = json.loads(path.read_text(encoding="utf-8"))
    source = path.as_posix()
    actions = [action_from_dict(step["action"], source) for step in data.get("steps", [])]
    trajectory = record(meta_from_dict(data, source), actions, str(data.get("answer", "")))
    write_trajectory(path, trajectory)
    return trajectory
