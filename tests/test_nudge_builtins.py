#!/usr/bin/env python3
"""
Unit tests for the escape-hatch builtins (scripts/nudge_builtins.py).

Ports the in-process behavior assertions from the old test_hook.py
(improve) and test_workflow_guidance.py (workflow + saved_workflow_exists)
onto the named-callable seams. These run against the functions directly,
not via subprocess.
"""
import sys
from pathlib import Path

# scripts/ is on sys.path[0] when the engine runs; mirror that for unit tests.
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import nudge_builtins  # noqa: E402
from nudge_builtins import (  # noqa: E402
    HANDLERS,
    MATCHERS,
    improve,
    saved_workflow_exists,
    workflow,
)


# ---------------------------------------------------------------------------
# Allowlist registries
# ---------------------------------------------------------------------------

def test_handlers_allowlist():
    """HANDLERS exposes improve and workflow by string name"""
    assert "improve" in HANDLERS
    assert "workflow" in HANDLERS
    assert HANDLERS["improve"] is improve
    assert HANDLERS["workflow"] is workflow


def test_matchers_allowlist():
    """MATCHERS exposes the saved_workflow_exists builtin by string name"""
    assert "saved_workflow_exists" in MATCHERS
    assert MATCHERS["saved_workflow_exists"] is saved_workflow_exists


# ---------------------------------------------------------------------------
# improve() - ports of test_hook.py
# ---------------------------------------------------------------------------

def test_improve_bypass_asterisk():
    """The * prefix strips the prefix and returns the bare prompt"""
    assert improve({"prompt": "* just add a comment"}) == "just add a comment"


def test_improve_bypass_slash():
    """The / prefix passes through unchanged (slash commands)"""
    assert improve({"prompt": "/commit"}) == "/commit"


def test_improve_bypass_hash():
    """The # prefix passes through unchanged (memorize feature)"""
    assert improve({"prompt": "# remember to use TypeScript"}) == "# remember to use TypeScript"


def test_improve_evaluation_wrapper():
    """Normal prompts get the evaluation wrapper"""
    context = improve({"prompt": "fix the bug"})
    assert "PROMPT EVALUATION" in context
    assert "fix the bug" in context
    assert "EVALUATE" in context
    assert "skill" in context.lower()
    assert "proceed" in context.lower() or "clear" in context.lower()


def test_improve_empty_prompt_still_wraps():
    """An empty prompt still produces the evaluation wrapper (skill mention)"""
    context = improve({"prompt": ""})
    assert "prompt-improver skill" in context.lower()


def test_improve_missing_prompt_key():
    """A dict with no prompt key behaves like an empty prompt"""
    context = improve({})
    assert "PROMPT EVALUATION" in context


def test_improve_multiline_preserved():
    """Multiline prompts are preserved inside the wrapper"""
    prompt = "refactor the auth system\nto use async/await\nand add error handling"
    context = improve({"prompt": prompt})
    assert "refactor the auth system" in context


def test_improve_quote_escaping():
    """Special characters are escaped but content is preserved"""
    context = improve({"prompt": 'fix the "bug" in user\'s code & database'})
    assert "bug" in context
    assert "user" in context
    # Embedded double-quotes are backslash-escaped in the wrapper.
    assert '\\"bug\\"' in context


def test_improve_backslash_escaping():
    """Backslashes are escaped so the wrapper stays well formed"""
    context = improve({"prompt": r"match \d+ digits"})
    assert r"\\d+" in context


# ---------------------------------------------------------------------------
# workflow() - ports of test_workflow_guidance.py
# ---------------------------------------------------------------------------

def test_workflow_keyword_triggers():
    """A prompt containing 'workflow' returns routing guidance"""
    context = workflow({"prompt": "build a workflow to migrate 500 files"})
    assert context is not None
    assert "orchestration" in context
    assert "implementation" in context


def test_workflow_plural_keyword_triggers():
    """The plural 'workflows' also triggers"""
    context = workflow({"prompt": "compare dynamic workflows for this repo"})
    assert context is not None
    assert "orchestration" in context


def test_workflow_management_command_silent():
    """/workflows is a run-management command, not a launch trigger"""
    assert workflow({"prompt": "/workflows"}) is None


def test_workflow_conditional_guard_present():
    """Guidance leads with the self-cancelling conditional guard"""
    context = workflow({"prompt": "build a workflow to migrate 500 files"})
    assert context.startswith("If this prompt")


def test_workflow_deep_research_triggers():
    """The /deep-research command triggers guidance"""
    context = workflow({"prompt": "/deep-research the auth subsystem"})
    assert context is not None
    assert "implementation" in context


def test_workflow_ultracode_appends_clause():
    """/effort ultracode triggers and appends the session-wide clause"""
    context = workflow({"prompt": "/effort ultracode"})
    assert context is not None
    assert "every task" in context


def test_workflow_non_ultracode_omits_clause():
    """Non-ultracode triggers do not include the ultracode clause"""
    context = workflow({"prompt": "build a workflow to refactor"})
    assert "every task" not in context


def test_workflow_non_workflow_prompt_silent():
    """An ordinary prompt returns None"""
    assert workflow({"prompt": "add a comment to utils.py"}) is None


def test_workflow_bypass_asterisk_silent():
    """The * bypass prefix suppresses guidance even for workflow prompts"""
    assert workflow({"prompt": "* build a workflow"}) is None


def test_workflow_bypass_hash_silent():
    """The # memorize prefix suppresses guidance even for workflow prompts"""
    assert workflow({"prompt": "# remember the deploy workflow doc"}) is None


def test_workflow_empty_prompt_silent():
    """An empty prompt returns None"""
    assert workflow({"prompt": ""}) is None
    assert workflow({}) is None


def test_workflow_token_budget():
    """Guidance string stays within the token budget"""
    context = workflow({"prompt": "/effort ultracode"})
    assert len(context.split()) < 110


# ---------------------------------------------------------------------------
# saved_workflow_exists() - ports of the scan + path-traversal tests
# ---------------------------------------------------------------------------

def test_saved_workflow_scan_match(tmp_path, monkeypatch):
    """A saved workflow file under .claude/workflows is detected"""
    workflows = tmp_path / ".claude" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "myflow.md").write_text("# saved workflow\n")

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    assert saved_workflow_exists("/myflow run it") is True
    assert saved_workflow_exists("/notaflow run it") is False


def test_saved_workflow_via_handler(tmp_path, monkeypatch):
    """The workflow handler triggers on a saved-workflow slash command"""
    workflows = tmp_path / ".claude" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "myflow.md").write_text("# saved workflow\n")

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    context = workflow({"prompt": "/myflow run it"})
    assert context is not None
    assert "orchestration" in context

    assert workflow({"prompt": "/notaflow run it"}) is None


def test_saved_workflow_path_traversal_safe(tmp_path, monkeypatch):
    """Path-traversal slash input does not match and does not raise"""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert saved_workflow_exists("/../../etc/passwd") is False


def test_saved_workflow_non_slash_no_match(tmp_path, monkeypatch):
    """A non-slash prompt never matches a saved workflow"""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert saved_workflow_exists("myflow run it") is False
