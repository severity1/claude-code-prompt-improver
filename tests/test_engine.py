#!/usr/bin/env python3
"""
End-to-end tests for the engine entry point (scripts/engine.py).

Runs the engine as a subprocess per event (engine.py <EventName>),
mirroring how Claude Code dispatches the hook. Covers merged output
shape, fragment presence/absence by trigger, bypass exact-equality,
robustness (bad JSON, unknown/missing event), and the zero-Python
extensibility guarantee via a drop-in fixture nudge.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
ENGINE = PROJECT_ROOT / "scripts" / "engine.py"
NUDGES_DIR = PROJECT_ROOT / "nudges"

# Engine lives in scripts/ and imports its siblings (rules, nudge_builtins) by
# bare name, so put scripts/ on the path to import it in-process for the #1 test.
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import engine  # noqa: E402 - import after sys.path mutation


def run_engine(event, payload=None, raw=None, cwd=None, env=None):
    """Run engine.py <event> feeding JSON (payload) or raw stdin."""
    if raw is not None:
        stdin = raw
    else:
        stdin = json.dumps(payload if payload is not None else {})
    return subprocess.run(
        [sys.executable, str(ENGINE), event],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def context_of(result, event):
    """Assert success + correct echoed event, return additionalContext."""
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["hookEventName"] == event
    return output["hookSpecificOutput"]["additionalContext"]


# ---------------------------------------------------------------------------
# Merged output shape
# ---------------------------------------------------------------------------

def test_userpromptsubmit_shape_and_event_echo():
    """UserPromptSubmit emits the merged hookSpecificOutput shape"""
    result = run_engine("UserPromptSubmit", {"prompt": "fix the bug"})
    context = context_of(result, "UserPromptSubmit")
    assert isinstance(context, str)


def test_improve_fragment_always_present_on_ups():
    """The improve wrapper is always present on UserPromptSubmit"""
    context = context_of(
        run_engine("UserPromptSubmit", {"prompt": "fix the bug"}),
        "UserPromptSubmit",
    )
    assert "PROMPT EVALUATION" in context
    assert "fix the bug" in context


# ---------------------------------------------------------------------------
# Fragment merge: improve + workflow together
# ---------------------------------------------------------------------------

def test_workflow_and_improve_merge():
    """A workflow prompt yields both the improve wrapper and workflow guidance"""
    context = context_of(
        run_engine("UserPromptSubmit", {"prompt": "build a workflow to migrate files"}),
        "UserPromptSubmit",
    )
    assert "PROMPT EVALUATION" in context
    assert "orchestration" in context
    # Blank-line join between fragments.
    assert "\n\n" in context


def test_non_workflow_prompt_has_no_workflow_guidance():
    """An ordinary prompt has the improve wrapper but no workflow guidance"""
    context = context_of(
        run_engine("UserPromptSubmit", {"prompt": "add a comment to utils.py"}),
        "UserPromptSubmit",
    )
    assert "PROMPT EVALUATION" in context
    assert "orchestration" not in context


# ---------------------------------------------------------------------------
# Bypass exact-equality
# ---------------------------------------------------------------------------

def test_asterisk_bypass_exact_equality():
    """* prefix yields exactly the stripped prompt, no other fragments merged"""
    context = context_of(
        run_engine("UserPromptSubmit", {"prompt": "* build a workflow"}),
        "UserPromptSubmit",
    )
    assert context == "build a workflow"


def test_slash_bypass_passthrough():
    """/ prefix passes through unchanged"""
    context = context_of(
        run_engine("UserPromptSubmit", {"prompt": "/commit"}),
        "UserPromptSubmit",
    )
    assert context == "/commit"


def test_hash_bypass_passthrough():
    """# prefix passes through unchanged"""
    context = context_of(
        run_engine("UserPromptSubmit", {"prompt": "# note for later"}),
        "UserPromptSubmit",
    )
    assert context == "# note for later"


