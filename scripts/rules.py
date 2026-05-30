#!/usr/bin/env python3
"""
Rule layer for the declarative hook engine.

Owns the JSON loader, validate_rule, the event->capability matrix, and
rules_for(event). Rules live in per-event subdirectories under nudges/
(nudges/<EventName>/*.json); the parent directory must match each rule's
event field. Each file is a single rule object (or an array of rule objects).
Invalid rows are skipped with a stderr note; loading never raises into the
engine.

Regexes are compiled once per dispatched event in rules_for, not at file
load, so an event with no rules costs no compilation.
"""
import copy
import json
import re
import sys
from pathlib import Path

import nudge_builtins

NUDGES_DIR = Path(__file__).parent.parent / "nudges"

# The v1 action vocabulary. The engine can dispatch any event, but only
# inject_context is implemented; block/permission actions are a future type.
CAPABILITY_MATRIX = {
    "UserPromptSubmit": {"inject_context"},
    "PreToolUse": {"inject_context"},
    "SubagentStart": {"inject_context"},
}

_FLAG_MAP = {
    "ignorecase": re.IGNORECASE,
    "multiline": re.MULTILINE,
    "dotall": re.DOTALL,
}


def _compile_flags(flags):
    """OR together the re flags named in a criteria.flags array."""
    result = 0
    for name in flags or []:
        result |= _FLAG_MAP.get(name, 0)
    return result


def _check_regexes(patterns, flags, errors, label):
    """Append an error for each uncompilable pattern in patterns."""
    for pattern in patterns:
        try:
            re.compile(pattern, flags)
        except re.error as exc:
            errors.append(f"{label} regex {pattern!r} does not compile: {exc}")


def validate_rule(row, seen_ids=None):
    """Return a list of validation errors for a raw rule row (empty = valid).

    Enforces: required id/event, known event, action XOR handler, action type
    legal for the event, compilable criteria/append_when regexes, allowlisted
    criteria.builtin and handler names, and unique id within seen_ids.
    """
    errors = []
    seen_ids = seen_ids or set()

    rule_id = row.get("id")
    if not rule_id or not isinstance(rule_id, str):
        errors.append("missing or non-string 'id'")
    elif rule_id in seen_ids:
        errors.append(f"duplicate id {rule_id!r}")

    event = row.get("event")
    if not event:
        errors.append("missing 'event'")
    elif event not in CAPABILITY_MATRIX:
        errors.append(f"unknown event {event!r}")

    has_action = "action" in row
    has_handler = "handler" in row
    if has_action and has_handler:
        errors.append("rule has both 'action' and 'handler' (exactly one allowed)")
    elif not has_action and not has_handler:
        errors.append("rule has neither 'action' nor 'handler'")

    if has_handler:
        handler = row.get("handler")
        if handler not in nudge_builtins.HANDLERS:
            errors.append(f"unknown handler {handler!r}")

    if has_action:
        action = row.get("action") or {}
        action_type = action.get("type")
        legal = CAPABILITY_MATRIX.get(event, set())
        if action_type not in legal:
            errors.append(
                f"action type {action_type!r} not legal for event {event!r}"
            )
        for clause in action.get("append_when", []):
            _check_regexes(clause.get("match", []), 0, errors, "append_when")

    criteria = row.get("criteria")
    if criteria:
        flags = _compile_flags(criteria.get("flags"))
        _check_regexes(criteria.get("match", []), flags, errors, "match")
        _check_regexes(criteria.get("exclude", []), flags, errors, "exclude")
        if "builtin" in criteria and criteria["builtin"] not in nudge_builtins.MATCHERS:
            errors.append(f"unknown builtin matcher {criteria['builtin']!r}")

    return errors


def load_rules():
    """Load and validate all bundled nudge rows; return valid raw rows.

    Rules live in per-event subdirectories (nudges/<EventName>/*.json). A file
    may hold one rule object or an array of them. The parent directory name
    must match each rule's ``event`` field - a mismatch is skipped with a
    stderr note so the directory structure stays authoritative. Unparsable
    files and invalid rows are skipped too, so one bad row can never suppress
    the rest.
    """
    rules = []
    seen_ids = set()
    if not NUDGES_DIR.is_dir():
        return rules

    for path in sorted(NUDGES_DIR.glob("**/*.json")):
        # The parent directory names the event; files loose in nudges/ are skipped.
        dir_event = path.parent.name
        if dir_event == NUDGES_DIR.name:
            print(f"[engine] skipping {path.name}: not in an event subdirectory", file=sys.stderr)
            continue

        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[engine] skipping {path.name}: {exc}", file=sys.stderr)
            continue

        rows = data if isinstance(data, list) else [data]
        for row in rows:
            errors = validate_rule(row, seen_ids)
            if isinstance(row, dict) and row.get("event") != dir_event:
                errors.append(
                    f"event {row.get('event')!r} does not match directory {dir_event!r}"
                )
            if errors:
                rid = row.get("id", "<no id>") if isinstance(row, dict) else "<not an object>"
                print(f"[engine] skipping rule {rid}: {'; '.join(errors)}", file=sys.stderr)
                continue
            seen_ids.add(row["id"])
            rules.append(row)

    return rules


def _compile_rule(rule):
    """Return a copy of rule with criteria/append_when regexes compiled."""
    compiled = copy.deepcopy(rule)

    criteria = compiled.get("criteria")
    if criteria:
        flags = _compile_flags(criteria.get("flags"))
        if "match" in criteria:
            criteria["match"] = [re.compile(p, flags) for p in criteria["match"]]
        if "exclude" in criteria:
            criteria["exclude"] = [re.compile(p, flags) for p in criteria["exclude"]]

    action = compiled.get("action")
    if action and "append_when" in action:
        for clause in action["append_when"]:
            if "match" in clause:
                clause["match"] = [re.compile(p) for p in clause["match"]]

    return compiled


def rules_for(event):
    """Return compiled rules for the dispatched event (empty for unknown)."""
    if event not in CAPABILITY_MATRIX:
        return []
    return [_compile_rule(r) for r in load_rules() if r.get("event") == event]
