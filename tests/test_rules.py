#!/usr/bin/env python3
"""
Unit tests for the rule layer (scripts/rules.py).

Covers validate_rule rejection cases, the event->capability matrix,
load_rules round-tripping the bundled nudges, and rules_for dispatch.
"""
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import rules  # noqa: E402
from rules import (  # noqa: E402
    CAPABILITY_MATRIX,
    load_rules,
    rules_for,
    validate_rule,
)


# ---------------------------------------------------------------------------
# validate_rule - happy paths
# ---------------------------------------------------------------------------

def test_validate_minimal_action_rule():
    """A minimal pure-data rule with a legal action validates clean"""
    errors = validate_rule(
        {
            "id": "x",
            "event": "UserPromptSubmit",
            "action": {"type": "inject_context", "text": ["hello"]},
        },
        seen_ids=set(),
    )
    assert errors == []


def test_validate_handler_rule():
    """A handler rule validates clean"""
    errors = validate_rule(
        {"id": "x", "event": "UserPromptSubmit", "handler": "improve"},
        seen_ids=set(),
    )
    assert errors == []


def test_validate_criteria_with_regex():
    """A rule with a compilable criteria regex validates clean"""
    errors = validate_rule(
        {
            "id": "x",
            "event": "UserPromptSubmit",
            "criteria": {"match": [r"\bworkflow\b"], "flags": ["ignorecase"]},
            "action": {"type": "inject_context", "text": ["hi"]},
        },
        seen_ids=set(),
    )
    assert errors == []


# ---------------------------------------------------------------------------
# validate_rule - rejection cases
# ---------------------------------------------------------------------------

def test_validate_rejects_missing_id():
    errors = validate_rule(
        {"event": "UserPromptSubmit", "action": {"type": "inject_context", "text": ["x"]}},
        seen_ids=set(),
    )
    assert errors


def test_validate_rejects_missing_event():
    errors = validate_rule(
        {"id": "x", "action": {"type": "inject_context", "text": ["x"]}},
        seen_ids=set(),
    )
    assert errors


def test_validate_rejects_unknown_event():
    errors = validate_rule(
        {"id": "x", "event": "NoSuchEvent", "action": {"type": "inject_context", "text": ["x"]}},
        seen_ids=set(),
    )
    assert errors


def test_validate_rejects_action_and_handler_both():
    """A rule with both action and handler is ambiguous and rejected"""
    errors = validate_rule(
        {
            "id": "x",
            "event": "UserPromptSubmit",
            "action": {"type": "inject_context", "text": ["x"]},
            "handler": "improve",
        },
        seen_ids=set(),
    )
    assert errors


def test_validate_rejects_neither_action_nor_handler():
    """A rule with neither action nor handler is rejected"""
    errors = validate_rule(
        {"id": "x", "event": "UserPromptSubmit"},
        seen_ids=set(),
    )
    assert errors


def test_validate_rejects_illegal_action_for_event():
    """An action type not legal for the event is rejected"""
    errors = validate_rule(
        {
            "id": "x",
            "event": "UserPromptSubmit",
            "action": {"type": "block_tool", "text": ["x"]},
        },
        seen_ids=set(),
    )
    assert errors


def test_validate_rejects_uncompilable_regex():
    """An uncompilable criteria regex is rejected"""
    errors = validate_rule(
        {
            "id": "x",
            "event": "UserPromptSubmit",
            "criteria": {"match": ["(unbalanced"]},
            "action": {"type": "inject_context", "text": ["x"]},
        },
        seen_ids=set(),
    )
    assert errors


def test_validate_rejects_uncompilable_append_when_regex():
    """An uncompilable append_when regex is rejected"""
    errors = validate_rule(
        {
            "id": "x",
            "event": "UserPromptSubmit",
            "action": {
                "type": "inject_context",
                "text": ["x"],
                "append_when": [{"match": ["(bad"], "text": ["y"]}],
            },
        },
        seen_ids=set(),
    )
    assert errors


def test_validate_rejects_unknown_builtin_matcher():
    """A criteria builtin not in the matcher allowlist is rejected"""
    errors = validate_rule(
        {
            "id": "x",
            "event": "UserPromptSubmit",
            "criteria": {"builtin": "rm_rf_everything"},
            "action": {"type": "inject_context", "text": ["x"]},
        },
        seen_ids=set(),
    )
    assert errors


