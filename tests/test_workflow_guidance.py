#!/usr/bin/env python3
"""
Tests for the workflow-guidance hook
Validates trigger detection, bypass, guidance content, exit codes, and token budget.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent.parent / "scripts" / "workflow-guidance.py"


def run_hook(prompt=None, raw=None, cwd=None, env=None):
    """Run the workflow-guidance hook and return the CompletedProcess.

    Pass `prompt` to send {"prompt": ...} JSON, or `raw` to send raw stdin.
    """
    if raw is not None:
        input_data = raw
    else:
        input_data = json.dumps({"prompt": prompt})

    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=input_data,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def parse(result):
    """Assert success and return the parsed additionalContext string."""
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    return output["hookSpecificOutput"]["additionalContext"]


def test_keyword_triggers():
    """A prompt containing 'workflow' triggers routing guidance"""
    context = parse(run_hook("build a workflow to migrate 500 files"))
    assert "orchestration" in context
    assert "implementation" in context


def test_plural_keyword_triggers():
    """The plural 'workflows' also triggers"""
    context = parse(run_hook("compare dynamic workflows for this repo"))
    assert "orchestration" in context


def test_workflows_management_command_no_output():
    """/workflows is a run-management command, not a launch trigger (#2)"""
    result = run_hook("/workflows")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_conditional_guard_present():
    """A keyword trigger's context leads with the conditional guard (#3)"""
    context = parse(run_hook("build a workflow to migrate 500 files"))
    assert context.startswith("If this prompt will run as a dynamic workflow")


def test_deep_research_command_triggers():
    """The /deep-research command triggers guidance"""
    context = parse(run_hook("/deep-research the auth subsystem"))
    assert "implementation" in context


def test_effort_ultracode_triggers_with_clause():
    """/effort ultracode triggers and appends the session-wide clause"""
    context = parse(run_hook("/effort ultracode"))
    assert "every task" in context


def test_non_ultracode_omits_clause():
    """Non-ultracode triggers do not include the ultracode clause"""
    context = parse(run_hook("build a workflow to refactor"))
    assert "every task" not in context


def test_saved_workflow_scan():
    """A saved workflow file under .claude/workflows triggers detection"""
    with tempfile.TemporaryDirectory() as tmp:
        workflows = Path(tmp) / ".claude" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "myflow.md").write_text("# saved workflow\n")

        # HOME override isolates both scan dirs to the tmp tree.
        env = {**os.environ, "HOME": tmp}

        triggered = run_hook("/myflow run it", cwd=tmp, env=env)
        context = parse(triggered)
        assert "orchestration" in context

        not_triggered = run_hook("/notaflow run it", cwd=tmp, env=env)
        assert not_triggered.returncode == 0
        assert not_triggered.stdout.strip() == ""


def test_path_traversal_does_not_trigger():
    """Path-traversal slash input does not trigger and does not raise"""
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "HOME": tmp}
        result = run_hook("/../../etc/passwd", cwd=tmp, env=env)
        assert result.returncode == 0
        assert result.stdout.strip() == ""
        assert result.stderr.strip() == ""


def test_non_workflow_prompt_no_output():
    """An ordinary prompt produces no output"""
    result = run_hook("add a comment to utils.py")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_bypass_prefix_no_output():
    """The * bypass prefix suppresses output even for workflow prompts"""
    result = run_hook("* build a workflow")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_hash_bypass_no_output():
    """The # memorize prefix suppresses output even for workflow prompts (#1)"""
    result = run_hook("# remember the deploy workflow doc")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_empty_stdin_exits_zero():
    """Empty stdin exits 0 with no output"""
    result = run_hook(raw="")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_invalid_json_stdin_exits_zero():
    """Invalid JSON stdin exits 0 with no output"""
    result = run_hook(raw="not json at all")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_token_budget():
    """Guidance string stays within the token budget"""
    context = parse(run_hook("/effort ultracode"))
    assert len(context.split()) < 110
