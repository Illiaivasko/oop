#!/bin/bash
# PreCompact hook: snapshot the live buffer and remind the agent to refresh its top hand-off block.
# Config (env): AGENT_WORKSPACE (default $CLAUDE_PROJECT_DIR/.work), AGENT_STATE_FILE (default session_state.md),
#               AGENT_STATE_BACKUPS how many backups to keep (default 20)
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
keep=${AGENT_STATE_BACKUPS:-20}
[[ $keep =~ ^[1-9][0-9]*$ ]] || keep=20
dir="$ws/state-backups"
if [ -f "$state" ] && mkdir -p "$dir" && cp "$state" "$dir/state-$(date +%Y%m%d-%H%M%S).md"; then
  ls -1t "$dir"/state-*.md | tail -n +$((keep + 1)) | while IFS= read -r old; do rm -f -- "$old"; done
  saved="A timestamped backup was saved to state-backups/ (the newest $keep are kept)."
else
  saved="NO backup was made: $state is missing or could not be copied."
fi
echo "PRECOMPACT: context is compacting. Make sure the TOP hand-off block of $(basename "$state") is current (that is what survives). $saved"
exit 0
