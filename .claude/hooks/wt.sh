#!/bin/sh
# Worktree pipeline helper: one isolated copy + one live server per task, inside the running container.
# Usage:
#   wt.sh new <name> [base]        worktree <REPO>/.worktrees/<name>, branch wt/<name> (base: $WT_BASE)
#   wt.sh test <name>              $WT_TEST_CMD from the worktree (host) - compare with the known failures
#   wt.sh serve <name> <port>      start that worktree's server on 127.0.0.1:<port> inside the container
#   wt.sh scen <port> <scenario>   $WT_SCEN_CMD inside the container against <port> (optional)
#   wt.sh hits <name>              how many $WT_HIT_PATTERN lines reached that worktree's server (the control)
#   wt.sh stop <port>              stop the worktree server on <port> (matches --port N, --port=N, host:N)
#   wt.sh list                     worktrees + running worktree servers
#   wt.sh land <name>              cherry-pick wt/<name> commits onto $WT_BASE (main tree; says so if it switches
#                                  the main tree's branch), then restart main + health
#   wt.sh rm <name>                remove worktree + branch; refuses if it has uncommitted or unlanded work
#
# Names are [A-Za-z0-9._-], ports digits; nothing from the arguments reaches a shell inside the container unquoted.
# Config (env; ~, $HOME and $CLAUDE_PROJECT_DIR are expanded as in the hooks, nothing is evaluated).
# Defaults are neutral; set them in the project profile.
#   AGENT_ROOT       project root                                     (default: cwd)
#   AGENT_REPO_DIR   its git repo                                     (default: $AGENT_ROOT)
#   AGENT_CONTAINER  the running app container                        (required for serve/scen/hits/stop)
#   AGENT_SERVICE    its compose service, restarted by `land`         (default: $AGENT_CONTAINER)
#   WT_BASE          base branch for new worktrees and `land`         (default: main)
#   WT_MOUNT         where AGENT_REPO_DIR is mounted in the container (default: /app)
#   WT_MAIN_PORT     port of the main (non-worktree) server           (default: 8000)
#   WT_HEALTH_PATH   health path that must return 200                 (default: /health)
#   WT_SERVER_CMD    server start command; {dir} = worktree dir in the container, {port} = port (required for serve)
#   WT_TEST_CMD      test command run inside the worktree on the host (default: make test)
#   WT_SCEN_CMD      scenario command in the container; {url} = http://127.0.0.1:<port>, {name} = scenario
#   WT_HIT_PATTERN   server log text counted by `hits`, one line per request (default: "POST ")
#   WT_COMPOSE_FILE  compose file `land` restarts the service with     (default: $AGENT_ROOT/docker-compose.yml)
set -e
replace_all() {  # $1 text, $2 needle, $3 replacement -> REPLY
  REPLY= _t=$1
  while :; do
    case $_t in *"$2"*) REPLY=$REPLY${_t%%"$2"*}$3; _t=${_t#*"$2"} ;; *) break ;; esac
  done
  REPLY=$REPLY$_t
}
expand_path() {  # $1 var name, $2 value -> stdout; a template placeholder is a CONFIG ERROR
  case $2 in *"<"[A-Z]*">"*)
    echo "CONFIG ERROR: placeholder $(printf '%s' "$2" | grep -oE '<[A-Z][A-Za-z0-9_-]*>' | head -1) in $1 - set it in the project env" >&2
    exit 1 ;;
  esac
  REPLY=$2
  case $REPLY in "~"|"~/"*) REPLY="$HOME${REPLY#?}" ;; esac
  replace_all "$REPLY" '${CLAUDE_PROJECT_DIR}' "${CLAUDE_PROJECT_DIR:-}"
  replace_all "$REPLY" '$CLAUDE_PROJECT_DIR' "${CLAUDE_PROJECT_DIR:-}"
  replace_all "$REPLY" '${HOME}' "$HOME"; replace_all "$REPLY" '$HOME' "$HOME"
  printf '%s' "$REPLY"
}
ROOT=$(expand_path AGENT_ROOT "${AGENT_ROOT:-$PWD}")
REPO=$(expand_path AGENT_REPO_DIR "${AGENT_REPO_DIR:-$ROOT}")
C="${AGENT_CONTAINER:-}"
SVC="${AGENT_SERVICE:-$C}"
BASE="${WT_BASE:-main}"
MOUNT="${WT_MOUNT:-/app}"
MAIN_PORT="${WT_MAIN_PORT:-8000}"
HEALTH_PATH="${WT_HEALTH_PATH:-/health}"
TEST_CMD="${WT_TEST_CMD:-make test}"
HIT_PATTERN="${WT_HIT_PATTERN:-POST }"
COMPOSE_FILE=$(expand_path WT_COMPOSE_FILE "${WT_COMPOSE_FILE:-$ROOT/docker-compose.yml}")
cmd=$1; shift || true

