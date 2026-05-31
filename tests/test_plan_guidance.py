#!/usr/bin/env python3
"""
Tests for the plan-guidance hook
Validates JSON output structure, guidance content, and exit code.
"""
import json
import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent.parent / "scripts" / "engine.py"


def run_hook(input_data=None):
    """Run the engine for the PreToolUse event and return the CompletedProcess.

    Defaults to an EnterPlanMode payload because the plan rule now self-gates on
    tool_name; the engine also runs on Bash, where plan must stay silent.
    """
    if input_data is None:
        input_data = json.dumps({"tool_name": "EnterPlanMode"})
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), "PreToolUse"],
        input=input_data,
        capture_output=True,
        text=True
    )
    return result


def test_output_json_structure():
    """Test that output follows the hook JSON format"""
    result = run_hook()
    assert result.returncode == 0

    output = json.loads(result.stdout)
    assert "hookSpecificOutput" in output
    assert output["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert "additionalContext" in output["hookSpecificOutput"]


def test_guidance_content():
    """Test that additionalContext contains plan readability guidance"""
    result = run_hook()
    output = json.loads(result.stdout)
    context = output["hookSpecificOutput"]["additionalContext"]

    assert "decision history" in context
    assert "rewrite the entire plan clean" in context
    assert "terse action steps" in context
    assert "problem statement" in context


def test_exit_code_zero():
    """Test that script exits with code 0"""
    result = run_hook()
    assert result.returncode == 0


def test_handles_empty_stdin():
    """Empty stdin exits 0; with no tool_name the plan rule stays silent"""
    result = run_hook("")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_handles_invalid_json_stdin():
    """Invalid JSON exits 0; with no tool_name the plan rule stays silent"""
    result = run_hook("not json at all")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_silent_on_bash_tool():
    """The engine also runs on Bash; the plan rule must not fire there"""
    result = run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
    assert result.returncode == 0
    assert "decision history" not in result.stdout
