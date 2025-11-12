#!/usr/bin/env python3
"""
Tests for the prompt-improver hook
Tests bypass prefixes, skill invocation, and JSON output format
"""
import json
import subprocess
import sys
from pathlib import Path

# Path to the hook script
HOOK_SCRIPT = Path(__file__).parent.parent / "scripts" / "improve-prompt.py"

def run_hook(prompt):
    """Run the hook script with given prompt and return parsed output"""
    input_data = json.dumps({"prompt": prompt})

    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=input_data,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Hook failed: {result.stderr}")

    return json.loads(result.stdout)

def test_bypass_asterisk():
    """Test that * prefix strips the prefix and passes through"""
    output = run_hook("* just add a comment")

    assert "hookSpecificOutput" in output
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

    context = output["hookSpecificOutput"]["additionalContext"]
    assert context == "just add a comment"
    assert not context.startswith("*")
    print("✓ Asterisk bypass test passed")

def test_bypass_slash():
    """Test that / prefix passes through unchanged (slash commands)"""
    output = run_hook("/commit")

    assert "hookSpecificOutput" in output
    context = output["hookSpecificOutput"]["additionalContext"]
    assert context == "/commit"
    print("✓ Slash command bypass test passed")

def test_bypass_hash():
    """Test that # prefix passes through unchanged (memorize feature)"""
    output = run_hook("# remember to use TypeScript")

    assert "hookSpecificOutput" in output
    context = output["hookSpecificOutput"]["additionalContext"]
    assert context == "# remember to use TypeScript"
    print("✓ Hash prefix bypass test passed")

def test_evaluation_prompt():
    """Test that normal prompts get evaluation wrapper"""
    output = run_hook("fix the bug")

    assert "hookSpecificOutput" in output
    assert output["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"

    context = output["hookSpecificOutput"]["additionalContext"]

    # Should contain evaluation prompt
    assert "PROMPT EVALUATION" in context
    assert "fix the bug" in context
    assert "EVALUATE:" in context or "evaluate" in context.lower()

    # Should mention using the skill for vague cases
    assert "prompt-improver skill" in context.lower() or "skill" in context.lower()

    # Should have proceed/clear logic
    assert "clear" in context.lower() or "proceed" in context.lower()

    print("✓ Evaluation prompt test passed")

def test_json_output_format():
    """Test that output follows correct JSON schema"""
    output = run_hook("test prompt")

    # Verify structure
    assert isinstance(output, dict)
    assert "hookSpecificOutput" in output
    assert isinstance(output["hookSpecificOutput"], dict)

    hook_output = output["hookSpecificOutput"]
    assert "hookEventName" in hook_output
    assert "additionalContext" in hook_output
    assert hook_output["hookEventName"] == "UserPromptSubmit"
    assert isinstance(hook_output["additionalContext"], str)

    print("✓ JSON output format test passed")

def test_empty_prompt():
    """Test handling of empty prompt"""
    output = run_hook("")

    assert "hookSpecificOutput" in output
    context = output["hookSpecificOutput"]["additionalContext"]

    # Should still invoke skill even for empty prompt
    assert "prompt-improver skill" in context.lower()
    print("✓ Empty prompt test passed")

def test_multiline_prompt():
    """Test handling of multiline prompts"""
    prompt = """refactor the auth system
to use async/await
and add error handling"""

    output = run_hook(prompt)

    assert "hookSpecificOutput" in output
    context = output["hookSpecificOutput"]["additionalContext"]

    # Should preserve multiline content in skill invocation
    assert "refactor the auth system" in context
    print("✓ Multiline prompt test passed")

def test_special_characters():
    """Test handling of special characters in prompts"""
    output = run_hook('fix the "bug" in user\'s code & database')

    assert "hookSpecificOutput" in output
    context = output["hookSpecificOutput"]["additionalContext"]

    # Should contain the original prompt
    assert "bug" in context
    assert "user" in context or "users" in context
    print("✓ Special characters test passed")

def run_all_tests():
    """Run all tests"""
    tests = [
        test_bypass_asterisk,
        test_bypass_slash,
        test_bypass_hash,
        test_evaluation_prompt,
        test_json_output_format,
        test_empty_prompt,
        test_multiline_prompt,
        test_special_characters,
    ]

    print(f"Running {len(tests)} hook tests...\n")

    failed = []
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed.append((test.__name__, e))

    print(f"\n{'='*60}")
    if failed:
        print(f"FAILED: {len(failed)}/{len(tests)} tests failed")
        for name, error in failed:
            print(f"  - {name}: {error}")
        sys.exit(1)
    else:
        print(f"SUCCESS: All {len(tests)} hook tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    run_all_tests()
