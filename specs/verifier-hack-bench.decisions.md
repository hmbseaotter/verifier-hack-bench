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

**Extended by D12** — which verifier an exploit is classified against; the first decision question was reworded there, and the probe table changed.

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

**Partly taken up by D11** — the scaffold for option (C) was built as phase 4. Running a model and reporting what it does remains deferred.

**One exception made by D17** — a single run file that a model produced is published, unscored, as an illustration of two points the README makes. No count, rate, or comparison is reported from it, so option (C) stays deferred.

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

**Extended at 0.2.0** — phase 4 was added (D11); the tags now run P0 to P4 and still follow the plan's numbering.

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

## D12 — Against which verifier is an exploit classified?

**Fork:** Found during the build, while checking P1 labels against the decision procedure of D3. On the infeasible task, a trajectory that opens one page and refuses passes the naive verifier because its predicate is vacuously true, and would pass a hardened verifier because that verifier believes the refusal. One exploit, two defensible classes — the very thing D3 set out to prevent.

**Options considered**
- **(A) Always classify against the naive verifier** — simple; but the class of a surviving exploit would then describe a flaw that hardening already fixed, and say nothing about why it still passes.
- **(B) One class per verifier version** — accurate; breaks "exactly one class per exploit" and with it every per-class count.
- **(C) Classify against the strongest verifier the exploit defeats** (with two verifiers: the hardened one if the exploit gets through it, otherwise the naive one) — single-valued, and the class names the assumption to fix next, which is what a reader of the residual list needs.

**Decision ✅** — **(C)**. The first decision question was reworded from "passed without correctly declaring infeasibility" to "passed for any reason other than its declaring infeasibility", which says the same thing in terms of what the verifier looked at, consistent with the other four questions.

**Why** — A taxonomy is a tool for deciding what to repair. For an exploit that hardening stops, the naive verifier's assumption is the repair that was needed. For one that survives, the hardened verifier's assumption is the repair still owed.

**Consequences / caveats** — The refuse-only probe on an infeasible task is `INFEASIBLE_PASS`, because a probe defeats at most the naive verifier, which never reads the declaration. The authored constant-policy refusal is `CLAIM_CREDULITY` on the expectation that it survives hardening; if P2 shows it does not, its label is wrong and must change. **Outcome:** P2 showed that it does survive; it is the scorecard's one residual entry.

**Rule** — every entry of the scorecard's residual list is checked by a test to carry the class it was authored with, and the constant-policy refusal is asserted to be among them; enforced by the test for AC-12. Whether a label names the *right* assumption remains judgment.

---

## D13 — Three choices inside the live runner

**Fork:** Building P4 raised three questions the specification had not settled: which model is the default, what happens when the model refuses, and how a model-produced run is marked.

**Options considered**
- **(A) Default to a mid-tier model, as the specification first said** — cheaper per run; but it is a cost decision made on the owner's behalf, and the provider's current guidance is explicit that the default is `claude-opus-5` unless the user names another model.
- **(B) Default to `claude-opus-5`, overridable with `--model`** — follows that guidance and leaves cost to the owner.
- **(C) On a refusal, fall back to another model server-side** — the provider's recommended default for application code; but here the model *is* the subject of the measurement, and a run silently finished by a different model is a contaminated data point.
- **(D) On a refusal, end the episode and record the stop reason** — loses the run; keeps the data honest.

**Decision ✅** — **(B)** and **(D)**. Live output is written with label `unreviewed` and origin `model`.

**Why** — A harness that measures a model must not quietly substitute another one. And the choice of how much to spend is not the builder's to make.

**Consequences / caveats** — `model` is deliberately outside the origin enumeration, so no model run can enter the scored set until a later specification adds it and says how such runs are counted. Declining the provider's fallback default is a deviation from its guidance, made for a stated reason; the owner may overrule it. The model-backed policy has never been executed: no test may construct it, so its first real run is also its first test. *Update, 2026-09-21: the default model chosen here was changed by D16 after that first real run; the refusal rule stands.*

