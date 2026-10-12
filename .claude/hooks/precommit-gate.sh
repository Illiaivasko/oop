#!/bin/bash
# Compatibility shim for installs wired to the .sh name: the gate is precommit-gate.py (same dir).
exec python3 "$(dirname "$0")/precommit-gate.py"
