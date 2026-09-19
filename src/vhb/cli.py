"""Command line: python -m vhb record | replay | probes | score | serve."""
from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from vhb.probes import write_probes
from vhb.record import replay, stamp_file
from vhb.recordmode import serve
from vhb.scorer import SCORECARD, ReplayDiverged, markdown_table, render
from vhb.taxonomy import ExploitClass
from vhb.trajectory import Label, Meta, Origin, read_trajectory, write_text

TRAJECTORIES: Final = Path("trajectories")


def trajectory_files(paths: Sequence[Path]) -> list[Path]:
    """Every .json under the given files and directories, in one stable order."""
    found: list[Path] = []
    for path in paths or [TRAJECTORIES]:
        found += sorted(path.rglob("*.json")) if path.is_dir() else [path]
    return sorted(found, key=lambda p: p.as_posix())


def cmd_record(args: argparse.Namespace) -> int:
    for path in trajectory_files(args.paths):
        print(f"stamped {path.as_posix()}: {len(stamp_file(path).steps)} step(s)")
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    failures = 0
    for path in trajectory_files(args.paths):
        diverged_at = replay(read_trajectory(path)).diverged_at
        failures += diverged_at is not None
        print(f"{'ok      ' if diverged_at is None else f'DIVERGED at step {diverged_at}'} "
              f"{path.as_posix()}")
    return 1 if failures else 0


def cmd_probes(args: argparse.Namespace) -> int:
    for path in write_probes(TRAJECTORIES):
        print(f"wrote {path.as_posix()}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    """Exit 0 on success, 1 when --check finds a mismatch, 2 when a trajectory diverges."""
    try:
        text = render(trajectory_files([]))
    except ReplayDiverged as error:
        print(f"error: {error} - no scorecard written")
        return 2
    if args.check:
        same = SCORECARD.exists() and SCORECARD.read_bytes() == text.encode("utf-8")
        print(f"{SCORECARD}: " + ("reproduced byte for byte" if same else "MISMATCH"))
        return 0 if same else 1
    write_text(SCORECARD, text)
    print(markdown_table(json.loads(text)), end="")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    exploit_class = ExploitClass(args.exploit_class) if args.exploit_class else None
    meta = Meta(args.task, Label(args.label), Origin.HUMAN, exploit_class, args.rationale)
    serve(meta, args.out, args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vhb", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    record = commands.add_parser("record", help="(re)stamp trajectory files in place")
    record.add_argument("paths", nargs="+", type=Path)
    record.set_defaults(run=cmd_record)

    replay_ = commands.add_parser("replay", help="replay trajectories and compare every stamp")
    replay_.add_argument("paths", nargs="*", type=Path)
    replay_.set_defaults(run=cmd_replay)

    probes = commands.add_parser("probes", help="write the three generic probes for every task")
    probes.set_defaults(run=cmd_probes)

    score = commands.add_parser("score", help="replay all, run both verifiers, write scorecard")
    score.add_argument("--check", action="store_true",
                       help="compare a fresh scorecard with the committed one; write nothing")
    score.set_defaults(run=cmd_score)

    serve_ = commands.add_parser("serve", help="record a trajectory by clicking in a browser")
    serve_.add_argument("--task", required=True)
    serve_.add_argument("--out", required=True, type=Path)
    serve_.add_argument("--port", type=int, default=5000)
    serve_.add_argument("--label", default="honest", choices=[label.value for label in Label])
    serve_.add_argument("--exploit-class", default="")
    serve_.add_argument("--rationale", default="")
    serve_.set_defaults(run=cmd_serve)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result: int = args.run(args)
    return result
