#!/usr/bin/env python3
"""
Escape-hatch builtins for the declarative hook engine.

Holds two allowlist dicts referenced by string name from nudge rules:
- HANDLERS: full-fragment handlers that own their own bypass logic
  (improve, workflow). A rule with ``"handler": "improve"`` runs improve(data).
- MATCHERS: builtin criteria predicates (saved_workflow_exists). A rule with
  ``"criteria": {"builtin": "saved_workflow_exists"}`` runs the named matcher.

Named by string only. The engine never uses eval/importlib/getattr-on-path:
an unknown name is a load-time skip, never an arbitrary import. Functions
resolve cwd/HOME at call time (not module load) so callers and tests can
relocate them via monkeypatch.

This module is deliberately NOT named ``builtins``: the stdlib ``builtins``
module is loaded into sys.modules before any user code runs, so a local
builtins.py would be permanently shadowed and never importable.
"""
import re
from pathlib import Path

# --- improve: prompt-clarity evaluation wrapper -----------------------------

_EVALUATION_WRAPPER = """PROMPT EVALUATION

Original user request: "{prompt}"

EVALUATE: Is this prompt clear enough to execute, or does it need enrichment?

PROCEED IMMEDIATELY if:
- Detailed/specific OR you have sufficient context OR can infer intent

ONLY USE SKILL if genuinely vague (e.g., "fix the bug" with no context):
- If vague:
  1. First, preface with brief note: "Hey! The Prompt Improver Hook flagged your prompt as a bit vague because [specific reason: ambiguous scope/missing context/unclear target/etc]."
  2. Then use the prompt-improver skill to research and generate clarifying questions
- The skill will guide you through research, question generation, and execution
- Trust user intent by default. Check conversation history before using the skill.

If clear, proceed with the original request. If vague, invoke the skill."""


def improve(data):
    """Return the prompt-evaluation fragment for a UserPromptSubmit payload.

    Always returns a string. Bypass prefixes short-circuit the wrapper:
    - ``*`` strips the prefix and returns the bare prompt
    - ``/`` (slash commands) and ``#`` (memorize) pass through unchanged
    """
    prompt = data.get("prompt", "")
    if not isinstance(prompt, str):
        prompt = ""

    if prompt.startswith("*"):
        return prompt[1:].strip()
    if prompt.startswith("/") or prompt.startswith("#"):
        return prompt

    # Escape backslashes first, then double-quotes, so the prompt embeds
    # safely inside the wrapper's quoted "Original user request" line.
    escaped = prompt.replace("\\", "\\\\").replace('"', '\\"')
    return _EVALUATION_WRAPPER.format(prompt=escaped)


# --- workflow: model-routing guidance for dynamic-workflow requests ---------

# Leads with a condition so false positives self-cancel at the model: the hook
# is a high-recall regex filter with no workflow signal in its input, so it
# cannot distinguish "build a workflow" from "fix the CI workflow file". That
# residual ambiguity is intentionally deferred to the model reading the context.
_CORE_GUIDANCE = (
    "If this prompt will run as a dynamic workflow: "
    "enter plan mode first and show the plan before running. "
    "For token efficiency, use models suited to each stage: "
    "reserve the session model for planning, strategy, and orchestration; "
    "route implementation to a smaller, cheaper model. "
    "If this is not a workflow, ignore this guidance."
)

# Appended only for /effort ultracode, which makes every task a workflow.
_ULTRACODE_CLAUSE = " Under ultracode, apply this routing to every task this session."

_WORKFLOW_KEYWORD = re.compile(r"\bworkflows?\b", re.IGNORECASE)
_DEEP_RESEARCH = re.compile(r"^/deep-research\b", re.IGNORECASE)
_EFFORT_ULTRACODE = re.compile(r"^/effort\s+ultracode\b", re.IGNORECASE)
# Strict leading-token capture; path-traversal input fails to match.
_WORKFLOW_NAME = re.compile(r"^/([A-Za-z0-9_:-]+)")


def saved_workflow_exists(stripped):
    """True if the leading /name token matches a file in a known workflow dir.

    Resolves cwd and HOME at call time so tests can relocate both via
    monkeypatch. Non-slash input and path-traversal input never match.
    """
    match = _WORKFLOW_NAME.match(stripped)
    if not match:
        return False
    name = match.group(1)
    workflow_dirs = (
        Path.cwd() / ".claude" / "workflows",
        Path.home() / ".claude" / "workflows",
    )
    for directory in workflow_dirs:
        try:
            if any(directory.glob(f"{name}.*")):
                return True
        except OSError:
            continue
    return False


def workflow(data):
    """Return model-routing guidance when a dynamic workflow is requested.

    Returns None (silent) for non-workflow prompts and for the ``*``/``#``
    bypass prefixes. The natural-language keyword search runs on non-slash
    prompts only; slash prompts keep explicit detection (/deep-research,
    /effort ultracode, saved-workflow scan), so run-management commands like
    /workflows do not keyword-trigger. The saved-workflow scan is gated behind
    a leading "/" so non-slash prompts do zero filesystem I/O.
    """
    prompt = data.get("prompt", "")
    if not isinstance(prompt, str) or not prompt:
        return None

    stripped = prompt.lstrip()

    # * (explicit bypass) and # (memorize) suppress guidance entirely.
    if stripped.startswith("*") or stripped.startswith("#"):
        return None

    is_ultracode = bool(_EFFORT_ULTRACODE.match(stripped))
    triggered = (
        is_ultracode
        or (not stripped.startswith("/") and bool(_WORKFLOW_KEYWORD.search(prompt)))
        or bool(_DEEP_RESEARCH.match(stripped))
        or (stripped.startswith("/") and saved_workflow_exists(stripped))
    )

    if not triggered:
        return None

    context = _CORE_GUIDANCE
    if is_ultracode:
        context += _ULTRACODE_CLAUSE
    return context


# --- allowlists referenced by string name from nudge rules ------------------

HANDLERS = {
    "improve": improve,
    "workflow": workflow,
}

MATCHERS = {
    "saved_workflow_exists": saved_workflow_exists,
}