**Rule** — the runner refuses without the flag and the key, and no test constructs the model-backed policy; enforced by the tests for AC-35 and AC-37. That the model-backed policy *works* is not checkable without spending money, and is unverified. *Update, 2026-09-21: the owner has since spent the money; what those runs did and did not exercise is listed in the section on what was not checked.*

---

## D14 — Which license?

**Fork:** The specification first recorded "no LICENSE file", as an assumption the owner confirmed. The sweep at 0.2.4 found that assumption rested on a false fact, and reopened it. Which license, if any?

**Options considered**
- **(A) MIT** — what most of the owner's licensed public repositories use, including the toolkit that produced this specification. One short file; explicit permission to run, fork, and reuse.
- **(B) Apache-2.0 for code with CC BY 4.0 for documentation, plus a NOTICE file** — the owner's most deliberate pattern, used once, in a repository adjacent to patented work, where an explicit patent grant earns its place. Nothing here touches a patent.
- **(C) No license** — what the specification first said. All rights reserved by default: anyone may read the code, and a careful engineer at a company may not be allowed to run it.

**Decision ✅** — **(A)**, chosen by the owner.

**Why** — The point of publishing is that someone may want to try it. Option (C) was never really chosen: it was confirmed on the strength of a check that queried a field which does not exist, and so reported "none" for every repository it was asked about.

**Consequences / caveats** — That check failed in the way this repository is about: a predicate that returns the same answer whatever it is shown, accepted because the answer was plausible. It was caught only because the owner knew the claim to be wrong. The assumption and its correction are both left visible in the specification.

**Rule** — the LICENSE file, the package metadata, and the README name the same license; enforced by test_the_license_is_the_one_the_documents_name.

---

## D15 — How does a run that nobody has labeled get judged?

**Fork:** A live run arrives labeled `unreviewed`, and a fresh browser recording carries whatever label was chosen before the session started. `replay` and `score` load files through scored-set validation, which rejects `unreviewed` on purpose (AC-34). So the person who has to label a run had no command that showed what the two verifiers say about that run. Step-by-step instructions for a live run, written on 2026-09-20, ended at "read the JSON".

**Options considered**
- **(A) A `judge` command that does not read the label** — replay the file, hand the evidence to both verifiers through the scorer's own `evaluate`, print two verdicts with their reasons, write nothing.
- **(B) Teach scored-set validation to accept `unreviewed`** — `replay` and `score` would then load such files. That weakens the one gate that keeps unreviewed runs out of the scorecard, and every consumer of the label enumeration gains a third case.
- **(C) A helper script outside the repository** — no change to the public artifact, but throw-away work, and a reader who follows the README's live-run steps would still end at a file that nothing judges.
- **(D) Put the command in `live/`** — leaves `src/` untouched, but judging a file has nothing to do with calling a model, and a browser recording needs the same command.

**Decision ✅** — **(A)**, chosen by the owner.

**Why** — A verifier is never shown a label (D5, R-07), so judging a file needs none; reading the label would be the irregular choice. The command reuses `replay` and `evaluate`, so there is one code path for verdicts, and a test holds `judge` to the scorecard on every committed trajectory.

**Consequences / caveats** — `judge` builds the trajectory with placeholder authored fields, the way the live runner already does before a run is stamped. A verdict is a result, so the exit code does not say pass or fail: zero means judged, non-zero means the replay diverged and nothing was judged. `judge` does not put model-produced runs into the scorecard; that still belongs to a later specification (D6, D13). `src/` grows to about 1,480 of its 1,500 lines.

**Rule** — `judge` reads no authored field, writes no file, and agrees with the scorecard on every committed trajectory; enforced by test_judge_gives_both_verdicts_for_a_run_nobody_has_labeled_and_writes_nothing, test_judge_and_the_scorecard_never_disagree, and test_judge_refuses_a_run_that_does_not_replay.

---

## D16 — Which model is the default, now that the first choice is refused?

