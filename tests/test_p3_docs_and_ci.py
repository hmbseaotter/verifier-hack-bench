"""Phase 3: the prose is under test too - README, walkthrough, CI workflow, repository hygiene."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from tests.conftest import ROOT
from vhb import seed
from vhb.cli import TABLE_BEGIN, TABLE_END
from vhb.scorer import markdown_table

README = (ROOT / "README.md").read_text(encoding="utf-8")
CARD = json.loads((ROOT / "scorecard.json").read_text(encoding="utf-8"))


def tracked_files() -> list[Path]:
    """What git would publish: tracked files plus untracked files that are not ignored."""
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    return [ROOT / name for name in listed.split("\0") if name and (ROOT / name).is_file()]


def test_readme_states_limits_first_names_what_survived_and_carries_the_real_table() -> None:
    """AC-31"""
    opening = README.split("\n\n")[1]
    assert not opening.startswith("#")
    for word in ("limits", "toy", "planted", "not a finding"):
        assert word in opening, f"the opening paragraph does not say '{word}'"
    assert "## Residual gaps" in README
    for entry in CARD["residual"] + CARD["over_blocking"]:
        assert Path(entry["file"]).stem in README
    table = README.split(TABLE_BEGIN, 1)[1].split(TABLE_END, 1)[0]
    assert table == "\n" + markdown_table(CARD), "run: python -m vhb readme"


def test_readme_numbers_match_the_repository() -> None:
    """AC-31, continued: every count the README states in prose is recomputed here."""
    spec = (ROOT / "specs" / "verifier-hack-bench.md").read_text(encoding="utf-8")
    requirements = len(set(re.findall(r"\((R-\d\d)\)", spec)))
    criteria = len(re.findall(r"^- \[[ x]\] \[P\d\] AC-", spec, re.MULTILINE))
    assert f"{len(CARD['trajectories'])} recorded trajectories" in README
    assert f"{requirements} requirements" in README and f"{criteria} acceptance" in README
    honest = sum(t["honest"]["hardened"]["total"] for t in CARD["tasks"].values())
    assert honest == 10 and "All ten honest runs" in README


def test_walkthrough_excerpts_are_the_real_source_and_the_real_seed() -> None:
    """AC-31, continued: a code excerpt that has drifted from the source is a false statement."""
    walkthrough = (ROOT / "docs" / "WALKTHROUGH.md").read_text(encoding="utf-8")
    sources = "".join(p.read_text(encoding="utf-8")
                      for p in sorted((ROOT / "src" / "vhb" / "verifiers").glob("*.py")))
    excerpts = re.findall(r"```python\n(.*?)```", walkthrough, re.DOTALL)
    assert len(excerpts) == 2 and all(excerpt in sources for excerpt in excerpts)
    submitted = [r[0] for r in seed.REPORTS if r[4] == "submitted"]
    assert submitted == [3, 5] and "Two reports are submitted: #3 (320.00) and #5" in walkthrough
    for run in re.findall(r"`((?:honest|exploit)_\w+)(?:\.json)?`", walkthrough):
        assert list((ROOT / "trajectories").rglob(f"{run}.json")), run


def test_the_license_is_the_one_the_documents_name() -> None:
    """Decision D14: one license, named the same way everywhere it is named."""
    assert (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License\n")
    assert 'license = "MIT"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "## License\n\nMIT. See [LICENSE](LICENSE)." in README


def test_ci_runs_every_gate_on_both_systems_and_line_endings_are_pinned() -> None:
    """AC-32. The workflow itself can only be observed after the first push."""
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for needle in ("ubuntu-latest", "windows-latest", '"3.11"', '"3.14"', "uv sync --locked",
                   "ruff check", "mypy", "pytest", "vhb score --check"):
        assert needle in workflow, needle
    assert "* text=auto eol=lf" in (ROOT / ".gitattributes").read_text(encoding="utf-8")


def test_nothing_published_names_a_machine_a_person_or_a_secret() -> None:
    """AC-33. Patterns are assembled from pieces so that this file does not match itself."""
    patterns = {
        "windows home path": r"[A-Za-z]:[\\/]+" + "Users" + r"[\\/]",
        "unix home path": "/" + "home" + r"/\w+",
        "macos home path": "/" + "Users" + r"/\w+",
        "drive-letter path": r"\b[A-Za-z]:\\\\?[A-Za-z_]+\\",
        "api key": "sk-" + r"ant-|gh" + r"p_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}",
    }
    offenders = []
    for path in tracked_files():
        if path.suffix in {".lock"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        offenders += [f"{path.relative_to(ROOT).as_posix()}: {name}"
                      for name, pattern in patterns.items() if re.search(pattern, text)]
    assert not offenders, offenders
    names = {path.name for path in tracked_files()}
    assert not any(n.endswith("_session.txt") or n.startswith(".env") for n in names)
