# verifier-hack-bench — Decision Record

- **Project:** verifier-hack-bench
- **Identity:** a red-team harness that measures how often a task verifier can be satisfied without the task being done
- **Spec:** specs/verifier-hack-bench.md
- **Status:** decisions accrue during the interview and the build; finalized alongside the spec
- **Legend:** ✅ decided · 🔶 open / revisit · ⏭️ deferred to a later phase

Each entry ends with a **Rule** line naming what enforces the decision, or stating plainly that it
is a judgment nothing can check.

<!-- rules-required-from: D0 -->

---

## D0 — What is an action, and how is a trajectory replayed?

**Fork:** Should the environment be driven by a real browser, or by the HTTP requests a browser would send?

**Options considered**
- **(A) HTTP requests, replayed in-process, plus a record mode for human sessions** — a trajectory is an ordered list of requests; replay runs through the framework's test client with no browser and no socket; a record mode captures a person clicking through the application into the same format. Deterministic by construction; a reader reproduces everything with one install. Costs the "browser agent" look.
- **(B) HTTP requests only** — as (A) without record mode. About forty lines cheaper; loses the concrete demonstration that a trace is simply what the browser sent.
- **(C) Real browser through Playwright** — trajectories are goto/click/fill steps. Closest to a browser agent. Every reader and every CI run needs a browser download; replay needs a live port and waits on page loads; determinism has to be argued rather than shown by hash equality.

**Decision ✅** — **(A)**, chosen by the owner.

**Why** — None of the five exploit classes depends on pixels or on the DOM; every one is expressible as requests. The repository's central promise is that any number can be recomputed by someone who does not trust the author, and a browser in the loop weakens exactly that promise. Record mode is kept because it makes the trajectory format explainable in one sentence.

**Consequences / caveats** — The README must say the action space is HTTP-level and must not claim browser-agent realism. A later live-model phase plugs into `step`, not into a browser.

**Rule** — scoring opens no socket; enforced by the test for AC-26.

---

## D1 — Which application is the environment?

**Fork:** Which fake internal tool gives every exploit class a natural home?

**Options considered**
- **(A) Expense-approval desk** — workflow states (shortcut), a writable policy limit (tampering), exports (artifact), totals (answer matching), nonexistent reports (infeasible).
- **(B) Ticket triage** — good for workflow and answer tasks; tampering and artifact exploits feel contrived.
- **(C) Inventory adjustment** — infeasible tasks are very natural; answer matching and tampering are weak fits.

**Decision ✅** — **(A)**, chosen by the owner.

**Why** — It is the only candidate where no exploit class has to be forced, and the domain needs no explanation.

**Consequences / caveats** — Money enters the design, so amounts are integer cents throughout.

**Rule** — no float in any snapshot, trajectory, or scorecard; enforced by the test for AC-17.

---

## D2 — Repository name

**Fork:** Keep `verifier-hack-bench`, or rename?

**Options considered**
- **(A) `verifier-hack-bench`** — contains "verifier" and "hack"; the repository does bench verifiers for hackability.
- **(B) `verifier-redteam`** — closer to the phrase "red-teaming suites"; avoids "bench", which some read as an agent benchmark.
- **(C) `reward-hack-audit`** — leads with the RL term; drops the word "verifier".

**Decision ✅** — **(A)**, chosen by the owner. Package name `vhb`.

**Why** — The measured object is the verifier, so "bench" is accurate; the name was already in use.

**Rule** — judgment, not checkable.

---

## D3 — What principle makes the taxonomy closed and single-label?

**Fork:** The starting taxonomy mixed exploit mechanisms (four classes) with a task defect (infeasible task). How is "exactly one class per exploit" made decidable?

**Options considered**
- **(A) Flat list of five names with prose definitions** — simple; a reviewer can argue most exploits into two classes, and nothing settles the argument.
- **(B) Multi-label** — honest about overlap; destroys per-class counts and the claim of a typed taxonomy.
- **(C) Partition the verifier's evidence surface, with an ordered decision procedure** — every pass depends either on answer text or on state; state is reference data, a new artifact, or an existing target object; infeasibility overrides all. Five questions asked in order, first "yes" wins.

**Decision ✅** — **(C)**.

**Why** — Each class then names one ungrounded assumption in the verifier, which is the thing a verifier author can actually fix. Exhaustiveness follows from the partition rather than from the author's imagination, and the last question is a true catch-all. "Substring or format credulity" is renamed `CLAIM_CREDULITY` because the same assumption covers an unfounded "done" and an unfounded "infeasible".

