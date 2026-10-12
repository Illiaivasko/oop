"""Shared path config for the kit's python hooks. Everything is driven by env vars; nothing is hardcoded.

AGENT_WORKSPACE   personal workspace dir (default: $CLAUDE_PROJECT_DIR/.work, else ./.work)
AGENT_STATE_FILE  live buffer file name inside the workspace (default: session_state.md)
AGENT_CODE_DIRS   ':'-separated code dirs watched by record-check (default: the project dir)
AGENT_CODE_GLOBS  ','-separated globs of code files (default: *.py,*.ts,*.tsx,*.js,*.go,*.rb,*.java,*.rs)
AGENT_MEMORY_DIR  optional machine-local memory dir (e.g. the agent's auto-memory folder)
AGENT_SKILLS_DIR  skills dir (default: $CLAUDE_PROJECT_DIR/.claude/skills)
Values may contain ~ and $VARS (e.g. "$HOME/<PROJECT>/.work"); they are expanded here.
"""
from __future__ import annotations
import os
import pathlib
import re

PLACEHOLDER = re.compile(r"<[A-Z][A-Z0-9_ -]*>")


class ConfigError(ValueError):
    pass


def env(name: str, default: str | None = None) -> str | None:
    """An env value, or the default; an unfilled <PLACEHOLDER> is an error, never a silent setting."""
    value = os.environ.get(name)
    hit = PLACEHOLDER.search(value or "")
    if hit:
        raise ConfigError(f"CONFIG ERROR: placeholder {hit.group(0)} in {name} - set it (SETUP.md section 5) or remove it from the settings env")
    return value or default


def _path(value: str) -> pathlib.Path:
    return pathlib.Path(os.path.expandvars(os.path.expanduser(value)))


def project_dir() -> pathlib.Path:
    return _path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def workspace() -> pathlib.Path:
    return _path(env("AGENT_WORKSPACE") or str(project_dir() / ".work"))


def state_file() -> pathlib.Path:
    return workspace() / os.environ.get("AGENT_STATE_FILE", "session_state.md")


def code_dirs() -> list[pathlib.Path]:
    raw = os.environ.get("AGENT_CODE_DIRS")
    return [_path(p) for p in raw.split(":") if p] if raw else [project_dir()]


def code_globs() -> list[str]:
    raw = os.environ.get("AGENT_CODE_GLOBS", "*.py,*.ts,*.tsx,*.js,*.go,*.rb,*.java,*.rs")
    return [g.strip() for g in raw.split(",") if g.strip()]


def memory_dir() -> pathlib.Path | None:
    raw = os.environ.get("AGENT_MEMORY_DIR")
    return _path(raw) if raw else None


def skills_dir() -> pathlib.Path:
    return _path(os.environ.get("AGENT_SKILLS_DIR") or str(project_dir() / ".claude" / "skills"))
