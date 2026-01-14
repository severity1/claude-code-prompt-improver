#!/bin/bash
# Cross-platform wrapper to invoke Python with the correct interpreter
# - Linux/macOS: uses python3
# - Windows (Git Bash/MSYS/Cygwin): uses py -3

SCRIPT_DIR="$(dirname "$0")"
HOOK_SCRIPT="$SCRIPT_DIR/improve-prompt.py"

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OS" == "Windows_NT" ]]; then
    py -3 -u "$HOOK_SCRIPT"
else
    python3 -u "$HOOK_SCRIPT"
fi
