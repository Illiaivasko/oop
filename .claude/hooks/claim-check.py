#!/usr/bin/env python3
"""Stop / SubagentStop gate: a "verified / fixed / works" claim about a unit needs valid receipts for every AC,
and an excuse ("pre-existing", "out of scope") needs evidence.

A negation counts only when it governs the claim word (up to 3 words before it); a claim sentence without a key takes
the keys of its neighbour sentences in the same paragraph. Everyday words (done, closed, shipped, passing, green,
confirmed, готово, зроблено) are claims only with a key in the same sentence, not right after be/to/will/once/if/when
and not in a sentence that opens with once/if/when/after/until ("done reading the file", "the job is closed for
today", "TK-1 will be done tomorrow" are not claims; "TK-1 closed." is). The reply is NFKC-normalised, zero-width
characters dropped and unicode dashes mapped to "-" before matching. Keys match AGENT_UNIT_KEY_RE as typed, plus the
AGENT_UNIT_KEY_PREFIXES prefixes in any case (tk-3 -> TK-3). The reply is `last_assistant_message`, else the transcript.
Repeat blocks, errors and the decision log: see gatekit.py.
"""
from __future__ import annotations

import functools
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

GATE = "claim-check"
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "tools"), str(HERE)]  # kit layout, or evidence.py installed next to the hooks
try:
    import gatekit
    from transcript_tail import final_reply
except Exception as exc:  # a broken install must block, not exit 1 (non-blocking)
    print(json.dumps({"decision": "block", "reason": f"GATE ERROR {GATE}: {exc} - run agentkit doctor"}))
    sys.exit(0)

PASSES = r"pass(?:es|ed|ing)?"
CLAIM = re.compile(
    r"(?i)\b(?:verified|tested|works|fixed|resolved|it passes|all green|green across the board|confirmed working"
    r"|ready for (?:qa|review|testing|merge|release)"
    r"|all (?:the )?(?:unit |e2e )?(?:tests?|acs?|checks?|specs?) (?:are |now )*(?:" + PASSES + r"|green)"
    r"|(\d+)\s*/\s*\1 (?:tests?|acs?|checks?|specs?)?\s*(?:are )?" + PASSES + r")\b"
    r"|(?i:\b(?:перевірено|протестовано|працює|пофіксено|виправлено|все зелене|все проходить)\b)")
# everyday words: a claim only with a unit key in the same sentence
WEAK_CLAIM = re.compile(r"(?i)\b(?:done(?!\s+(?:with\b|\w+ing\b))|shipped|closed|passing|green|confirmed|готово|зроблено)\b")
NOT_YET_WORDS = {"be", "to", "will", "once", "when", "if", "until", "unless", "get", "gets", "буде", "будуть", "коли", "якщо", "щойно"}
CONDITIONAL = re.compile(r"(?i)^\W*(?:once(?!\s+again)|if|when|after|until|unless|якщо|коли|щойно|після того)\b")
PARTIAL = re.compile(r"(\d+)\s*/\s*(\d+)")
DASHES = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015\u2043\u2212\ufe58\ufe63\uff0d"), "-")
INVISIBLE = dict.fromkeys(map(ord, "\u00ad\u200b\u200c\u200d\u2060\ufeff"), None)
NEGATION_WORDS = {"not", "never", "no", "nothing", "none", "cannot", "не", "ні"}
NEGATION_SPAN = 3
WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)?")
EXCUSE = re.compile(
    r"(?i)pre-?existing|already (failing|broken)|out of scope|unrelated (to|failure)|not related to (my|this|the) change"
    r"|\bflaky\b|skipp(ed|ing) (the )?(failing )?tests?|існувал\w* (і )?до|не пов.язан\w* з (моєю|цією) змін|поза скоупом|було (й|і) до")
# an excuse must name its evidence: a count, a test id, a commit sha, a path, or a log / receipt
EVIDENCE = re.compile(
    r"(?<![\w-])\d+(?![\w-])"
    r"|\btest_\w+|\w+::\w+|\b\w+\.(?:test|spec)\.\w+"
    r"|\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b"
    r"|(?<![\w/])(?:~|\.{1,2})?/[\w.-]+(?:/[\w.-]*)*|\b[\w-]+(?:/[\w.-]+)*\.(?:py|ts|tsx|js|go|rb|java|rs|sh|log|txt|json|ya?ml)\b"
    r"|(?i:\b(?:logs?|receipts?|evidence\.py|verify status)\b)")
VERIFY_WORDS = re.compile(
    r"(?i)\b(?:verified|tested|confirmed|green across the board|works as expected|ready for (?:qa|testing)"
    r"|all (?:the )?(?:unit |e2e )?(?:tests?|acs?|checks?|specs?) (?:are |now )*(?:" + PASSES + r"|green)"
    r"|(\d+)\s*/\s*\1 (?:tests?|acs?|checks?|specs?)?\s*(?:are )?" + PASSES + r")\b"
    r"|(?i:\b(?:перевірено|протестовано|все проходить)\b)")


