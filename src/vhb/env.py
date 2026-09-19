"""The environment wrapper: reset, step, snapshot, state digest.

`step` runs one action against the application in-process through the framework's test client.
No browser and no network socket are involved, which is why replay can be checked by hash
equality instead of being argued (decision D0).
"""
from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Final

from vhb.app import create_app
from vhb.trajectory import Action, Observation, Snapshot

METHODS: Final = ("GET", "POST")
# Digest of the seed state. `reset` must always land here; a test holds it (AC-01).
SEED_DIGEST: Final = "b7886adf8b8feec5112fce28400c44c71c3cf56102eeb26ae6406eac1442b4aa"


class ActionRefused(ValueError):
    """The action is not a GET or POST to a local absolute path; nothing was executed."""


def digest_of(snapshot: Snapshot) -> str:
    """SHA-256 over every table, tables in name order and rows in primary-key order."""
    dump = {table: [dict(row) for row in rows] for table, rows in snapshot.items()}
    text = json.dumps(dump, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Environment:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Back to the seed state: a brand-new application over a brand-new database."""
        self._app = create_app()
        self._client = self._app.test_client()

    def step(self, action: Action) -> tuple[Observation, str]:
        """Execute one action. Returns the observation to record, and the page body for the
        caller to read; only the body's hash is kept in a trajectory."""
        local = action.path.startswith("/") and not action.path.startswith("//")
        if action.method not in METHODS or not local:
            raise ActionRefused(f"refused: {action.method} {action.path}")
        data = dict(action.form) if action.method == "POST" else None
        response = self._client.open(action.path, method=action.method, data=data)
        body = response.get_data()
        observation = Observation(
            response.status_code, response.headers.get("Location", ""),
            hashlib.sha256(body).hexdigest())
        return observation, body.decode("utf-8")

    def snapshot(self) -> Snapshot:
        db = self._app.extensions["db"]
        tables = [row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
        return MappingProxyType({
            table: tuple(MappingProxyType(dict(row))
                         for row in db.execute(f"SELECT * FROM {table} ORDER BY 1"))
            for table in tables})

    def state_digest(self) -> str:
        return digest_of(self.snapshot())
