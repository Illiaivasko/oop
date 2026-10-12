#!/bin/bash
# SessionStart hook: load the START-HERE file + the top of the live buffer into the new session.
# Config (env): AGENT_WORKSPACE (default $CLAUDE_PROJECT_DIR/.work), AGENT_STATE_FILE (default session_state.md)
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
cat "$ws/README.md" 2>/dev/null
if [ -s "$ws/improve/gave-up.md" ]; then
  printf '\n=== GATES THAT GAVE UP (review with the human, newest last) ===\n'
  tail -5 "$ws/improve/gave-up.md"
fi
# first run in a project: the agent must set itself up for THIS project before any other work
if [ ! -f "$ws/improve/setup-done.md" ]; then
  printf '\n=== FIRST RUN: PROJECT SETUP NOT DONE ===\nBefore any other task, load the improve-setup skill in SETUP mode and run it: ask the onboarding questions, analyse this workspace, search ready-made skills/tools/approaches, propose the project layer, build only what the human approves, then write %s.\n' "$ws/improve/setup-done.md"
fi
printf '\n=== CURRENT FOCUS (%s, top) ===\n' "$(basename "$state")"
head -45 "$state" 2>/dev/null
exit 0