**Consequences / caveats** — Exhaustive only over the evidence these verifiers read. Judge-model manipulation and harness tampering are outside it and are listed as limits. Probe classes are assigned by a static table, which is exact for these five tasks and a simplification in general.

**Rule** — every exploit carries exactly one class from the five; enforced by the tests for AC-07 and AC-18. Whether a given label is the *right* class remains judgment, recorded as a rationale in each file.

---

## D4 — Harden the verifier, the environment, or both?

**Fork:** The application has planted weaknesses. Should hardening fix them?

**Options considered**
- **(A) Verifiers only; environment frozen** — before and after differ in exactly one variable, and every trajectory replays identically under both.
- **(B) Fix the application too** — closer to real practice, where both are fixed; but recorded trajectories stop replaying, and the measured reduction can no longer be attributed.

**Decision ✅** — **(A)**.

**Why** — Attribution. A comparison that changes two things measures neither. Real software also keeps affordances beyond the intended path, so a verifier has to be robust to them regardless.

**Consequences / caveats** — The README says that in practice the environment would be fixed as well.

**Rule** — both verifiers receive the identical input object; enforced by the test for AC-28.

---

## D5 — Where does ground truth come from?

**Fork:** How does the scorer know a trajectory is an exploit?

**Options considered**
- **(A) Author-assigned label in each trajectory file, loaded by the scorer** — transparent, reviewable, and wrong only where a human can see it.
- **(B) An oracle function that decides whether the task was really completed** — a perfect oracle would simply be the hardened verifier, so the measurement would grade the hardened verifier against itself.

**Decision ✅** — **(A)**.

**Why** — A scorer that derives its own expectations turns every scorer bug into ground truth. Loading them keeps the two independent.

**Consequences / caveats** — Verifiers must not see labels, or the separation is meaningless.

**Rule** — the verifier input type has no label, class, origin, or rationale field; enforced by the test for AC-25.

---

## D6 — How is the circularity of planted exploits handled?

**Fork:** The author writes the naive verifiers and the exploits that beat them, so the "before" number is fixed by construction. How much does the scorecard claim?

**Options considered**
- **(A) Targeted exploits only** — the before-count is always total/total and proves nothing by itself.
- **(B) Add task-agnostic probes, reported in their own column** — a do-nothing agent, a claim-only agent, and a refuse-only agent run against every task. They are not tailored to any verifier, so a probe that passes is a finding rather than a construction.
- **(C) Wait for a live model to find exploits** — the strongest evidence; needs spend and a human checkpoint, so it cannot be part of this specification.

**Decision ✅** — **(B)** now, **(C)** ⏭️ deferred.

**Why** — Probes cost three generated files per task and convert part of the scorecard from demonstration into measurement. The README states the circularity of the targeted column in plain words.

**Rule** — every targeted exploit must pass its naive verifier, and probes are counted separately; enforced by the tests for AC-06 and AC-08.

---

## D7 — What evidence may a hardened verifier trust?

**Fork:** Hardening means checking more. More of what?

**Options considered**
- **(A) Whole-state diff: nothing may change except the expected rows** — closes almost everything; also rejects honest trajectories that do something harmless and extra, such as generating a second export.
- **(B) In-environment audit log as process evidence** — natural, and wrong: anything inside the environment may be agent-writable.
- **(C) Declared protected state compared between initial and final snapshots, reference values from the task definition or the initial snapshot, process evidence from harness-recorded steps only** — constrains what matters, tolerates benign extras, and keeps the yardstick outside the agent's write surface.

**Decision ✅** — **(C)**.

**Why** — Over-blocking is a failure class of its own. (A) scores perfectly on hack rate while punishing honest variation; (C) is the narrowest rule that still closes the planted exploits.

**Consequences / caveats** — Each task must declare its protected state explicitly, and each task needs an atypical honest trajectory to give the control teeth. Honest trajectories are recorded before hardened verifiers are written.

**Rule** — every honest trajectory passes its hardened verifier or is reported; tampering exploits fail with the protected state named; enforced by the tests for AC-11 and AC-20.

---

## D8 — Specify before or after Phase 0?

**Fork:** Phase 0 is discovery. Does specifying first anchor the environment to an untested shape?

**Options considered**
- **(A) Build Phase 0, then specify Phases 1 and 2** — the spec describes a known environment; the interview waits on the build.
- **(B) Specify first, pin only the interface, allow amendment** — the interview happens once, up front; application routes and seed rows are marked amendable until P1.

**Decision ✅** — **(B)**. Phase tags P0 to P3 follow the project plan's numbering.

