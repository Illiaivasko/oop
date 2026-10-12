#!/bin/bash
# Optional status line: git branch + uncommitted count + the top focus line of the live buffer.
# Config (env): AGENT_REPO_DIR, AGENT_WORKSPACE, AGENT_STATE_FILE (same defaults as the other hooks)
# Expand ~, $HOME and $CLAUDE_PROJECT_DIR in $2 (named $1) into REPLY - never eval: a path must not run code.
# An unfilled template placeholder (an uppercase name in angle brackets) leaves a CONFIG ERROR line in REPLY, returns 1.
expand_path() {
  local re='<[A-Z][A-Za-z0-9_-]*>'
  REPLY=$2
  if [[ $REPLY =~ $re ]]; then
    REPLY="CONFIG ERROR: placeholder ${BASH_REMATCH[0]} in $1 - set it in the project settings env (.claude/settings.json)"
    return 1
  fi
  case $REPLY in "~"|"~/"*) REPLY="$HOME${REPLY#\~}" ;; esac
  REPLY=${REPLY//'${CLAUDE_PROJECT_DIR}'/"${CLAUDE_PROJECT_DIR:-}"}
  REPLY=${REPLY//'$CLAUDE_PROJECT_DIR'/"${CLAUDE_PROJECT_DIR:-}"}
  REPLY=${REPLY//'${HOME}'/"$HOME"}
  REPLY=${REPLY//'$HOME'/"$HOME"}
}
expand_path AGENT_WORKSPACE "${AGENT_WORKSPACE:-${CLAUDE_PROJECT_DIR:-$PWD}/.work}" || { echo "$REPLY"; exit 0; }
ws=$REPLY
expand_path AGENT_STATE_FILE "${AGENT_STATE_FILE:-session_state.md}" || { echo "$REPLY"; exit 0; }
state="$ws/$REPLY"
expand_path AGENT_REPO_DIR "${AGENT_REPO_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}" || { echo "$REPLY"; exit 0; }
cd "$REPLY" 2>/dev/null || exit 0
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
FOCUS=$(grep -m1 -iE '^\*\*#1|CURRENT FOCUS|IN PROGRESS' "$state" 2>/dev/null | sed 's/[#*]//g' | cut -c1-60)
echo "${BRANCH} | uncommitted:${DIRTY}${FOCUS:+ | ${FOCUS}}"
