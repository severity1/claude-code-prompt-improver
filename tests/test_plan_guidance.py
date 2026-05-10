#!/usr/bin/env python3
"""
Tests for the plan-guidance hook
Validates JSON output structure, guidance content, and exit code.
"""
import json
import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent.parent / "scripts" / "plan-guidance.py"


def run_hook(input_data="{}"):
    """Run the plan-guidance hook and return (parsed_output, returncode)"""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
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
    """Test graceful handling of empty stdin"""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="",
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "hookSpecificOutput" in output


def test_handles_invalid_json_stdin():
    """Test graceful handling of invalid JSON on stdin"""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="not json at all",
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert "hookSpecificOutput" in output
