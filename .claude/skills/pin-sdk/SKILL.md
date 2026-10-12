---
name: pin-sdk
description: Use when touching a dependency manifest (requirements.txt, package.json, go.mod, ...) or bumping any SDK. An unpinned dependency passes locally but breaks the freshly built image.
---
Adapted from: our pin-sdk skill (an open `>=` on a fast-moving SDK client let a no-cache CI build pull a newer major that removed an attribute and rejected a kwarg - every request failed on `<ENV>` while the local cached env was fine).

## Rules
- Pin every runtime-critical SDK to an EXACT version (or a tight compatible range) - especially fast-drifting API clients and their tracing / wrapper libraries. No open `>=` without an upper bound.
- The pinned version is the one verified working - read it from the local env (`pip freeze`, the lockfile), don't guess.
- Libraries that wrap each other are pinned as a compatible PAIR.
- "Works locally" is not proof: the deploy installs fresh from the specifiers.
- Bumping: verify on a fresh install (throwaway venv / no-cache build) and read the changelog for removed params and attributes.

## Triage
Health endpoint 200 but every real request 500s, and the same commit works locally = a deploy-time dependency / env difference. Get the container traceback before blaming code - it names the exact SDK, attribute or kwarg.