# ---------------------------------------------------------------------------
# PreToolUse (plan) + SubagentStart nudges
# ---------------------------------------------------------------------------

def test_pretooluse_plan_guidance_fires():
    """PreToolUse on EnterPlanMode emits the plan readability guidance"""
    context = context_of(
        run_engine("PreToolUse", {"tool_name": "EnterPlanMode"}), "PreToolUse"
    )
    assert "decision history" in context
    assert "rewrite the whole plan clean" in context


def test_pretooluse_plan_guidance_includes_self_review():
    """The plan nudge carries the pre-presentation self-review line"""
    context = context_of(
        run_engine("PreToolUse", {"tool_name": "EnterPlanMode"}), "PreToolUse"
    )
    assert "not checked against the code" in context


def test_plan_silent_on_bash():
    """The plan rule self-gates on tool_name and stays silent on Bash"""
    result = run_engine(
        "PreToolUse", {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}
    )
    assert result.returncode == 0
    assert "decision history" not in result.stdout


def test_background_exec_fires_on_long_running_command():
    """A dev-server Bash command triggers the background-exec guidance"""
    context = context_of(
        run_engine(
            "PreToolUse",
            {"tool_name": "Bash", "tool_input": {"command": "npm run dev"}},
        ),
        "PreToolUse",
    )
    assert "background" in context.lower()
    assert "token efficiency" in context.lower()


