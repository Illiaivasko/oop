#!/usr/bin/env python3
"""Text view of the [[wikilink]] graph over the workspace, memory dir and skills.

Usage: graph.py [NODE]  - no arg: hubs, orphans (non-artifact), broken links; NODE: its out/backlinks.
"""
import sys

from kb import graph, is_artifact, node_id, scan


def main() -> None:
    nodes = scan()
    primary, back, broken = graph()

    if len(sys.argv) > 1:
        q = sys.argv[1]
        if q not in nodes:
            sys.exit(f"no node '{q}'")
        nid = node_id(nodes[q][0])
        p, links = primary[nid]
        print(f"{nid}  ({p})\n  -> {sorted(links) or '-'}\n  <- {sorted(back[nid]) or '-'}")
        return

    orphans = sorted(k for k, (p, links) in primary.items() if not links and not back[k] and not is_artifact(p))
    hubs = sorted(primary, key=lambda k: -len(back[k]))[:10]
    print(f"nodes: {len(primary)}  links: {sum(len(v) for _, v in primary.values())}")
    print("top hubs (most backlinks):")
    for k in hubs:
        print(f"  {len(back[k]):3}  {k}")
    print(f"orphans ({len(orphans)}): {', '.join(orphans)}")
    print(f"broken links ({len(broken)}):")
    for src, dst in broken:
        print(f"  {src} -> [[{dst}]]")


if __name__ == "__main__":
    main()
