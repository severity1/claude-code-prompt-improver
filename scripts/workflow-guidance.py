#!/usr/bin/env python3
"""
Workflow Guidance Hook
Injects model-routing and plan-mode-first HITL guidance when a dynamic
workflow is requested, via UserPromptSubmit.
"""
import json
import re
import sys
from pathlib import Path

# Static guidance directed at Claude (the context reader).
# Leads with a condition so false positives self-cancel at the model: the hook
# is a high-recall regex filter with no workflow signal in its input, so it
# cannot distinguish "build a workflow" from "fix the CI workflow file". That
# residual ambiguity is intentionally deferred to the model reading the context.
CORE_GUIDANCE = (
    "If this prompt will run as a dynamic workflow: "
    "enter plan mode first and show the plan before running. "
    "For token efficiency, use models suited to each stage: "
    "reserve the session model for planning, strategy, and orchestration; "
    "route implementation to a smaller, cheaper model. "
    "If this is not a workflow, ignore this guidance."
)

# Appended only for /effort ultracode, which makes every task a workflow.
ULTRACODE_CLAUSE = " Under ultracode, apply this routing to every task this session."

WORKFLOW_KEYWORD = re.compile(r"\bworkflows?\b", re.IGNORECASE)
DEEP_RESEARCH = re.compile(r"^/deep-research\b", re.IGNORECASE)
EFFORT_ULTRACODE = re.compile(r"^/effort\s+ultracode\b", re.IGNORECASE)
# Strict leading-token capture; path-traversal input fails to match.
WORKFLOW_NAME = re.compile(r"^/([A-Za-z0-9_:-]+)")

WORKFLOW_DIRS = (
    Path.cwd() / ".claude" / "workflows",
    Path.home() / ".claude" / "workflows",
)


def saved_workflow_exists(stripped):
    """Check known workflow dirs for a file matching the leading /name token."""
    match = WORKFLOW_NAME.match(stripped)
    if not match:
        return False
    name = match.group(1)
    for directory in WORKFLOW_DIRS:
        try:
            if any(directory.glob(f"{name}.*")):
                return True
        except OSError:
            continue
    return False


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if not isinstance(input_data, dict):
        sys.exit(0)

    prompt = input_data.get("prompt", "")
    if not isinstance(prompt, str) or not prompt:
        sys.exit(0)

    stripped = prompt.lstrip()

    # Explicit bypass with * prefix
    if stripped.startswith("*"):
        sys.exit(0)

    # Memorize feature (# prefix) - mirrors improve-prompt.py's # bypass so a
    # prompt like "# remember the deploy workflow doc" does not false-trigger.
    if stripped.startswith("#"):
        sys.exit(0)

    is_ultracode = bool(EFFORT_ULTRACODE.match(stripped))

    # The natural-language keyword search runs on non-slash prompts only.
    # Slash prompts keep their explicit detection (/deep-research,
    # /effort ultracode, saved-workflow scan), so run-management commands like
    # /workflows no longer keyword-trigger. The saved-workflow scan is gated
    # behind a leading "/" so non-slash prompts do zero filesystem I/O.
    triggered = (
        is_ultracode
        or (not stripped.startswith("/") and bool(WORKFLOW_KEYWORD.search(prompt)))
        or bool(DEEP_RESEARCH.match(stripped))
        or (stripped.startswith("/") and saved_workflow_exists(stripped))
    )

    if not triggered:
        sys.exit(0)

    context = CORE_GUIDANCE
    if is_ultracode:
        context += ULTRACODE_CLAUSE

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