need() { [ -n "$2" ] || { echo "set $1 first (see the header of $0)" >&2; exit 1; }; }
valid() {  # $1 what, $2 value, $3 extended regex it must match in full
  printf '%s' "$2" | grep -qxE "$3" || { echo "invalid $1 '$2' (allowed: $3)" >&2; exit 1; }
}
name_ok() { valid name "$1" '[A-Za-z0-9][A-Za-z0-9._-]*'; }
port_ok() { valid port "$1" '[0-9]{1,5}'; }
fill() {  # template, dir, port, url, name - values are validated, so they hold no sed or shell metacharacters
  replace_all "$1" "{dir}" "$2"; replace_all "$REPLY" "{port}" "$3"
  replace_all "$REPLY" "{url}" "$4"; replace_all "$REPLY" "{name}" "$5"; printf '%s' "$REPLY"
}
valid WT_MOUNT "$MOUNT" '/[A-Za-z0-9._/-]*'

health() {
  docker exec "$C" python3 -c 'import urllib.request,sys;sys.exit(0 if urllib.request.urlopen("http://127.0.0.1:"+sys.argv[1]+sys.argv[2],timeout=2).status==200 else 1)' "$1" "$HEALTH_PATH" 2>/dev/null
}

case "$cmd" in
new)
  name=$1; base=${2:-$BASE}
  name_ok "$name"; valid base "$base" '[A-Za-z0-9._/][A-Za-z0-9._/~^-]*'
  grep -qx '.worktrees/' "$REPO/.git/info/exclude" || echo '.worktrees/' >> "$REPO/.git/info/exclude"
  git -C "$REPO" worktree add -q "$REPO/.worktrees/$name" -b "wt/$name" "$base"
  echo "worktree $REPO/.worktrees/$name on wt/$name from $(git -C "$REPO" rev-parse --short "$base")"
  ;;
test)
  name_ok "$1"
  cd "$REPO/.worktrees/$1"
  rc=0; out=$(sh -c "$TEST_CMD" 2>&1) || rc=$?
  printf '%s\n' "$out" | tail -4
  [ "$rc" = 0 ] || echo "test command failed (exit $rc)" >&2
  exit "$rc"
  ;;
serve)
  need AGENT_CONTAINER "$C"; need WT_SERVER_CMD "${WT_SERVER_CMD:-}"
  name=$1; port=$2; dir="$MOUNT/.worktrees/$name"
  name_ok "$name"; port_ok "$port"
  # an old server on the port answers the health check, so refuse instead of silently testing the wrong code
  if health "$port"; then echo "port $port is already served (see: wt.sh list) - wt.sh stop $port first" >&2; exit 1; fi
  docker exec -d -w "$dir" "$C" sh -c "$(fill "$WT_SERVER_CMD" "$dir" "$port") > /tmp/wt_$name.log 2>&1"
  for i in 1 2 3 4 5 6 7 8 9 10; do health "$port" && { echo "wt/$name serving on :$port"; exit 0; }; sleep 2; done
  echo "wt/$name did not come up on :$port - see: docker exec $C cat /tmp/wt_$name.log" >&2; exit 1
  ;;
