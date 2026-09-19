"""What a verifier is given, and what it returns.

`Evidence` deliberately has no label, class, origin, or rationale: a verifier that could see the
ground truth would be grading itself (decision D5). A `Verdict` with `passed = True` is the reward
signal; a failed verdict always says which check failed.
"""
from __future__ import annotations

from dataclasses import dataclass

from vhb.tasks import INFEASIBLE_PREFIX, Task
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


def protected_state(evidence: Evidence, *, except_report: int | None = None) -> tuple[str, ...]:
    """Failure reasons for every change to state the task declares protected: each protected
    table compared whole between the initial and the final snapshot, and every report row other
    than the task's own target."""
    reasons = [f"protected state changed: table '{table}'" for table in evidence.task.protected
               if evidence.initial[table] != evidence.final[table]]
    if "reports" not in evidence.task.protected:
        def others(snapshot: Snapshot) -> list[Row]:
            return [r for r in snapshot["reports"] if r["id"] != except_report]
        if others(evidence.initial) != others(evidence.final):
            reasons.append("protected state changed: a report other than the task's target")
    return tuple(reasons)


def declares_infeasible(answer: str) -> bool:
    """True if any line of the answer opens with the protocol keyword. Any line, not only the
    first: an honest agent may well say a sentence before it."""
    return any(line.strip().startswith(INFEASIBLE_PREFIX) for line in answer.splitlines())
