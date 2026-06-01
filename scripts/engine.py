#!/usr/bin/env python3
"""
Declarative hook engine entry point.

Usage: engine.py <EventName>   (stdin = hook JSON payload)

Reads stdin once, runs the event's rules, merges inject_context fragments by
priority with a blank-line join, emits one hookSpecificOutput object, and
exits 0 on every path. A missing/unknown event or an event with no rules is a
clean no-op that never reads stdin.
"""
import json
import sys

import nudge_builtins
from rules import rules_for

# Where each criteria.match_target reads its value from in the payload. A
# tuple value is a nested path walked dict-by-dict (e.g. tool_input.command for
# PreToolUse/Bash); a string value is a top-level key.
_TARGET_KEYS = {
    "prompt": "prompt",
    "tool_name": "tool_name",
    "agent_type": "agent_type",
    "command": ("tool_input", "command"),
}


def _read_payload():
    """Read stdin once; treat empty or invalid JSON as an empty payload."""
    try:
        raw = sys.stdin.read()
    # Intentionally broad: reading a closed stream raises ValueError, and this
    # runs after the load-rules guard in main(), so any escape here would
    # reintroduce a non-zero-exit path. Every failure mode falls back to {}.
    except (OSError, ValueError):
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except ValueError:  # JSONDecodeError subclasses ValueError
        return {}
    return data if isinstance(data, dict) else {}


def _target_value(data, match_target):
    """Return the string the criteria matches against, for the given target.

    Unknown targets fall back to the prompt key. A tuple key is walked as a
    nested path, stopping (and returning "") at any non-dict level, so a
    missing tool_input is just an empty match rather than a crash.
    """
    key = _TARGET_KEYS.get(match_target, "prompt")
    if isinstance(key, tuple):
        value = data
        for part in key:
            value = value.get(part, "") if isinstance(value, dict) else ""
    else:
        value = data.get(key, "")
    return value if isinstance(value, str) else ""


def _bypassed(target_value, match_target, bypass):
    """Default policy: suppress prompt-targeted rules on */#/empty input.

    Bypass applies only to prompt-targeted criteria; tool_name/agent_type
    targets and a rule with ``"bypass": "none"`` are never suppressed here.
    """
    if bypass == "none" or match_target != "prompt":
        return False
    stripped = target_value.lstrip()
    return not stripped or stripped.startswith("*") or stripped.startswith("#")


def _passes_criteria(data, criteria):
    """Evaluate a compiled criteria block against the payload."""
    if not criteria:
        return True

    match_target = criteria.get("match_target", "prompt")
    value = _target_value(data, match_target)

    if criteria.get("non_slash") and value.lstrip().startswith("/"):
        return False

    builtin = criteria.get("builtin")
    if builtin:
        matcher = nudge_builtins.MATCHERS.get(builtin)
        if matcher is None or not matcher(value.lstrip()):
            return False

    match = criteria.get("match")
    if match and not any(p.search(value) for p in match):
        return False

    exclude = criteria.get("exclude")
    if exclude and any(p.search(value) for p in exclude):
        return False

    return True


def _render_action(data, action, match_target="prompt"):
    """Render an inject_context action into a text fragment (or '' if empty).

    Joins the base text lines, then appends each append_when clause whose
    match fires against the rule's match_target value (defaults to prompt).
    """
    lines = list(action.get("text", []))
    fragment = "\n".join(lines)

    value = _target_value(data, match_target)
    for clause in action.get("append_when", []):
        patterns = clause.get("match", [])
        if any(p.search(value) for p in patterns):
            fragment += " " + " ".join(clause.get("text", []))

    return fragment


def _fragment_for(data, rule):
    """Return this rule's fragment, or None if it does not fire."""
    if "handler" in rule:
        handler = nudge_builtins.HANDLERS.get(rule["handler"])
        return handler(data) if handler else None

    criteria = rule.get("criteria")
    match_target = criteria.get("match_target", "prompt") if criteria else "prompt"
    bypass = rule.get("bypass", "default")

    # Criteria-less rules always fire; only criteria rules consult bypass.
    if criteria is not None:
        value = _target_value(data, match_target)
        if _bypassed(value, match_target, bypass):
            return None
        if not _passes_criteria(data, criteria):
            return None

    return _render_action(data, rule.get("action", {}), match_target)


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else None
    if not event:
        sys.exit(0)

    try:
        rules = rules_for(event)
    except Exception as exc:  # noqa: BLE001 - load failure must still exit 0
        print(f"[engine] failed to load rules for {event}: {exc}", file=sys.stderr)
        sys.exit(0)
    if not rules:
        sys.exit(0)

    data = _read_payload()

    fragments = []
    for rule in rules:
        try:
            fragment = _fragment_for(data, rule)
        except Exception as exc:  # noqa: BLE001 - one bad rule must not suppress others
            print(f"[engine] rule {rule.get('id', '?')} raised: {exc}", file=sys.stderr)
            continue
        if fragment:
            priority = rule.get("priority", 100)
            fragments.append((priority, fragment))

    if not fragments:
        sys.exit(0)

    fragments.sort(key=lambda pair: pair[0])
    merged = "\n\n".join(fragment for _, fragment in fragments)

    output = {
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": merged,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