def test_background_exec_silent_on_short_command():
    """A short-lived Bash command does not trigger background-exec"""
    result = run_engine(
        "PreToolUse", {"tool_name": "Bash", "tool_input": {"command": "ls -la"}}
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_background_exec_silent_when_no_command():
    """A Bash payload missing tool_input.command is a clean no-op, not a crash"""
    result = run_engine("PreToolUse", {"tool_name": "Bash"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_output_readability_fires_on_deliverable_keyword():
    """A prompt asking for a report triggers the output-readability nudge"""
    context = context_of(
        run_engine("UserPromptSubmit", {"prompt": "write a report comparing the two designs"}),
        "UserPromptSubmit",
    )
    assert "human-parsable" in context


def test_output_readability_silent_on_plain_prompt():
    """An ordinary prompt has the improve wrapper but no readability guidance"""
    context = context_of(
        run_engine("UserPromptSubmit", {"prompt": "rename the variable in utils.py"}),
        "UserPromptSubmit",
    )
    assert "human-parsable" not in context


def test_approach_assessment_fires_on_complexity_keyword():
    """A multi-file/architectural request triggers the approach-assessment nudge"""
    context = context_of(
        run_engine(
            "UserPromptSubmit", {"prompt": "refactor auth across all services"}
        ),
        "UserPromptSubmit",
    )
    assert "choose the approach before starting" in context


def test_approach_assessment_silent_on_trivial_prompt():
    """A trivial prompt has the improve wrapper but no approach-assessment guidance"""
    context = context_of(
        run_engine("UserPromptSubmit", {"prompt": "fix typo in README"}),
        "UserPromptSubmit",
    )
    assert "choose the approach before starting" not in context


def test_subagentstart_routing_fires():
    """SubagentStart emits routing guidance for an Explore agent"""
    context = context_of(
        run_engine("SubagentStart", {"agent_type": "Explore"}),
        "SubagentStart",
    )
    assert isinstance(context, str)
    assert context.strip() != ""


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------

def test_bad_json_exits_zero():
    """Invalid JSON on stdin exits 0 (centralized to exit-0)"""
    result = run_engine("UserPromptSubmit", raw="not json at all")
    assert result.returncode == 0
    # Bad JSON is treated as {}; improve still fires (always-on).
    if result.stdout.strip():
        output = json.loads(result.stdout)
        assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"


def test_empty_stdin_exits_zero():
    """Empty stdin exits 0"""
    result = run_engine("UserPromptSubmit", raw="")
    assert result.returncode == 0


def test_unknown_event_exits_zero_empty():
    """An unknown event exits 0 with no output"""
    result = run_engine("NoSuchEvent", {})
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_missing_event_arg_exits_zero_empty():
    """A missing event argument exits 0 with no output"""
    result = subprocess.run(
        [sys.executable, str(ENGINE)],
        input="{}",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_unknown_event_does_not_read_stdin():
    """An unknown event exits before requiring stdin (no hang/crash)"""
    # Even with garbage stdin, an unknown event is a clean no-op.
    result = run_engine("NoSuchEvent", raw="garbage {[}")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_rules_for_raising_still_exits_zero(monkeypatch, capsys):
    """A load-time exception in rules_for still exits 0 (issue #1).

    rules_for -> load_rules does a glob + regex compile before the per-rule
    crash guard, so a failure there must be caught by main() itself. Run
    in-process and force rules_for to raise; before the fix the exception
    propagates out of main() instead of becoming a clean exit 0.
    """
    def boom(_event):
        raise RuntimeError("glob/compile failure")

    monkeypatch.setattr(engine, "rules_for", boom)
    monkeypatch.setattr(sys, "argv", ["engine.py", "UserPromptSubmit"])

    with pytest.raises(SystemExit) as excinfo:
        engine.main()
    assert excinfo.value.code == 0
    # The failure is logged to stderr, never emitted as hook output on stdout.
    assert capsys.readouterr().out.strip() == ""


# ---------------------------------------------------------------------------
# Extensibility guarantee: a new nudge is a single JSON row, zero Python
# ---------------------------------------------------------------------------

def test_drop_in_fixture_nudge_fires_end_to_end():
    """A fresh nudges/<Event>/*.json row fires through the engine with no code change"""
    # Dropped into the event subdirectory with a priority-prefixed name, per
    # the authoring convention. The directory name must match the event field.
    fixture = NUDGES_DIR / "UserPromptSubmit" / "99-zz-fixture-test.json"
    sentinel = "ZZFIXTURESENTINELXYZ"
    fixture.write_text(
        json.dumps(
            {
                "id": "zz-fixture-test",
                "event": "UserPromptSubmit",
                "description": "test-only fixture, safe to delete",
                "criteria": {"match": [r"zzfixturetrigger"]},
                "action": {"type": "inject_context", "text": [sentinel]},
            }
        )
    )
    try:
        # Fires when the trigger keyword is present.
        hit = context_of(
            run_engine("UserPromptSubmit", {"prompt": "please zzfixturetrigger now"}),
            "UserPromptSubmit",
        )
        assert sentinel in hit

        # Silent when the trigger keyword is absent.
        miss = context_of(
            run_engine("UserPromptSubmit", {"prompt": "ordinary request"}),
            "UserPromptSubmit",
        )
        assert sentinel not in miss
    finally:
        fixture.unlink()


def test_append_when_respects_match_target():
    """append_when matches the rule's match_target, not always the prompt (issue #3).

    A SubagentStart rule with match_target=agent_type and an append_when clause
    keyed on the agent type must append when the agent matches - even though the
    payload has no prompt key. Before the fix _render_action hardcoded the prompt
    read, so the clause searched an empty string and the appended text was absent.
    """
    fixture = NUDGES_DIR / "SubagentStart" / "99-zz-append-test.json"
    base = "ZZBASESENTINEL"
    appended = "ZZAPPENDEDSENTINEL"
    fixture.write_text(
        json.dumps(
            {
                "id": "zz-append-test",
                "event": "SubagentStart",
                "description": "test-only fixture, safe to delete",
                "criteria": {"match_target": "agent_type"},
                "action": {
                    "type": "inject_context",
                    "text": [base],
                    "append_when": [{"match": [r"Explore"], "text": [appended]}],
                },
            }
        )
    )
    try:
        # agent_type carries the trigger; there is no prompt key in the payload.
        context = context_of(
            run_engine("SubagentStart", {"agent_type": "Explore"}),
            "SubagentStart",
        )
        assert base in context
        assert appended in context
    finally:
        fixture.unlink()
