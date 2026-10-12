---
name: triage-infra-first
description: Use when a test, scenario or regression suite suddenly fails, turns flaky, or shows "was passing, now red" - especially multi-step or follow-up failures that look like lost state - before blaming the latest code change.
---
Adapted from: our triage-infra-first skill + obra/superpowers systematic-debugging ("no root cause" section) + our lessons (a degraded store faked a regression in a clean fix; running the suite in parallel tripped our own rate limiter and faked six failures; an expired test credential looked exactly like lost context).

**Core rule:** degraded infra produces failures that look like code bugs. Rule infra out before touching the diff.

## 1. Health first
Run the deep health check (every dependency: store, cache, queue, external sandbox). Anything degraded -> STOP triaging code; restore it; re-run.
The deep check must probe a WRITE, not just a read: a read-ok / write-fail store (read-only or half-updated credentials) loses every save and looks like lost context on step 2+. Grep the save-failure log event too.

## 2. Read the failure signature
| Signature | Usually |
|---|---|
| Single-step tests pass, step 2+ lose state | durable store / cache down, or an expired credential |
| Many tests empty at step 1 after a long run | upstream sandbox or dependency self-degraded |
| Bursts of 429 / 5xx | your own rate limit or parallelism |
| A class of accounts fails, others pass | test data / account type, not code |
| Fails only in the full run, passes alone | ordering, shared state, resource exhaustion |

List EVERY failing case by name, with its bucket and the failing step - never a lump count. "N empty at step 1 = infra" must not hide real step-2 failures in the same run.

## 3. Re-run in isolation
Restart for a fresh environment; re-run ONLY the failing subset, serially. Refresh credentials the human owns (never read or edit secret files yourself - ask). After the human refreshes credentials / env, RECREATE the container - a plain restart keeps the old env.

## 4. Prove code causation
Still failing on a healthy env? Revert the change (file copy) and re-run. Fails on the old code too -> pre-existing or data drift, not your diff. Only a failure that appears with the change and disappears without it is a regression.

## 5. Keep the suite honest
Record which inputs / accounts actually exercise the path and move the suite onto them; otherwise it goes red from data drift and stops protecting anything.

## Red flags
Triaging code while health is degraded; trusting a baseline from a degraded run; `--parallel` on a rate-limited backend; "it must be my change" without the revert control.

## Example
Six follow-up scenarios failed after a clean fix. Health showed the store degraded (expired credentials). Human refreshed them, env restarted, the six re-run serially -> all passed. No code change needed.

LIVING: add a signature row each time infra fakes a regression.
