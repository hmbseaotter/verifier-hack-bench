"""Human record mode: click through the application in a real browser, get a trajectory.

The server notes the method, path, and form fields of every request the browser sends. On finish
it does not trust its own live state: it passes the captured action list through the ordinary
recorder on a fresh environment, so a human-recorded trajectory is stamped, and replayable,
exactly like an authored one.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

from flask import Flask, render_template_string, request

from vhb.app import create_app
from vhb.env import METHODS
from vhb.record import record
from vhb.seed import build_db
from vhb.tasks import TASKS
from vhb.trajectory import Action, Meta, write_trajectory

CONTROL_PREFIX: Final = "/__record"
_IGNORED: Final = ("/favicon.ico",)
_FINISH: Final = """<!doctype html><title>Finish recording</title>
<h1>Finish recording: {{ task.id }}</h1><p>{{ task.instruction }}</p>
<p>{{ count }} action(s) captured.</p>
<form method="post">final answer <textarea name="answer"></textarea>
<button>Stamp and save</button></form>
"""


def recording_app(meta: Meta, out: Path) -> Flask:
    app = create_app()
    captured: list[Action] = []

    @app.before_request
    def capture() -> None:
        path = request.path
        if path.startswith(CONTROL_PREFIX) or path in _IGNORED or request.method not in METHODS:
            return
        if request.query_string:
            path = f"{path}?{request.query_string.decode('utf-8')}"
        captured.append(Action(request.method, path, tuple(sorted(request.form.items()))))

    @app.get(f"{CONTROL_PREFIX}/finish")
    def finish_form() -> str:
        return render_template_string(_FINISH, task=TASKS[meta.task], count=len(captured))

    @app.post(f"{CONTROL_PREFIX}/finish")
    def finish() -> str:
        trajectory = record(meta, list(captured), request.form.get("answer", "").strip())
        write_trajectory(out, trajectory)
        captured.clear()
        app.extensions["db"] = build_db()  # the next session starts from the seed again
        return f"Saved {len(trajectory.steps)} step(s) to {out.as_posix()}. State reset to seed."

    return app


def serve(meta: Meta, out: Path, port: int) -> None:
    """Loopback only, one request at a time, so captured order equals execution order."""
    print(f"Task: {TASKS[meta.task].instruction}")
    print(f"Open http://127.0.0.1:{port}/ - when done, open {CONTROL_PREFIX}/finish")
    recording_app(meta, out).run(host="127.0.0.1", port=port, threaded=False)
