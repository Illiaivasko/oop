#!/bin/bash
# Warn (never block) when a local dependency is down before a local probe/test, so a degraded stack
# is not mistaken for a code failure. Called by precommit-gate.py on AGENT_PROBE_CMD_RE.
# Config (env): AGENT_HEALTH_URL  deep health endpoint returning {"status": "ok", "checks": {"<dep>": "ok", ...}}
[ -z "${AGENT_HEALTH_URL:-}" ] && exit 0
re='<[A-Z][A-Za-z0-9_-]*>'
if [[ $AGENT_HEALTH_URL =~ $re ]]; then
  echo "CONFIG ERROR: placeholder ${BASH_REMATCH[0]} in AGENT_HEALTH_URL - set it in the project settings env (.claude/settings.json)"; exit 0
fi
case $AGENT_HEALTH_URL in
  http://*|https://*) ;;
  *) echo "CONFIG ERROR: AGENT_HEALTH_URL must start with http:// or https:// (got: $AGENT_HEALTH_URL)"; exit 0 ;;
esac
h=$(curl -s --max-time 8 -- "$AGENT_HEALTH_URL" 2>/dev/null)
[ -z "$h" ] && { echo "HEALTH PREFLIGHT: $AGENT_HEALTH_URL unreachable - is the app up (or reloading after an edit)?"; exit 0; }
printf '%s' "$h" | python3 -c 'import sys,json
d=json.load(sys.stdin); c=d.get("checks") or {}
down={k:v for k,v in c.items() if v!="ok"}
if d.get("status")!="ok" or down:
    print("HEALTH PREFLIGHT WARN: status="+str(d.get("status"))+" down="+str(down or c)+" - a local probe/test may give FALSE failures (a down store = state not persisted, looks like lost context). Restore it first.")' 2>/dev/null
exit 0