def test_validate_rejects_unknown_handler():
    """A handler name not in the handler allowlist is rejected"""
    errors = validate_rule(
        {"id": "x", "event": "UserPromptSubmit", "handler": "definitely_not_real"},
        seen_ids=set(),
    )
    assert errors


def test_validate_rejects_duplicate_id():
    """A duplicate id is rejected when the id is already seen"""
    errors = validate_rule(
        {"id": "dup", "event": "UserPromptSubmit", "handler": "improve"},
        seen_ids={"dup"},
    )
    assert errors


# ---------------------------------------------------------------------------
# Capability matrix
# ---------------------------------------------------------------------------

def test_capability_matrix_known_events():
    """The matrix covers the three v1 inject-context events"""
    for event in ("UserPromptSubmit", "PreToolUse", "SubagentStart"):
        assert event in CAPABILITY_MATRIX
        assert "inject_context" in CAPABILITY_MATRIX[event]


# ---------------------------------------------------------------------------
# load_rules / rules_for
# ---------------------------------------------------------------------------

def test_load_rules_round_trips_bundled():
    """load_rules loads the bundled nudge rows without raising"""
    loaded = load_rules()
    ids = {r["id"] for r in loaded}
    # The three migrated rules must all be present.
    assert "improve" in ids
    assert "workflow" in ids
    assert "plan" in ids


def test_load_rules_unique_ids():
    """All bundled rule ids are unique"""
    loaded = load_rules()
    ids = [r["id"] for r in loaded]
    assert len(ids) == len(set(ids))


def _write_rule(directory, name, event):
    """Write a minimal valid rule file into directory under the given event."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(
        json.dumps(
            {
                "id": name.replace(".json", ""),
                "event": event,
                "action": {"type": "inject_context", "text": ["x"]},
            }
        )
    )


def test_load_rules_directory_must_match_event(tmp_path, monkeypatch):
    """A rule whose event matches its folder loads; a mismatch is skipped"""
    monkeypatch.setattr(rules, "NUDGES_DIR", tmp_path)

    # Matching: PreToolUse/ holds a PreToolUse rule.
    _write_rule(tmp_path / "PreToolUse", "00-good.json", "PreToolUse")
    # Mismatch: PreToolUse/ holds a rule claiming UserPromptSubmit.
    _write_rule(tmp_path / "PreToolUse", "01-bad.json", "UserPromptSubmit")

    loaded_ids = {r["id"] for r in rules.load_rules()}
    assert "00-good" in loaded_ids
    assert "01-bad" not in loaded_ids


def test_load_rules_skips_loose_files(tmp_path, monkeypatch):
    """A JSON file directly in nudges/ (no event subdir) is skipped"""
    monkeypatch.setattr(rules, "NUDGES_DIR", tmp_path)
    (tmp_path / "loose.json").write_text(
        json.dumps(
            {
                "id": "loose",
                "event": "UserPromptSubmit",
                "action": {"type": "inject_context", "text": ["x"]},
            }
        )
    )
    assert rules.load_rules() == []


def test_rules_for_filters_by_event():
    """rules_for returns only rules for the dispatched event"""
    ups = rules_for("UserPromptSubmit")
    assert all(r["event"] == "UserPromptSubmit" for r in ups)
    ids = {r["id"] for r in ups}
    assert "improve" in ids
    assert "workflow" in ids
    # plan is PreToolUse, must not leak into UserPromptSubmit.
    assert "plan" not in ids


def test_rules_for_pretooluse_has_plan():
    """rules_for(PreToolUse) includes the plan rule"""
    pre = rules_for("PreToolUse")
    ids = {r["id"] for r in pre}
    assert "plan" in ids


def test_rules_for_subagentstart_has_routing():
    """rules_for(SubagentStart) includes the subagent-routing rule"""
    sub = rules_for("SubagentStart")
    ids = {r["id"] for r in sub}
    assert "subagent-routing" in ids


def test_rules_for_unknown_event_empty():
    """rules_for returns an empty list for an unknown event"""
    assert rules_for("NoSuchEvent") == []


def test_compiled_regex_cached_on_load():
    """Criteria regexes are compiled once at load (not raw strings)"""
    import re as _re

    ups = rules_for("UserPromptSubmit")
    for rule in ups:
        criteria = rule.get("criteria")
        if criteria and criteria.get("match"):
            for pattern in criteria["match"]:
                assert isinstance(pattern, _re.Pattern)
