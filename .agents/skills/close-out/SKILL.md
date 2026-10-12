---
name: close-out
description: Use whenever a unit of work (ticket, issue, task) is being closed, moved to testing / review / done, or given a status or verification comment - one unit OR a batch ("close these", "what can we close", "move to done", "status comment"). MANDATORY before drafting any close-out comment; notes and statuses are never enough.
---
Adapted from: our close-ticket skill + obra/superpowers verification-before-completion and finishing-a-development-branch + our lessons (a batch drafted from notes marked two units "close now" that depended on a release, and missed an acceptance point on two others; comments ignored the human's posted format; three demos handed over at once).

**Core rule:** close from the LIVE unit and fresh evidence, never from notes - one unit at a time, in the human's own format.

## 0. Batch = N close-outs
Run steps 1-3 for EACH unit before drafting ANY comment. Demos go ONE at a time: one demo -> STOP -> human runs it -> validate -> comment -> next.

## 1. Re-read the full LIVE unit
Fetch the current description, EVERY comment, status and attachments (read-only). Write down: (a) the reported problem, (b) EVERY acceptance point, (c) anything in comments that changed the ask. Live unit contradicts your notes -> the live unit wins.

## 2. Demo or not?
- User-facing behaviour -> demo (step 3).
- No demo when it is not reproducible, not ours, infra, a policy decision, a pure refactor or a doc. Say WHY, verify by the right means (code trace, test, owner), go to step 4.

## 3. Demo handshake - STOP-and-WAIT gate
a. From the live acceptance points, form the SINGLE smallest demo on the current build: exact inputs / clicks + a control that must still work.
b. Hand it over, then STOP. Do not draft, do not claim "verified".
c. When the result comes back, validate point by point against the acceptance list, quoting what the evidence shows. Any point fails or is unclear -> not closed.
Your own local probe is preparation, never the close evidence for a user-facing fix.

## 4. Draft the comment - MATCH THE HUMAN'S POSTED FORMAT
Before drafting, read 2-3 comments the human actually posted on similar units and copy their shape, length, tone and opener. Default when none exist: where it is -> what changed in user terms -> the concrete example from the demo -> the control that still works -> "Verified on <ENV>." Plain words, no jargon, no file paths. The human posts it - NEVER write to the tracker yourself.

## 5. Record + remind
Update the unit record (Problem / Root cause / Our action / Verified / Follow-ups / Source). Remind the human to move the status - do not transition it yourself unless explicitly told. Finishing a branch too? Full suite green first, then present options (merge / open a review / keep); never push or merge without an explicit instruction.

## Red flags
"Notes say done"; a status sweep over 8 units; a comment before the demo result; several demos at once; your own format instead of theirs.

## Example
"Fixed and on staging. Saving a profile with an empty optional field no longer shows an error - it now saves and shows the confirmation. Profiles with all fields filled still save as before. Verified on staging."

LIVING: replace the example with the human's latest real posted comment.
