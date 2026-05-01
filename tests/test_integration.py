#!/usr/bin/env python3
"""
Integration tests for the prompt-improver system
Tests the complete flow from hook to skill
"""
import json
import subprocess
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
HOOK_SCRIPT = PROJECT_ROOT / "scripts" / "improve-prompt.py"
PLUGIN_JSON = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
SKILL_DIR = PROJECT_ROOT / "skills" / "prompt-improver"

def run_hook(prompt):
    """Run the hook script with given prompt and return stdout text"""
    input_data = json.dumps({"prompt": prompt})

    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=input_data,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Hook failed: {result.stderr}")

    return result.stdout.rstrip("\n")

def test_plugin_configuration():
    """Test that plugin.json is properly configured"""
    assert PLUGIN_JSON.exists(), "plugin.json not found"

    config = json.loads(PLUGIN_JSON.read_text())

    # Check version is 0.5.2
    assert config["version"] == "0.5.2", f"Expected version 0.5.2, got {config['version']}"

    # Check hooks field is NOT present (standard hooks/hooks.json is auto-discovered)
    assert "hooks" not in config, "The 'hooks' field should not be present (standard location is auto-discovered)"

    # Check skills field is NOT present (standard skills/ directory is auto-discovered)
    assert "skills" not in config, "The 'skills' field should not be present (standard location is auto-discovered)"

    print("✓ Plugin configuration is correct")

def test_end_to_end_flow():
    """Test complete flow from prompt to evaluation"""
    # Test normal prompt
    output = run_hook("add authentication")

    # Should get evaluation wrapper
    assert "PROMPT EVALUATION" in output or "EVALUATE" in output
    assert "add authentication" in output

    # Should mention skill for vague cases
    assert "skill" in output.lower()

    print("✓ End-to-end flow works (normal prompt → evaluation wrapper)")

def test_bypass_flow():
    """Test that bypass mechanism works end-to-end"""
    # Test asterisk bypass
    output = run_hook("* just do it")
    assert output == "just do it"
    assert "skill" not in output.lower()

    # Test slash command
    output = run_hook("/commit")
    assert output == "/commit"

    # Test hash prefix
    output = run_hook("# note for later")
    assert output == "# note for later"

    print("✓ Bypass mechanisms work end-to-end")

def test_skill_file_integrity():
    """Test that all skill files are present and valid"""
    # Check SKILL.md
    skill_md = SKILL_DIR / "SKILL.md"
    assert skill_md.exists(), "SKILL.md missing"

    content = skill_md.read_text()
    assert content.startswith("---\n"), "SKILL.md missing YAML frontmatter"
    assert "name: prompt-improver" in content, "Skill name incorrect"

    # Check reference files
    references_dir = SKILL_DIR / "references"
    assert references_dir.exists(), "references directory missing"

    expected_refs = [
        "question-patterns.md",
        "research-strategies.md",
        "examples.md",
    ]

    for ref in expected_refs:
        ref_file = references_dir / ref
        assert ref_file.exists(), f"Missing reference file: {ref}"

    print("✓ All skill files present and valid")

def test_token_overhead():
    """Test that hook overhead is reasonable"""
    output = run_hook("test")

    # Rough character count (tokens ≈ chars/4 for English)
    char_count = len(output)
    estimated_tokens = char_count // 4

    # New version should be ~200-220 tokens (evaluation prompt with preface instruction)
    # Old v0.3.2 was ~275 tokens (embedded evaluation logic)
    assert estimated_tokens < 250, \
        f"Hook overhead too high: ~{estimated_tokens} tokens (expected <250)"

    # Should be less than old version
    old_estimated_tokens = 275
    if estimated_tokens < old_estimated_tokens:
        reduction_percent = ((old_estimated_tokens - estimated_tokens) / old_estimated_tokens) * 100
        print(f"✓ Token overhead acceptable: ~{estimated_tokens} tokens (<250), ~{reduction_percent:.0f}% reduction from v0.3.2")
    else:
        print(f"✓ Token overhead acceptable: ~{estimated_tokens} tokens (<250)")

def test_hook_output_consistency():
    """Test that hook output is consistent across different prompts"""
    prompts = [
        "fix the bug",
        "add tests",
        "refactor code",
        "implement feature X",
    ]

    for prompt in prompts:
        output = run_hook(prompt)

        # All should be plain text (not JSON)
        assert not output.strip().startswith("{")
        assert "hookSpecificOutput" not in output

        # All should have evaluation wrapper
        assert "EVALUATE" in output or "evaluate" in output.lower()
        assert prompt in output

    print(f"✓ Hook output consistent across {len(prompts)} different prompts")

def test_architecture_separation():
    """Test that architecture properly separates concerns"""
    # Hook should be reasonably sized (< 80 lines)
    hook_lines = len(HOOK_SCRIPT.read_text().split("\n"))
    assert hook_lines < 80, f"Hook too large: {hook_lines} lines (expected <80)"

    # Hook should contain evaluation logic
    hook_content = HOOK_SCRIPT.read_text()
    assert "PROMPT EVALUATION" in hook_content or "EVALUATE" in hook_content

    # SKILL.md should contain research and question logic (now 4 phases)
    skill_content = (SKILL_DIR / "SKILL.md").read_text()
    assert "Phase 1" in skill_content or "phase 1" in skill_content.lower()
    assert "Phase 2" in skill_content or "phase 2" in skill_content.lower()
    assert "Research" in skill_content

    # Skill should mention being invoked for vague prompts
    assert "vague" in skill_content.lower()

    print("✓ Architecture properly separates concerns (hook evaluates, skill enriches)")

def run_all_tests():
    """Run all integration tests"""
    tests = [
        test_plugin_configuration,
        test_end_to_end_flow,
        test_bypass_flow,
        test_skill_file_integrity,
        test_token_overhead,
        test_hook_output_consistency,
        test_architecture_separation,
    ]

    print(f"Running {len(tests)} integration tests...\n")

    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed.append((test.__name__, e))
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed.append((test.__name__, e))

    print(f"\n{'='*60}")
    if failed:
        print(f"FAILED: {len(failed)}/{len(tests)} tests failed")
        for name, error in failed:
            print(f"  - {name}: {error}")
        sys.exit(1)
    else:
        print(f"SUCCESS: All {len(tests)} integration tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    run_all_tests()