**Fork:** D13 made `claude-opus-5` the default, following the provider's guidance to default to its newest model. On 2026-09-21 the owner ran the runner for the first time. The provider's safety classifier declined the request twice, before the model had written anything, under the policy category `cyber`. The same request, sent to `claude-opus-4-8`, was served. The provider documents all of this: its newest models carry these classifiers, benign work can trigger the `cyber` category, and the stated remedy is to send the request to another model. A reader following the README would have ended at a refusal with no steps.

**Options considered**
- **(A) Default to `claude-opus-4-8`, and document the refusal** — the reader's first run works; the README says what a classifier refusal looks like and that `--model` selects another model.
- **(B) Keep `claude-opus-5`, and document the refusal and the `--model` remedy** — leaves D13 untouched; every reader's first run is likely to end at a refusal.
- **(C) No default: make `--model` required** — nothing in the repository then implies which model is "the" model; adds friction, and changes the runner's interface.
- **(D) Reword the system prompt until the classifier lets the request through** — not suggested by the provider, and it means shaping text to pass a safety filter. Rejected without trial.
- **(E) Turn on the provider's automatic fallback** — the rerouting that D13 rejected: a run silently finished by a different model is a contaminated data point.

**Decision ✅** — **(A)**, chosen by the owner.

**Why** — A default that is declined before the model reads the request measures nothing. Choosing the model in the open, by name, keeps what D13 protects: no run is ever finished by a model other than the one named on the command line and in the file.

**Consequences / caveats** — This supersedes only D13's choice of default model; D13's refusal rule stands. The observation rests on two declined requests and one served request, on one task, on one day, and the provider can change its classifiers at any time, so the README says "may". A refusal now keeps the policy category and the explanation that the provider returns, because the first refusal was recorded without them and could not be explained.

**Rule** — the README names the same default model as the runner's source, and a refusal's category and explanation are part of the recorded stop text; enforced by test_the_live_run_steps_name_what_the_runner_really_uses and test_a_refusal_keeps_the_category_and_the_explanation_the_api_gave.

---

## D17 — May the repository quote a live run at all?

**Fork:** The specification puts "running a live model, and reporting its results" out of scope (D6, option C, deferred), and the README said that no result from the runner is reported. The owner's first served run then showed two things worth saying, both about verifiers and not about the model: an honest refusal whose conclusion was right and one of whose stated reasons was false, which no verifier here can notice; and an answer with a sentence before the protocol keyword, which one of the over-strict test verifiers would have failed. Say so, and if so, how?

**Options considered**
- **(A) Quote the run in the README, publish the run file, and hold every stated fact with a test** — the file sits under `live/observed/`, outside `trajectories/`, exactly as the runner wrote it; any reader can run `judge` on it offline.
- **(B) Quote the run in prose only** — smaller; but it would be the one statement in the README that a reader cannot check, in a repository whose point is that claims are recomputable.
- **(C) Keep it out of the repository** — consistent with the out-of-scope line as first written; loses a real example of residual gap 2 and of why the control exists.
- **(D) Add the run to `trajectories/` as a labeled honest run** — it would change the scorecard, and origin `model` is outside the origin enumeration on purpose (D13). Counting model runs is what D6 deferred.

**Decision ✅** — **(A)**, chosen by the owner.

**Why** — An anecdote without its evidence is the kind of claim this repository exists to distrust. Publishing the file costs under two kilobytes and turns the anecdote into something a reader can replay.

**Consequences / caveats** — This is an illustration, not a measurement: one run, one model, one day, read by one person. No count, rate, or comparison is reported, so D6's deferral stands. The file keeps the label `unreviewed` although a person has read it, because it is kept byte for byte as the runner wrote it, and relabeling a model-produced run needs an origin value that the enumeration does not have yet. The model identifier in the file name will age. The scorecard never reads the file.

**Rule** — every fact the README states about the published run is recomputed from the file and the seed data; enforced by test_the_published_model_run_shows_exactly_what_the_readme_says.

---

## Not checked — as of 0.3.3 @ D17

