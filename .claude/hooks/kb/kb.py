"""Shared knowledge-base scan for graph.py and recall.py: workspace + optional memory dir + skills.

Paths come from ../config.py (env vars AGENT_WORKSPACE, AGENT_MEMORY_DIR, AGENT_SKILLS_DIR).
A node is one .md file; its id is the file stem (or the folder name for SKILL.md).
Links are [[wikilinks]] plus `skill-name` in backticks when that skill exists.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from config import memory_dir, skills_dir, workspace  # noqa: E402

SKIP_PARTS = {"state-backups", "stashes", "node_modules", ".git"}
LINK = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
NAME = re.compile(r"^name:\s*(\S+)", re.M)
TICK = re.compile(r"`([a-z][a-z0-9-]+)`")
# Words used as example links inside templates; never counted as real links.
PLACEHOLDERS = {"link", "links", "topic", "other-fact", "name", "their-name", "related"}
# File stems that are fine without links (indexes, drafts, logs). Extend for your own output files.
ARTIFACT_PREFIXES = ("standup_", "_", "state-archive", "daily", "draft")
ARTIFACT_NAMES = {"MEMORY", "README"}


def dirs() -> list[pathlib.Path]:
    out = [workspace(), skills_dir()]
    mem = memory_dir()
    if mem:
        out.append(mem)
    return out


def node_id(f: pathlib.Path) -> str:
    return f.parent.name if f.name == "SKILL.md" else f.stem


def is_artifact(f: pathlib.Path) -> bool:
    n = f.stem
    return "drafts" in f.parts or n.startswith(ARTIFACT_PREFIXES) or n in ARTIFACT_NAMES


def files() -> list[pathlib.Path]:
    out = []
    for d in dirs():
        if d.exists():
            out += [f for f in d.rglob("*.md") if not SKIP_PARTS & set(f.parts)]
    return out


def skill_names() -> set[str]:
    d = skills_dir()
    return {p.name for p in d.iterdir() if (p / "SKILL.md").exists()} if d.exists() else set()


def scan() -> dict[str, tuple[pathlib.Path, set[str], list[str]]]:
    """id -> (file, outgoing link ids, lines). Also indexed by frontmatter `name:`."""
    nodes: dict[str, tuple[pathlib.Path, set[str], list[str]]] = {}
    skills = skill_names()
    for f in files():
        text = f.read_text(errors="ignore")
        links = {ln.strip().split("/")[-1].removesuffix(".md") for ln in LINK.findall(text)
                 if not ln.strip().startswith(("<", "..."))} - PLACEHOLDERS
        links |= (set(TICK.findall(text)) & skills) - {node_id(f)}
        entry = (f, links, text.splitlines())
        nodes[node_id(f)] = entry
        m = NAME.search(text[:500])
        if m:
            nodes.setdefault(m.group(1), entry)
    return nodes


def graph() -> tuple[dict, dict[str, set[str]], list[tuple[str, str]]]:
    """(id -> (file, links), id -> backlink ids, [(src, missing dst)]) over primary node ids."""
    nodes = scan()
    primary = {node_id(p): (p, links) for p, links, _ in nodes.values()}
    back: dict[str, set[str]] = {k: set() for k in primary}
    broken: list[tuple[str, str]] = []
    for src, (_, links) in primary.items():
        for dst in links:
            if dst in nodes:
                back[node_id(nodes[dst][0])].add(src)
            else:
                broken.append((src, dst))
    return primary, back, broken
