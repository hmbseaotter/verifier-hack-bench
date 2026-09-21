"""Phase 3: the prose is under test too - README, walkthrough, CI workflow, repository hygiene."""
from __future__ import annotations

import hashlib
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
    seeded = (len(seed.EMPLOYEES), len(seed.REPORTS), len(seed.PAYMENTS), len(seed.POLICY))
    assert seeded == (4, 8, 2, 1)
    for document in (README, (ROOT / "docs" / "CONCEPTS.md").read_text(encoding="utf-8")):
        assert "four employees, eight expense reports, two payments" in document


def test_the_word_lists_are_ordered_the_way_they_say() -> None:
    """The README promises ten terms in build-up order; the glossary promises alphabetical order."""
    words = README.split("## The words this page uses", 1)[1].split("\n## ", 1)[0]
    assert "These ten terms" in words and len(re.findall(r"^- \*\*", words, re.MULTILINE)) == 10
    concepts = (ROOT / "docs" / "CONCEPTS.md").read_text(encoding="utf-8")
    glossary = concepts.split("## Glossary, in alphabetical order", 1)[1].split("\n## ", 1)[0]
    terms = re.findall(r"^\| \*\*([^*]+)\*\*", glossary, re.MULTILINE)
    assert len(terms) > 30 and terms == sorted(terms, key=str.casefold), terms


def test_fingerprints_can_be_recomputed_with_any_sha256_tool() -> None:
    """The documents say a plain `sha256sum <file>` reproduces a fingerprint. Hold them to it:
    it stays true only while files keep LF endings and trajectories stay in canonical form."""
    listed = {**CARD["fingerprints"]["modules"], **CARD["fingerprints"]["trajectories"]}
    assert len(listed) > 40
    for name, expected in listed.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    for document in (README, (ROOT / "docs" / "CONCEPTS.md").read_text(encoding="utf-8")):
        assert "sha256sum" in document and "Get-FileHash" in document


def test_the_live_run_steps_name_what_the_runner_really_uses() -> None:
    """The README walks a reader through a run that costs money, so every name, option and default
    in those steps is read from the runner itself."""
    runner = (ROOT / "live" / "run_agent.py").read_text(encoding="utf-8")
    steps = README.split("### A live run, step by step", 1)[1].split("\n## ", 1)[0]
    for name in ("DEFAULT_MODEL", "KEY_VARIABLE"):
        value = re.search(rf'^{name}: Final = "([^"]+)"', runner, re.MULTILINE)
        assert value and f"`{value.group(1)}`" in steps, name
    options = re.findall(r'add_argument\("(--[a-z-]+)"', runner)
    assert len(options) == 5 and all(f"`{option}`" in steps for option in options), options
    limits = re.findall(r'"(--max-[a-z-]+)", type=int, default=([\d_]+)', runner)
    assert len(limits) == 2
    for option, default in limits:
        assert f"`{option}` (default {int(default)})" in steps, option
    assert "uv sync --locked --extra live" in steps and "`live_runs/`" in steps
    assert "uv run python -m vhb judge live_runs\n" in steps, "the steps must end in a verdict"
    assert "live_runs/" in (ROOT / ".gitignore").read_text(encoding="utf-8").split()


def test_the_documents_are_not_written_in_the_first_person() -> None:
    """The documents describe a method, in general terms; who wrote which file is not the point."""
    for name in ("README.md", "docs/CONCEPTS.md", "docs/WALKTHROUGH.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        prose = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)  # code blocks are not prose
        first_person = re.findall(r"\b(?:I|[Mm]y|me|mine|[Ww]e|[Oo]ur|us)\b", prose)
        assert not first_person, f"{name}: {first_person}"


def test_no_sentence_claims_that_something_is_still_to_happen_for_the_first_time() -> None:
    """A present-perfect "never" is true until the day it is not, and nothing marks that day. Five
    such sentences went stale here, about commit state, CI, and the model runner; the decision
    record said a third would justify a scan. That record is the one exemption: its entries are
    dated, and they are corrected by dated notes, never rewritten."""
    expiring = re.compile(r"\b(?:has|have)\s+(?:never|not\s+yet)\b", re.IGNORECASE)
    exempt = {"specs/verifier-hack-bench.decisions.md"}
    offenders = []
    for path in tracked_files():
        name = path.relative_to(ROOT).as_posix()
        if path.suffix in {".md", ".py"} and name not in exempt:
            text = path.read_text(encoding="utf-8")
            offenders += [f"{name}: {m.group(0)!r}" for m in expiring.finditer(text)]
    assert not offenders, offenders


def test_no_stray_control_characters_in_anything_published() -> None:
    """An unescaped backslash sequence once turned a Windows path in a document into a tab and a
    vertical tab, which no reader would have spotted. Nothing published here needs any control
    character except the newline."""
    for path in tracked_files():
        stray = sorted({hex(byte) for byte in path.read_bytes() if byte < 32 and byte != 10})
        assert not stray, f"{path.relative_to(ROOT).as_posix()}: {stray}"


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
    # The first CI run failed before any code ran, on a floating major tag that does not exist.
    # Only GitHub's own actions are trusted to publish one; everything else is pinned exactly.
    for action, ref in re.findall(r"uses:\s*([\w.-]+/[\w./-]+)@(\S+)", workflow):
        exact = re.fullmatch(r"v\d+\.\d+\.\d+|[0-9a-f]{40}", ref)
        assert exact or action.startswith("actions/"), f"{action}@{ref} is a floating reference"
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
