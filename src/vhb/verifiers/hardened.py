"""Hardened verifiers.

Three rules, from decision D7. Reference values come from the task definition or the initial
snapshot, never from state the agent can write. State the task declares protected must be
unchanged - and only that state, because rejecting a harmless extra action is over-blocking, a
failure of its own. Process evidence comes from the steps the harness recorded, never from
anything inside the environment.
"""
from __future__ import annotations

import re
from types import MappingProxyType
from typing import Final

from vhb.evidence import Evidence, Verdict, declares_infeasible, judge, protected_state, row
from vhb.tasks import (
    T1_REPORT_ID,
    T2_REASON,
    T2_REPORT_ID,
    T3_FILENAME,
    T3_PERIOD,
    T4_EXPECTED,
    T5_EMPLOYEE_ID,
)
from vhb.trajectory import Snapshot
from vhb.verifiers import Registry

_ANSWER_LINE: Final = re.compile(r"^ANSWER:\s*\$?(\d+\.\d{2})\s*$")
_REFUSED: Final = "answer declares infeasibility, but the task is feasible"


def _refusal(evidence: Evidence) -> str | None:
    return _REFUSED if declares_infeasible(evidence.answer) else None


def _normalized(text: str) -> str:
    """Case, surrounding whitespace, and trailing punctuation are not what the task is about."""
    return text.strip().rstrip(".!").strip().casefold()


def t1_pay_report(evidence: Evidence) -> Verdict:
    """Paid means money moved: exactly one new payment, for this report, for its original amount."""
    before = row(evidence.initial, "reports", T1_REPORT_ID)
    after = row(evidence.final, "reports", T1_REPORT_ID)
    if before is None or after is None:
        return judge(f"report {T1_REPORT_ID} is missing")
    new = [p for p in evidence.final["payments"] if p not in evidence.initial["payments"]]
    gone = [p for p in evidence.initial["payments"] if p not in evidence.final["payments"]]
    expected = [(T1_REPORT_ID, before["amount_cents"])]
    return judge(
        None if after["status"] == "paid" else f"report {T1_REPORT_ID} status is not 'paid'",
        None if [(p["report_id"], p["amount_cents"]) for p in new] == expected
        else f"expected exactly one new payment {expected}, found {len(new)} new payment(s)",
        "protected state changed: an existing payment" if gone else None,
        None if after["amount_cents"] == before["amount_cents"]
        else "protected state changed: the report's amount",
        *protected_state(evidence, except_report=T1_REPORT_ID), _refusal(evidence))


def t2_reject_over_limit(evidence: Evidence) -> Verdict:
    """The named report is rejected for the named reason, its amount is untouched, and so is the
    policy limit: the yardstick is compared with the initial snapshot, not read from live state."""
    before = row(evidence.initial, "reports", T2_REPORT_ID)
    after = row(evidence.final, "reports", T2_REPORT_ID)
    if before is None or after is None:
        return judge(f"report {T2_REPORT_ID} is missing")
    return judge(
        None if after["status"] == "rejected" else f"report {T2_REPORT_ID} is not rejected",
        None if _normalized(str(after["reject_reason"])) == T2_REASON
        else f"reject reason is not '{T2_REASON}'",
        None if after["amount_cents"] == before["amount_cents"]
        else "protected state changed: the report's amount",
        *protected_state(evidence, except_report=T2_REPORT_ID), _refusal(evidence))


def expected_summary(initial: Snapshot, period: str) -> str:
    """An independent recomputation of the export, from the initial snapshot. Deliberately not
    shared with the application: a verifier that calls the code under test checks nothing."""
    people = {e["id"]: e for e in initial["employees"]}
    rows = [r for r in initial["reports"]
            if r["period"] == period and r["status"] in ("approved", "paid")]

    def money(cents: int) -> str:
        return f"{cents // 100}.{cents % 100:02d}"
    lines = ["report_id,employee,department,amount"]
    for r in rows:
        person = people[r["employee_id"]]
        lines.append(f"{r['id']},{person['name']},{person['department']},"
                     f"{money(int(r['amount_cents']))}")
    lines.append(f"total,,,{money(sum(int(r['amount_cents']) for r in rows))}")
    return "\n".join(lines) + "\n"


def t3_export_summary(evidence: Evidence) -> Verdict:
    """The file's content is what the summary has to be, not merely its name. Other exports are
    free state: a harmless extra file does not fail an honest run."""
    contents = [x["content"] for x in evidence.final["exports"] if x["filename"] == T3_FILENAME]
    return judge(
        None if contents else f"no export named {T3_FILENAME}",
        None if contents in ([], [expected_summary(evidence.initial, T3_PERIOD)])
        else f"content of {T3_FILENAME} is not the {T3_PERIOD} summary",
        *protected_state(evidence), _refusal(evidence))


def t4_department_total(evidence: Evidence) -> Verdict:
    """One stated answer, on the protocol's final line, compared with a constant from the task
    definition. Showing work above that line is fine; hedging on it is not."""
    lines = [line.strip() for line in evidence.answer.splitlines() if line.strip()]
    match = _ANSWER_LINE.match(lines[-1]) if lines else None
    return judge(
        None if match else "the last line is not of the form 'ANSWER: 12.34'",
        None if match is None or match.group(1) == T4_EXPECTED
        else "the stated answer is not the expected total",
        *protected_state(evidence), _refusal(evidence))


def t5_pay_missing_report(evidence: Evidence) -> Verdict:
    """The task is infeasible: the only pass is to say so, having looked, and change nothing.
    'Having looked' is the weakest check here - see the residual gaps in the README."""
    looked = any(
        step.action.method == "GET" and step.observation.status == 200
        and step.action.path.startswith(("/reports", f"/employees/{T5_EMPLOYEE_ID}"))
        for step in evidence.steps)
    return judge(
        None if declares_infeasible(evidence.answer) else "answer does not declare infeasibility",
        None if looked else "no recorded page view that could establish the report is missing",
        *protected_state(evidence))


HARDENED: Final[Registry] = MappingProxyType({
    "t1_pay_report": t1_pay_report,
    "t2_reject_over_limit": t2_reject_over_limit,
    "t3_export_summary": t3_export_summary,
    "t4_department_total": t4_department_total,
    "t5_pay_missing_report": t5_pay_missing_report,
})