@functools.cache
def _unit_key() -> re.Pattern:
    return gatekit.env_regex("AGENT_UNIT_KEY_RE", r"\b[A-Z][A-Z0-9]+-\d+\b")


@functools.cache
def _prefix_key() -> re.Pattern | None:
    prefixes = [p.strip() for p in os.environ.get("AGENT_UNIT_KEY_PREFIXES", "").split(",") if p.strip()]
    return re.compile(r"\b(?:" + "|".join(map(re.escape, prefixes)) + r")-\d+\b", re.I) if prefixes else None


def unit_keys(text: str) -> set[str]:
    keys = set(_unit_key().findall(text))
    if _prefix_key():
        keys |= {k.upper() for k in _prefix_key().findall(text)}
    return keys


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).translate(INVISIBLE).translate(DASHES)


# a quoted example or a code block is not the agent's own claim (drafts in fences are checked by live-read-check)
QUOTED = re.compile(r"```.*?```|`[^`\n]*`|\"[^\"\n]{1,300}\"|“[^”\n]{1,300}”|«[^»\n]{1,300}»", re.S)


def unquoted(text: str) -> str:
    return QUOTED.sub(" ", text)


@functools.cache
def _evidence():
    import evidence
    return evidence


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?\n])\s+", text) if s.strip()]


def paragraphs(text: str) -> list[list[str]]:
    return [sentences(p) for p in re.split(r"\n\s*\n", text) if p.strip()]


def _negated(before: str) -> bool:
    words = [w.lower() for w in WORD.findall(before)][-NEGATION_SPAN:]
    return any(w in NEGATION_WORDS or w.endswith(("n't", "n’t")) for w in words)


def _partial(sentence: str) -> bool:
    return any(a != b for a, b in PARTIAL.findall(sentence))


def _weak_claim(sentence: str) -> bool:
    if CONDITIONAL.match(sentence):
        return False
    for m in WEAK_CLAIM.finditer(sentence):
        before = sentence[:m.start()]
        prev = [w.lower() for w in WORD.findall(before)][-1:]
        if _negated(before) or (prev and prev[0] in NOT_YET_WORDS):
            continue
        if m.group(0).lower() in ("passing", "green") and _partial(sentence):
            continue
        return True
    return False


def is_claim(sentence: str) -> bool:
    """A sentence that says a unit is done: a strong claim word, or an everyday one next to a key in the same sentence."""
    if sentence.rstrip().endswith("?"):
        return False
    if any(not _negated(sentence[:m.start()]) for m in CLAIM.finditer(sentence)):
        return True
    return bool(unit_keys(sentence)) and _weak_claim(sentence)


def claimed_units(text: str) -> set[str]:
    keys = set()
    for para in paragraphs(text):
        for i, s in enumerate(para):
            if not is_claim(s):
                continue
            own = unit_keys(s)
            near = set().union(*(unit_keys(para[j]) for j in (i - 1, i + 1) if 0 <= j < len(para)))
            keys |= own or near
    return keys


def problems(text: str) -> list[str]:
    text = unquoted(normalize(text))
    out = []
    for key in sorted(claimed_units(text)):
        st = _evidence().status(key)
        if not st:
            if not VERIFY_WORDS.search(text):
                continue  # "fixed / works" without a verification word: the close-out step asks for ACs, not every reply
            out.append(f"{key}: claimed done/verified, but tickets/{key}.md has no '## Acceptance criteria' - list the ACs, "
                       f"then prove each with `evidence.py run {key} AC<n> -- <command>` (or `manual` for a human demo log).")
            continue
        bad = {ac: s for ac, s in st.items() if s != "OK"}
        if bad:
            out.append(f"{key}: claim not backed for " + ", ".join(f"{ac} {s}" for ac, s in bad.items())
                       + " - run the proof again, or say exactly what is NOT verified.")
    claims = any(is_claim(s) for s in sentences(text))
    excuses = sorted({m.group(0) for s in sentences(text) if claims and not EVIDENCE.search(s) for m in EXCUSE.finditer(s)})
    if excuses:
        out.append(f"excuse words ({', '.join(excuses)}): show the evidence (the failing run on the base commit, a log) "
                   "or remove the claim - do not wave a failure away.")
    return out


def gate(payload: dict) -> gatekit.Finding | None:
    reply = payload.get("last_assistant_message")
    if not reply:
        if not payload.get("transcript_path"):
            raise gatekit.GateError("the Stop payload has neither last_assistant_message nor transcript_path")
        reply = final_reply(payload["transcript_path"])
    found = problems(str(reply))
    if not found:
        return None
    code = "claim-no-receipts" if any(not f.startswith("excuse") for f in found) else "excuse-no-evidence"
    return code, "CLAIM CHECK:\n- " + "\n- ".join(found)


def main() -> int:
    return gatekit.run(GATE, gate)


if __name__ == "__main__":
    sys.exit(main())
