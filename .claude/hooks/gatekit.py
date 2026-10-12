"""Shared plumbing for the blocking Stop gates: safe stdin, fail-closed errors, a per-gate repeat ladder, a decision log.

Repeat ladder, per session + gate, reset at the first Stop of each turn (stop_hook_active false):
  1st block   -> the gate's own message;
  2nd block   -> end the turn with ONE direct question to the human about this gate (never a silent pass);
  3rd and on  -> allowed, logged as gave-up (stops an endless block loop); the 3rd also appends one misses-style row to
                 <workspace>/improve/gave-up.md (date, [gave-up-<gate>], reason code, session hash) for the human to review.
Any exception (bad stdin, invalid env regex, missing module, unreadable file) is a block "GATE ERROR <gate>: ...".
Every decision goes to <workspace>/improve/gates.jsonl as gate, ts, session hash, reason code - never prompt or reply text.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl
except ImportError:  # no flock on this platform: parallel gates may lose a counter update, never a block
    fcntl = None

STATE_NAME = "gate-state.json"
LOG_NAME = "gates.jsonl"
GAVE_UP_NAME = "gave-up.md"
GAVE_UP_HEADER = "# Stop gates that gave up (3rd block in a turn let through) - review each reply, then delete its row\n"
MAX_STATE_KEYS = 200
ASK = ("{gate} blocked again in the same turn:\n{message}\n"
       "Do not retry or rephrase around it. End this turn NOW with one direct question to the human about this gate: "
       "what it found, what you propose (do the step, or skip it and why), and ask them to decide.")

Finding = tuple[str, str]  # (reason code, block message)


class GateError(Exception):
    pass


def read_payload(text: str | None = None) -> dict:
    raw = sys.stdin.read() if text is None else text
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise GateError(f"stdin is not JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise GateError(f"stdin is a JSON {type(data).__name__}, not an object")
    return data


def env_regex(name: str, default: str, flags: int = 0) -> re.Pattern:
    try:
        from config import ConfigError, env
        pattern = env(name, default) or default
    except ConfigError as exc:
        raise GateError(str(exc)) from exc
    try:
        return re.compile(pattern, flags)
    except re.error as exc:
        raise GateError(f"invalid regex in {name}: {exc}") from exc


def session_hash(payload: dict) -> str:
    sid = f"{payload.get('session_id') or ''}:{payload.get('agent_id') or ''}"
    return hashlib.sha256(sid.encode()).hexdigest()[:12]


def _improve_dir() -> Path:
    try:
        from config import workspace
        d = workspace() / "improve"
        d.mkdir(parents=True, exist_ok=True)
        return d
    except Exception:
        d = Path(tempfile.gettempdir()) / f"agentkit-gates-{os.getuid() if hasattr(os, 'getuid') else 0}"
        d.mkdir(parents=True, exist_ok=True)
        return d


def log_decision(gate: str, decision: str, reason: str, session: str) -> None:
    line = json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "gate": gate, "decision": decision,
                       "session": session, "reason": reason})
    with (_improve_dir() / LOG_NAME).open("a") as f:
        f.write(line + "\n")


def record_gave_up(gate: str, code: str, session: str) -> None:
    path = _improve_dir() / GAVE_UP_NAME
    row = f"| {time.strftime('%Y-%m-%d')} | [gave-up-{gate}] | {code} | s:{session} |\n"
    with path.open("a") as f:
        f.write(("" if f.tell() else GAVE_UP_HEADER) + row)


@contextmanager
def _locked_state():
    path = _improve_dir() / STATE_NAME
    with path.open("a+") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        try:
            state = json.loads(f.read() or "{}")
        except ValueError:
            state = {}
        state = state if isinstance(state, dict) else {}
        yield state
        if len(state) > MAX_STATE_KEYS:
            for key in sorted(state, key=lambda k: state[k].get("ts", 0))[:len(state) - MAX_STATE_KEYS]:
                del state[key]
        f.seek(0)
        f.truncate()
        f.write(json.dumps(state))


def _count(gate: str, session: str, active: bool, blocking: bool) -> tuple[int, int]:
    """(blocks earlier in this turn, blocks including this one)."""
    with _locked_state() as state:
        key = f"{session}:{gate}"
        before = int((state.get(key) or {}).get("n", 0)) if active else 0
        now = before + 1 if blocking else 0
        state[key] = {"n": now, "ts": time.time()}
    return before, now


def decide(gate: str, payload: dict, found: Finding | None) -> dict | None:
    """The block decision to print for this Stop, or None to let it through; logs every non-trivial decision."""
    session = session_hash(payload)
    before, now = _count(gate, session, bool(payload.get("stop_hook_active")), found is not None)
    if found is None:
        if before:
            log_decision(gate, "passed-after-block", "ok", session)
        return None
    code, message = found
    if now >= 3:
        log_decision(gate, "gave-up", code, session)
        if now == 3:  # one row per turn, and the human sees it now instead of reading a log later
            record_gave_up(gate, code, session)
            return {"systemMessage": f"{gate}: gave up after 2 blocks this turn ({code}) - not verified; "
                                     "recorded in improve/gave-up.md, review it."}
        return None
    log_decision(gate, "error" if code.startswith("error") else ("blocked" if now == 1 else "asked"), code, session)
    return {"decision": "block", "reason": message if now == 1 else ASK.format(gate=gate.upper(), message=message)}


def run(gate: str, check: Callable[[dict], Finding | None]) -> int:
    """Run one Stop gate fail-closed: an exception anywhere is a GATE ERROR block, never a silent pass."""
    payload: dict = {}
    try:
        payload = read_payload()
        found = check(payload)
    except Exception as exc:
        found = (f"error:{type(exc).__name__}", f"GATE ERROR {gate}: {type(exc).__name__}: {exc} - run agentkit doctor")
    try:
        out = decide(gate, payload, found)
    except Exception as exc:
        out = {"decision": "block", "reason": f"GATE ERROR {gate}: gate state {type(exc).__name__}: {exc} - run agentkit doctor"}
    if out:
        print(json.dumps(out))
    return 0
