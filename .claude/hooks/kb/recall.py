#!/usr/bin/env python3
"""Deterministic recall: find everything the knowledge base holds about KEY.

Usage: recall.py KEY [KEY2 ...]   e.g. recall.py <TICKET> | recall.py cache stale | recall.py 409
Searches the workspace (unit records, state, notes, playbook), the optional memory dir and skills.
All KEYs must appear in a file (AND); matching ignores case and treats - and _ as equal.
"""
import re
import sys

from kb import node_id, scan

MAX_LINES = 4


def norm(s: str) -> str:
    return s.lower().replace("_", "-")


def main() -> None:
    keys = [norm(k) for k in sys.argv[1:]]
    if not keys:
        sys.exit(__doc__)
    nodes = scan()
    seen, hits = set(), []
    for f, links, lines in nodes.values():
        if f in seen:
            continue
        seen.add(f)
        low = [norm(line) for line in lines]
        body = "\n".join(low)
        if not all(k in body or k in norm(node_id(f)) for k in keys):
            continue
        matched = [(i + 1, lines[i].strip()) for i, line in enumerate(low) if any(k in line for k in keys)]
        name_hit = any(k in norm(node_id(f)) for k in keys)
        hits.append((name_hit, len(matched), f, links, matched))

    hits.sort(key=lambda h: (not h[0], -h[1]))
    print(f"recall {' + '.join(sys.argv[1:])}: {len(hits)} file(s)\n")
    for name_hit, n, f, links, matched in hits:
        tag = "NAMED " if name_hit else ""
        print(f"{tag}{node_id(f)}  ({n} hit{'s' if n != 1 else ''})  {f}")
        for ln, text in matched[:MAX_LINES]:
            print(f"    {ln:>4}: {re.sub(r'\s+', ' ', text)[:150]}")
        if links:
            print(f"    links -> {', '.join(sorted(links)[:8])}")
        print()


if __name__ == "__main__":
    main()
