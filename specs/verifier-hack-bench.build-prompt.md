# build prompt — verifier-hack-bench, first push (phases P0 to P4)

This is the file handed to the building agent. It targets **phases P0, P1, P2, P3, and P4 of
`specs/verifier-hack-bench.md` at spec version 0.2.0**, built strictly in that order. The owner
composed the first push as the whole skeleton floor (P0 to P3) plus the optional P4 scaffold.

Read `specs/verifier-hack-bench.md` and `specs/verifier-hack-bench.decisions.md` in full before
writing any code.

## Order of work

1. Restate the outcome in one sentence.
2. Re-read the spec's `assumptions` block. All were confirmed by the owner on 2026-09-19; flag any that the build shows to be wrong rather than working around it.
3. Build one phase at a time. A phase is finished only when every acceptance criterion tagged for it passes **by running it**. Do not start the next phase before that.
4. Within a phase, write tests alongside the code. Every test that verifies an acceptance criterion names the criterion's identifier (`AC-nn`) in its docstring, because AC-30 checks exactly that.
5. In P1, record every honest trajectory — including the atypical ones — **before** any hardened verifier exists. If a hardened verifier later rejects an honest trajectory, that is a finding: report it under `over_blocking` and in the README. Do not quietly edit the trajectory to make the problem disappear.
6. In P1, annotate a naive verifier with a published source only after opening and verifying that source. Otherwise describe the pattern without a citation.
7. After P4, run the whole suite, `mypy --strict`, `ruff check`, and `python -m vhb score --check` once more from a clean checkout state.

## Plan gate

Cleared. The owner approved the build plan in the specifying session on 2026-09-19 and authorized
local commits for that session, one per phase, with these subject lines:

1. `Add specification, decision record, and build prompt`
2. `P0: deterministic expense-desk environment with record and replay`
3. `P1: five tasks, naive verifiers, honest and exploit trajectories, taxonomy`
4. `P2: hardened verifiers, deterministic scorer, committed scorecard`
5. `P3: README, concept and walkthrough docs, cross-platform CI workflow`

Repair commits use `P<n> fix: <what>`. Phase 4 was added to the first push in the same answer that
granted the authorization, so its subject line was never shown to the owner: P4 work is left
uncommitted, with the proposed message `P4: live-model scaffold outside the scored package, fake
policy only` awaiting approval. A building agent working in any *other* session has no
authorization at all: it enters plan mode, presents its plan, and waits for the owner.

## Bright lines — never do these unattended

- Never push to a remote, and never create the GitHub repository.
- Never spend money. That includes constructing the model-backed policy in `live/`, calling any model API, and installing anything that bills.
- Never commit a credential, an absolute local path, or a tool-generated session file.

## Determinism boundary and type discipline

- Everything under `src/` is plain deterministic code. No model call, no network call, no wall-clock time, no randomness, no float for money.
- The only judgment task in the whole repository is the agent policy inside `live/`, which the build exercises with a scripted fake policy only.
- All of `src/` and `live/` passes `mypy --strict`. Records are frozen dataclasses; constants are `Final`; labels, origins, and taxonomy classes are enums.
- Every text file is written with `encoding="utf-8"` and `newline="\n"`.

## Scope discipline

- Build only what is tagged P0 to P4. Do not add features outside `in scope`; the `out of scope` list is as binding as the requirements.
- Flask is the sole runtime dependency. Flag any other runtime package before adding it.
- `src/` stays at or under 1,500 physical lines (AC-29). If the cap is threatened, cut, do not raise it.
- The application and seed may change freely during P0. From the first P1 recording onward they are frozen: any change means re-recording every trajectory and adding a changelog line.

## Records to keep

- Any fork the build resolves that the spec did not cover gets an entry in `specs/verifier-hack-bench.decisions.md`, in the same shape as the existing ones, ending with a **Rule** line, and a bullet under `decisions made` in the spec.
- If the spec itself has to change, add a changelog line and bump the version.
- Tick each acceptance-criterion checkbox in the spec only after running the check that proves it.

## Build-time settings

Recommended and acknowledged by the owner: Claude Fable 5.1 at high effort. The verifier and exploit
design in P1 and P2 is subtle adversarial reasoning and warrants it; P0 glue and P3 prose would run
fine one tier down, but the phases are too small to justify switching mid-build.

## Regeneration test

Could another agent rebuild this from the spec alone with behaviorally identical output? Structure
and behavior: yes. The exact scorecard: no, by design — seed rows and route details are Phase 0
discovery (D8). If the build finds anything else the spec leaves undetermined, that is a gap in the
spec: record it.
