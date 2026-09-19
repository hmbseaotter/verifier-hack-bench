"""What a verifier is given, and what it returns.

`Evidence` deliberately has no label, class, origin, or rationale: a verifier that could see the
ground truth would be grading itself (decision D5). A `Verdict` with `passed = True` is the reward
signal; a failed verdict always says which check failed.
"""
from __future__ import annotations

from dataclasses import dataclass

from vhb.tasks import Task
from vhb.trajectory import Row, Snapshot, Step


@dataclass(frozen=True)
class Evidence:
    task: Task
    initial: Snapshot
    final: Snapshot
    steps: tuple[Step, ...]
    answer: str


@dataclass(frozen=True)
class Verdict:
    passed: bool
    reasons: tuple[str, ...] = ()


def judge(*failures: str | None) -> Verdict:
    """Pass when no check reported a failure. Each check yields a reason string or None."""
    reasons = tuple(failure for failure in failures if failure)
    return Verdict(not reasons, reasons)


def row(snapshot: Snapshot, table: str, key: int | str) -> Row | None:
    """The row whose first column (the primary key) equals `key`, or None."""
    for candidate in snapshot[table]:
        if next(iter(candidate.values())) == key:
            return candidate
    return None


def changed(evidence: Evidence, table: str) -> str | None:
    """A failure reason if `table` differs between the initial and the final snapshot."""
    if evidence.initial[table] != evidence.final[table]:
        return f"protected state changed: table '{table}'"
    return None