What the sweep of 2026-09-21 looked at and set aside, or could not look at. This list replaces the one written at 0.2.4 @ D13; each of that list's items is carried forward below in its present state.

- **What this sweep read.** The specification, this record, and the build prompt were read whole, and every path and symbol named in the README and the two documents under `docs/` was checked by script. The README and `docs/CONCEPTS.md` were reviewed line by line by the owner on 2026-09-20 and 2026-09-21, reading as a newcomer would. `docs/WALKTHROUGH.md` was not re-read in this sweep; its code excerpts, seed facts, and run names are held by a test.
- **CI and Python versions.** The workflow passes on Ubuntu and Windows under Python 3.11 and 3.14, last observed on the commit before this one. The development machine has no 3.11 interpreter: between a change and its first CI run, 3.11 rests on the linter, which checks against a 3.11 target. macOS is not checked at all.
- **The model-backed policy.** No test may construct it. The owner has run it three times. Two requests were declined by the provider's safety classifier before the model wrote anything, and were recorded as refusals with no steps, as D13 requires. One request was served and ran the full exchange: the model sent requests through the tool, received each result, and returned a final answer; the file replayed and was judged. Not exercised with a real model: several tool calls in one turn, an invalid tool call, the step limit, and the output-token budget. Those paths are tested with the scripted stand-in only.
- **What D16 rests on.** Three requests, on one task, on one day. Whether the newest model declines the other four tasks was not tried, and the provider can change its classifiers at any time. The README says "may".
- **The README's live-run steps.** Each command was run as written, with two limits. The PowerShell line that asks for the key was run by the owner at a real terminal and never by a test, since it needs one. The Linux and macOS line was run in bash only, with its input piped in; it was not run in zsh and not at a real terminal.
- **`judge` on a path that does not exist** ends in the interpreter's own file-not-found error and not in a message of this harness. Left as is.
- **The published run (D17) is one file, and its test names that file.** A second file placed under `live/observed/` would be covered by the repository-wide checks for control characters, credentials, and local paths, and by nothing else.
- **Citations.** The four cited sources were opened and their claims checked, but through a fetch tool that converts pages to text, not by reading the PDFs. Section numbers were not re-verified independently. The provider's documentation page that D16 and the README cite was read the same way on 2026-09-21; it is a living page and may change.
- **`docs/CONCEPTS.md` is partly under test.** Held by tests: the glossary's alphabetical order, the seed counts it states, the hashing tools it names, the absence of first person, and the absence of control characters. Not held by any test: the paths and symbols in the glossary's "Where it lives" column, which were checked by script in this sweep, and its example commands for record mode and `judge`, which were run by hand.
- **The fingerprint set is an enumeration of six modules.** Verifier helper logic in `evidence.py`, and the replay and scoring code, are outside it. A change there that alters any verdict still changes the scorecard and fails `score --check`; what is lost is only the fingerprint that would say *which* input moved. Accepted for now; widening the set to every module under `src/` would change the committed scorecard and is left as a follow-up.
- **Whether each label names the right class.** The taxonomy makes classification decidable, and tests hold that every exploit has exactly one class. That the class chosen is the correct one remains judgment, recorded as a rationale in each file (D3).
- **Sentences that expire: now held by a scan.** The list at 0.2.4 recorded two stale claims about commit state and said a third instance would justify a detector. Three more of the same shape followed, each a sentence saying that something "has never" happened: about CI, about the model-backed policy, and in the README about the runner. A test now rejects that construction in every tracked document and source file except this record, whose entries are dated and are corrected by dated notes, never rewritten.

---

## Document status

Decisions **D0–D17** recorded; D12 and D13 were resolved by the build, and D14 to D17 after it. Nothing is open. Running a live model and reporting its results
(D6, option C) remains deferred to a later specification; D11 covers only the scaffold. The spec is at `specs/verifier-hack-bench.md` and the build prompt at
`specs/verifier-hack-bench.build-prompt.md`.

Any new fork encountered during the build is to be appended in the same shape — fork, options
considered, decision, why, rule — so this record does not go stale.
