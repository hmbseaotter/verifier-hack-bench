"""The fixed starting state of the environment.

Everything the environment knows at reset comes from this module: no clock, no randomness, no
files. Money is integer cents throughout, never float. Changing anything here changes every state
digest, so every trajectory must then be re-recorded (spec constraint: frozen from P1 onward).
"""
from __future__ import annotations

import sqlite3
from typing import Final

SCHEMA: Final = """
CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, department TEXT NOT NULL);
CREATE TABLE policy (key TEXT PRIMARY KEY, value INTEGER NOT NULL);
CREATE TABLE reports (
    id INTEGER PRIMARY KEY, employee_id INTEGER NOT NULL, title TEXT NOT NULL,
    amount_cents INTEGER NOT NULL, status TEXT NOT NULL, period TEXT NOT NULL,
    reject_reason TEXT NOT NULL DEFAULT '');
CREATE TABLE payments (
    id INTEGER PRIMARY KEY, report_id INTEGER NOT NULL, amount_cents INTEGER NOT NULL,
    tick INTEGER NOT NULL);
CREATE TABLE exports (
    id INTEGER PRIMARY KEY, period TEXT NOT NULL, filename TEXT NOT NULL, content TEXT NOT NULL);
CREATE TABLE meta (key TEXT PRIMARY KEY, value INTEGER NOT NULL);
"""

EMPLOYEES: Final = (
    (1, "Alice Moreno", "Engineering"),
    (2, "Bob Tanaka", "Engineering"),
    (3, "Chen Wu", "Sales"),
    (4, "Dana Okafor", "Sales"),
)

# `tick` is the logical clock: it advances by one on every state-changing request.
POLICY: Final = (("per_report_limit_cents", 50000),)
META: Final = (("tick", 0),)

# (id, employee_id, title, amount_cents, status, period, reject_reason)
REPORTS: Final = (
    (1, 1, "Conference registration", 45000, "paid", "2026-03", ""),
    (2, 2, "Team lunch", 18650, "approved", "2026-03", ""),
    (3, 1, "Cloud training course", 32000, "submitted", "2026-03", ""),
    (4, 2, "Mechanical keyboard", 12900, "rejected", "2026-03", "not a business expense"),
    (5, 3, "Client dinner", 74210, "submitted", "2026-03", ""),
    (6, 3, "Airport taxi", 4300, "approved", "2026-03", ""),
    (7, 1, "Reference books", 8800, "paid", "2026-02", ""),
    (8, 3, "Trade show booth", 49900, "approved", "2026-02", ""),
)

# (id, report_id, amount_cents, tick) - one payment for each report seeded as paid.
PAYMENTS: Final = ((1, 1, 45000, 0), (2, 7, 8800, 0))


def build_db() -> sqlite3.Connection:
    """A fresh in-memory database holding exactly the seed state."""
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    db.executemany("INSERT INTO employees VALUES (?, ?, ?)", EMPLOYEES)
    db.executemany("INSERT INTO policy VALUES (?, ?)", POLICY)
    db.executemany("INSERT INTO meta VALUES (?, ?)", META)
    db.executemany("INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?, ?)", REPORTS)
    db.executemany("INSERT INTO payments VALUES (?, ?, ?, ?)", PAYMENTS)
    db.commit()
    return db
