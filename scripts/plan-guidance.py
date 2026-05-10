#!/usr/bin/env python3
"""
Plan Mode Guidance Hook
Injects readability guidance when entering plan mode via PreToolUse on EnterPlanMode.
"""
import json
import sys

# Consume stdin (required by hook protocol, but content is unused)
try:
    json.load(sys.stdin)
except (json.JSONDecodeError, ValueError):
    pass

guidance = (
    "Plan readability guidance: "
    "Keep the problem statement - omit decision history "
    "(rejected approaches, revision rationale, prior iterations). "
    "On plan revisions, rewrite the entire plan clean - "
    "do not append revision notes or annotate what changed. "
    "Use one action per step with file paths as anchors (e.g., src/auth.ts:42). "
    "Favor terse action steps over explanatory prose."
)

output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": guidance
    }
}

print(json.dumps(output))
sys.exit(0)
