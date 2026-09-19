"""Record types for trajectories, and their canonical JSON form.

A trajectory is the ordered log of what an agent did: for each step, the action it sent, the
observation that came back, and a digest of the whole database after the step; then the agent's
final answer. Label, class, and rationale are authored ground truth: the scorer loads them and
never derives them, and verifiers never see them (decision D5).
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from vhb.tasks import TASKS
from vhb.taxonomy import ExploitClass

Row = Mapping[str, int | str]
Snapshot = Mapping[str, tuple[Row, ...]]


class Label(StrEnum):
    HONEST = "honest"
    EXPLOIT = "exploit"


class Origin(StrEnum):
    AUTHORED = "authored"
    PROBE = "probe"
    HUMAN = "human"


class TrajectoryError(ValueError):
    """A trajectory file is invalid. The message names the file and the field."""


@dataclass(frozen=True)
class Action:
    method: str
    path: str
    form: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Observation:
    status: int
    location: str
    body_sha256: str


@dataclass(frozen=True)
class Step:
    action: Action
    observation: Observation
    state_digest: str


@dataclass(frozen=True)
class Meta:
    """The authored part of a trajectory: everything except what the recorder stamps."""
    task: str
    label: Label
    origin: Origin
    exploit_class: ExploitClass | None = None
    rationale: str = ""
    atypical: bool = False


@dataclass(frozen=True)
class Trajectory:
    meta: Meta
    steps: tuple[Step, ...]
    answer: str


def canonical_json(data: object) -> str:
    """The one JSON form this repository writes: byte-identical across runs and platforms."""
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def to_dict(trajectory: Trajectory) -> dict[str, Any]:
    meta = trajectory.meta
    return {
        "task": meta.task, "label": meta.label.value, "origin": meta.origin.value,
        "exploit_class": meta.exploit_class.value if meta.exploit_class else None,
        "rationale": meta.rationale, "atypical": meta.atypical, "answer": trajectory.answer,
        "steps": [{
            "action": {"method": s.action.method, "path": s.action.path,
                       "form": dict(s.action.form)},
            "observation": {"status": s.observation.status, "location": s.observation.location,
                            "body_sha256": s.observation.body_sha256},
            "state_digest": s.state_digest,
        } for s in trajectory.steps],
    }


def _field(data: Mapping[str, Any], key: str, kind: type, source: str) -> Any:
    if key not in data or not isinstance(data[key], kind):
        raise TrajectoryError(f"{source}: field '{key}': missing or not {kind.__name__}")
    return data[key]


def meta_from_dict(data: Mapping[str, Any], source: str) -> Meta:
    """Parse and validate the authored fields. Every rejection names the file and the field."""
    task = _field(data, "task", str, source)
    if task not in TASKS:
        raise TrajectoryError(f"{source}: field 'task': unknown task '{task}'")
    try:
        label = Label(_field(data, "label", str, source))
    except ValueError as error:
        raise TrajectoryError(f"{source}: field 'label': {error}") from None
    try:
        origin = Origin(_field(data, "origin", str, source))
    except ValueError as error:
        raise TrajectoryError(f"{source}: field 'origin': {error}") from None
    raw_class = data.get("exploit_class")
    rationale = _field(data, "rationale", str, source)
    atypical = _field(data, "atypical", bool, source)
    if label is Label.HONEST:
        if raw_class is not None:
            raise TrajectoryError(f"{source}: field 'exploit_class': honest trajectory has a class")
        return Meta(task, label, origin, None, rationale, atypical)
    try:
        exploit_class = ExploitClass(str(raw_class))
    except ValueError:
        raise TrajectoryError(
            f"{source}: field 'exploit_class': exploit needs exactly one class from the taxonomy, "
            f"got {raw_class!r}") from None
    if not rationale.strip():
        raise TrajectoryError(f"{source}: field 'rationale': exploit needs a rationale")
    if atypical:
        raise TrajectoryError(f"{source}: field 'atypical': only honest trajectories are atypical")
    if exploit_class is ExploitClass.INFEASIBLE_PASS and TASKS[task].feasible:
        raise TrajectoryError(
            f"{source}: field 'exploit_class': INFEASIBLE_PASS on feasible task '{task}'")
    return Meta(task, label, origin, exploit_class, rationale, atypical)


def action_from_dict(data: Mapping[str, Any], source: str) -> Action:
    form = _field(data, "form", dict, source) if "form" in data else {}
    return Action(_field(data, "method", str, source), _field(data, "path", str, source),
                  tuple(sorted((str(k), str(v)) for k, v in form.items())))


def from_dict(data: Mapping[str, Any], source: str) -> Trajectory:
    steps = []
    for raw in _field(data, "steps", list, source):
        seen = _field(raw, "observation", dict, source)
        steps.append(Step(
            action_from_dict(_field(raw, "action", dict, source), source),
            Observation(_field(seen, "status", int, source), _field(seen, "location", str, source),
                        _field(seen, "body_sha256", str, source)),
            _field(raw, "state_digest", str, source)))
    return Trajectory(meta_from_dict(data, source), tuple(steps),
                      _field(data, "answer", str, source))


def read_trajectory(path: Path) -> Trajectory:
    return from_dict(json.loads(path.read_text(encoding="utf-8")), path.as_posix())


def write_trajectory(path: Path, trajectory: Trajectory) -> None:
    write_text(path, canonical_json(to_dict(trajectory)))
