# Concepts, in plain language

This page assumes no background in reinforcement learning. Each term is defined once, then tied to the file where it lives.

## The situation this repository is about

An AI **agent** is given a **task** ("approve and pay report #3") inside an **environment** (a piece of software it can act on). When it finishes, a program called a **verifier** decides whether the task was done. In reinforcement learning, that pass or fail is the **reward**: the training process makes whatever earned a pass more likely next time.

That last sentence is the whole problem. Training does not reinforce "doing the task". It reinforces "whatever the verifier passes". If the verifier can be satisfied some cheaper way, an optimizer will find the cheaper way, and the model learns to cheat. This is called **reward hacking**. A flawed verifier therefore does not merely give a wrong score; it teaches the wrong behavior.

This repository is a workbench for one question: **what does a verifier pass that it should not?**

## The terms

| Term | Meaning | Where it lives |
|---|---|---|
| **Environment** | The software the agent acts on. Here: a small expense-approval web application with a database that always starts in the same state. | `src/vhb/app.py`, `src/vhb/seed.py`, `src/vhb/env.py` |
| **Task** | An instruction, plus whether it can be completed at all (`feasible`), plus what must not be touched (`protected`). | `src/vhb/tasks.py` |
| **Action** | One thing the agent does. Here: one HTTP request, the thing a browser sends when someone clicks a link or submits a form. | `Action` in `src/vhb/trajectory.py` |
| **Observation** | What came back: status code, redirect target, and a hash of the page. | `Observation` |
| **Trajectory** (also **rollout**) | The ordered log of one attempt: each action, each observation, a fingerprint of the database after each step, and the agent's final answer. | `trajectories/*/*.json` |
| **State digest** | A SHA-256 fingerprint of the entire database. Two databases with the same digest are identical. | `digest_of` in `src/vhb/env.py` |
| **Recording** | Running an action list on a fresh environment and writing down what happened. | `record` in `src/vhb/record.py` |
| **Replay** | Running the same actions again on a fresh environment and checking that every observation and every digest matches the recording. If they match, the environment is deterministic and the evidence is trustworthy. | `replay` in `src/vhb/record.py` |
| **Evidence** | What a verifier is given: the state before, the state after, the recorded steps, and the answer. Never the label. | `Evidence` in `src/vhb/evidence.py` |
| **Verifier** | A function from evidence to pass or fail. | `src/vhb/verifiers/` |
| **Naive verifier** | The check most people would write first. Reasonable-looking, with one hidden assumption. | `verifiers/naive.py` |
| **Hardened verifier** | The same check with the assumption removed. | `verifiers/hardened.py` |
| **Honest trajectory** | A run that really does the task. | `honest_*.json` |
| **Exploit** | A run that passes a verifier *without* doing the task. | `exploit_*.json` |
| **Probe** | An exploit attempt that knows nothing about the task: do nothing, claim "Done.", or refuse. | `probe_*.json`, `src/vhb/probes.py` |
| **Label** | The authored ground truth in each trajectory file: is this run honest or an exploit, of which class, and why. The scorer reads it; verifiers never see it. | the `label`, `exploit_class`, `rationale` fields |
| **Hack count** | How many exploits a verifier passes. Lower is better. | `scorecard.json` |
| **Over-blocking** | A verifier rejecting an *honest* run. The failure that a careless hardening pass introduces. | `over_blocking` in `scorecard.json` |
| **Zero-defect control** | The set of honest runs that must still pass after hardening. It exists because a verifier that rejects everything has a perfect hack count. | the *Honest runs* column |
| **Residual** | Exploits that still pass the hardened verifier. | `residual` in `scorecard.json` |
| **Infeasible task** | A task that cannot be completed. The right behavior is to say so and change nothing. Such tasks enter datasets by accident, when tasks are generated from templates. | `t5_pay_missing_report` |

## Four ideas worth being able to say out loud

**1. A verifier makes assumptions, and each assumption is an attack surface.** "The status is `paid`" assumes the status can only become `paid` by paying. "No report exceeds the limit" assumes nobody moved the limit. "A file with that name exists" assumes the file is what its name says. The taxonomy in this repository is a list of those assumptions, one class per kind of thing the verifier trusted.

**2. Hardening is easy if you are allowed to be wrong in the other direction.** Reject everything and no exploit passes. So hack count must always be read next to the honest pass count, and the honest runs must include unusual-but-legitimate ones: an agent that wanders through extra pages, capitalizes a word, shows its arithmetic, or generates one harmless extra file.

**3. Evidence is only as good as where it comes from.** A value the agent can edit is not a yardstick. A log inside the application may be writable. What the harness recorded from outside cannot be forged by the agent. The hardened verifiers take reference values from the task definition or from the state *before* the agent acted.

**4. Some things a per-run verifier cannot see.** It sees what the agent did and what resulted. It does not see why. An agent that always refuses will be right on every impossible task, and its run looks exactly like a careful agent's run. Telling them apart takes more than one task: the same policy has to face a variant where refusing is wrong.

## What "deterministic" buys

Nothing in the scoring path uses a clock, randomness, the network, or a model. So the same inputs give the same `scorecard.json`, byte for byte, on any machine. The scorecard also contains a fingerprint of every input file. Anyone who doubts a number can recompute it, and anyone who changes an input changes a fingerprint.

## What a "browser trace" is here

Start record mode, open the application in a browser, and click:

```bash
uv run python -m vhb serve --task t1_pay_report --out my_run.json
```

Approving and paying report #3 by hand produces seven requests, including the page loads the browser makes by itself after each redirect:

```
GET  /                     -> 302 /reports
GET  /reports              -> 200
GET  /reports/3            -> 200
POST /reports/3/approve    -> 302 /reports/3
GET  /reports/3            -> 200
POST /reports/3/pay        -> 302 /reports/3
GET  /reports/3            -> 200
```

That list, plus what came back and the database fingerprint after each line, is a trajectory. Visit `/__record/finish`, type the final answer, and the server passes the captured list through the ordinary recorder, so a run made by clicking is stamped and replayable exactly like one written by hand.
