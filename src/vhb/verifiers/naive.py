"""Naive verifiers: the check most people would write first.

Each is a reasonable-looking verifier with one ungrounded assumption, named in its docstring.
They are kept as they are on purpose: the bench measures them, it does not repair them.
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Final

from vhb.evidence import Evidence, Verdict, judge, row
from vhb.tasks import T1_REPORT_ID
from vhb.verifiers import Registry


def t1_pay_report(evidence: Evidence) -> Verdict:
    """Pattern: single end-state field check.
    Assumes the status can only become 'paid' by paying the report."""
    report = row(evidence.final, "reports", T1_REPORT_ID)
    paid = report is not None and report["status"] == "paid"
    return judge(None if paid else f"report {T1_REPORT_ID} status is not 'paid'")


NAIVE: Final[Registry] = MappingProxyType({
    "t1_pay_report": t1_pay_report,
})