scen)
  need AGENT_CONTAINER "$C"; need WT_SCEN_CMD "${WT_SCEN_CMD:-}"
  port=$1; scen=$2
  port_ok "$port"; valid scenario "$scen" '[A-Za-z0-9._:/=,+-]+'
  docker exec -i "$C" sh -c "$(fill "$WT_SCEN_CMD" "" "$port" "http://127.0.0.1:$port" "$scen")"
  ;;
hits)
  need AGENT_CONTAINER "$C"
  name_ok "$1"
  docker exec "$C" sh -c 'grep -cF -- "$1" "/tmp/wt_$2.log" || true' sh "$HIT_PATTERN" "$1"
  ;;
stop)
  need AGENT_CONTAINER "$C"
  port=${1#--port=}; port_ok "$port"
  docker exec "$C" python3 -c '
import os, re, signal, sys
port, proc, me, stopped = sys.argv[1], os.environ.get("WT_PROC", "/proc"), os.getpid(), 0
pat = re.compile(rb"(^|[=:])" + port.encode() + rb"$")
for p in os.listdir(proc):
    if p.isdigit() and int(p) != me:
        try:
            cl = open(f"{proc}/{p}/cmdline", "rb").read().split(b"\0")
        except OSError:
            continue
        if any(b".worktrees/" in a for a in cl) and any(pat.search(a) for a in cl):
            os.kill(int(p), signal.SIGTERM); print("stopped", p); stopped += 1
if not stopped:
    sys.exit(f"no worktree server on :{port}")' "$port"
  ;;
list)
  git -C "$REPO" worktree list
  [ -z "$C" ] || docker exec "$C" sh -c 'for p in /proc/[0-9]*; do tr "\0" " " < "$p/cmdline" 2>/dev/null; echo; done | grep -o -- "$1/\.worktrees/.*" | grep -v "\[" | sort -u' sh "$MOUNT"
  ;;
land)
  name=$1; name_ok "$name"
  [ -z "$(git -C "$REPO" status --porcelain --untracked-files=no)" ] || { echo "main tree has uncommitted changes - land refused" >&2; exit 1; }
  commits=$(git -C "$REPO" cherry "$BASE" "wt/$name" | sed -n "s/^+ //p")
  [ -n "$commits" ] || { echo "nothing to land from wt/$name"; exit 0; }
  cur=$(git -C "$REPO" rev-parse --abbrev-ref HEAD)
  if [ "$cur" != "$BASE" ]; then
    echo "land: switching the main tree ($REPO) from branch '$cur' to '$BASE' - git checkout $cur to go back"
    git -C "$REPO" checkout -q "$BASE"
  fi
  for c in $commits; do git -C "$REPO" cherry-pick "$c" >/dev/null || { echo "conflict on $c - resolve, or git cherry-pick --abort" >&2; exit 1; }; echo "landed $(git -C "$REPO" log --oneline -1)"; done
  [ -n "$SVC" ] || { echo "landed; no AGENT_SERVICE set - restart the main server yourself, then lint + tests + live check"; exit 0; }
  docker compose -f "$COMPOSE_FILE" restart "$SVC" >/dev/null 2>&1
  for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -w "%{http_code}" "http://localhost:$MAIN_PORT$HEALTH_PATH" | grep -q 200 && { echo "main healthy - now lint + tests + live check on :$MAIN_PORT"; exit 0; }; sleep 2; done
  echo "main not healthy after restart" >&2; exit 1
  ;;
rm)
  name=$1; name_ok "$name"; wt="$REPO/.worktrees/$name"
  [ -z "$(git -C "$wt" status --porcelain)" ] || { echo "wt/$name has uncommitted changes - refused" >&2; exit 1; }
  left=$(git -C "$REPO" cherry "$BASE" "wt/$name" | grep -c "^+" || true)
  [ "$left" = "0" ] || [ "$2" = "--discard" ] || { echo "wt/$name has $left commit(s) not on $BASE - refused (add --discard only with the lead's OK)" >&2; exit 1; }
  git -C "$REPO" worktree remove "$wt" && git -C "$REPO" branch -D "wt/$name" >/dev/null && echo "removed wt/$name"
  ;;
*)
  sed -n 2,27p "$0"; exit 1
  ;;
esac
