"""Verifier registries: for each task, one naive verifier and (from P2) one hardened verifier."""
from __future__ import annotations

from collections.abc import Callable, Mapping

from vhb.evidence import Evidence, Verdict

Verifier = Callable[[Evidence], Verdict]
Registry = Mapping[str, Verifier]