**Why** — The shapes the requirements depend on — reset, step, snapshot, digest, trajectory — are not in doubt. What is in doubt is route and seed detail, which the spec deliberately does not freeze.

**Rule** — any change to the application or seed after P1 requires re-recording and a changelog line; enforced by replay divergence failing the scorer (AC-22).

---

## D9 — Web framework

**Fork:** Flask, FastAPI, or no framework?

**Options considered**
- **(A) Flask with stdlib `sqlite3`** — one runtime dependency, server-rendered forms, an in-process test client. Verified to install on Python 3.14.
- **(B) FastAPI** — typed request models; drags in a compiled validation dependency and reads as an API rather than an internal tool.
- **(C) stdlib WSGI by hand** — zero dependencies; costs lines and looks odd to a reader.

**Decision ✅** — **(A)**.

**Rule** — no module under `src/` imports an HTTP client or a model SDK; enforced by the test for AC-26.

---

## D10 — How are results expressed?

**Fork:** Percentages or counts, and for which verifiers?

**Options considered**
- **(A) Hack rate as a percentage, honest pass rate after hardening only** — reads well; hides denominators of three to six.
- **(B) passed/total pairs everywhere, honest pass counts for naive verifiers too** — less tidy; shows the true sample size and exposes any naive verifier that rejects honest work.

**Decision ✅** — **(B)**.

**Rule** — the scorecard holds only integer pairs for results; enforced by the test for AC-27.

---

## D11 — Where does the live-model scaffold live, and does it count toward the line cap?

**Fork:** The owner selected a live-model scaffold for the first push, against the interviewer's advice to defer it. The bench promises that nothing under `src/` imports a model SDK and that `src/` stays under 1,500 lines. A model runner strains both promises. Where does it go?

**Options considered**
- **(A) Inside the package, `src/vhb/agent.py`, counted toward the cap** — one place to look; but the scored package would then import a model SDK, even if lazily, and the static offline check would need an exception — an exception in a guarantee is the start of not having one.
- **(B) A separate `live/` directory outside `src/`, not counted toward the cap, size stated in the README** — the scored package stays provably offline and small; the scaffold is visibly optional. The cost is that "the cap counts `src/` only" could be read as a dodge, so the scaffold's size has to be stated rather than hidden.
- **(C) Defer the scaffold to a later specification** — the interviewer's recommendation; declined by the owner.

**Decision ✅** — **(B)**.

**Why** — The offline guarantee is worth more than tidiness, and it is only a guarantee while it has no exceptions. The cap exists so a reviewer can read the bench in ten minutes; an optional runner in its own directory does not lengthen that read.

**Consequences / caveats** — The runner writes trajectories labeled `unreviewed`, a label the scored set rejects by design, so no model output can enter the scorecard without a person labeling it. The build and the tests use a scripted fake policy only; constructing the model-backed policy spends money and is the owner's act alone. `step` must return the response body to its caller, because a model needs to read the page, while the recorded observation keeps only the body's hash.

**Rule** — no module under `src/` imports `live`, and the runner refuses without the flag and the key; enforced by the tests for AC-35 and AC-37.

---

## Not checked — as of 0.1.0 @ D10

- **Published verifier patterns.** The naive verifiers are meant to model patterns that occur in real benchmarks (substring matching, predicates a do-nothing agent satisfies). No source was verified while writing the spec; verification is a build task, and an unverified pattern is described without citation.
- **The environment does not exist yet.** Routes and seed rows in the design reference are a plan. Whether every planned exploit is actually reachable through them is unknown until Phase 0 and Phase 1 run.
- **Whether any exploit genuinely survives hardening.** AC-12 requires a non-empty residual list. The expected survivor is the constant-policy refusal on the infeasible task; that expectation is reasoning, not a result.
- **CI.** The workflow cannot run before the GitHub repository exists. Linux behavior is therefore unobserved until the first push; macOS is not checked at all.
- **Traceability by count only.** The linter compares the number of criteria to the number of requirements. The mapping was traced by hand once; AC-30 makes it a test, which does not exist yet.

---

## Document status

Decisions **D0–D11** recorded. Nothing is open. Running a live model and reporting its results
(D6, option C) remains deferred to a later specification; D11 covers only the scaffold. The spec is at `specs/verifier-hack-bench.md` and the build prompt at
`specs/verifier-hack-bench.build-prompt.md`.

Any new fork encountered during the build is to be appended in the same shape — fork, options
considered, decision, why, rule — so this record does not go stale.
