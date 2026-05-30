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
ENGINE = PROJECT_ROOT / "scripts" / "engine.py"
PLUGIN_JSON = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
SKILL_DIR = PROJECT_ROOT / "skills" / "prompt-improver"

# scripts/ on sys.path so isolated-fragment asserts can import builtins directly.
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

def run_hook(prompt):
    """Run the engine for the UserPromptSubmit event with the given prompt"""
    input_data = json.dumps({"prompt": prompt})

    result = subprocess.run(
        [sys.executable, str(ENGINE), "UserPromptSubmit"],
        input=input_data,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Hook failed: {result.stderr}")

    return json.loads(result.stdout)

def test_plugin_configuration():
    """Test that plugin.json is properly configured"""
    assert PLUGIN_JSON.exists(), "plugin.json not found"

    config = json.loads(PLUGIN_JSON.read_text())

    # Check version is 0.5.4
    assert config["version"] == "0.5.4", f"Expected version 0.5.4, got {config['version']}"

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
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "PROMPT EVALUATION" in context or "EVALUATE" in context
    assert "add authentication" in context

    # Should mention skill for vague cases
    assert "skill" in context.lower()

    print("✓ End-to-end flow works (normal prompt → evaluation wrapper)")

def test_bypass_flow():
    """Test that bypass mechanism works end-to-end"""
    # Test asterisk bypass
    output = run_hook("* just do it")
    context = output["hookSpecificOutput"]["additionalContext"]
    assert context == "just do it"
    assert "skill" not in context.lower()

    # Test slash command
    output = run_hook("/commit")
    context = output["hookSpecificOutput"]["additionalContext"]
    assert context == "/commit"

    # Test hash prefix
    output = run_hook("# note for later")
    context = output["hookSpecificOutput"]["additionalContext"]
    assert context == "# note for later"

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
    """Each matched nudge fragment stays within the per-fragment token budget.

    Isolated-fragment unit assert (in-process): render every bundled nudge in
    isolation and confirm none alone busts the 250-token budget. Fragments can
    legitimately co-fire and merge (e.g. improve + workflow on a workflow
    prompt), so the guard is deliberately per-fragment - matching main's
    separate-hook behavior, where each hook emitted its own bounded context and
    Claude Code concatenated them.
    """
    import rules as rules_mod
    import nudge_builtins

    # Triggering inputs so handler rules actually emit a fragment to measure.
    handler_inputs = {
        "improve": {"prompt": "fix the bug"},
        "workflow": {"prompt": "build a workflow to migrate files"},
    }

    for rule in rules_mod.load_rules():
        if "handler" in rule:
            fragment = nudge_builtins.HANDLERS[rule["handler"]](
                handler_inputs.get(rule["handler"], {"prompt": "x"})
            ) or ""
        else:
            action = rule.get("action", {})
            fragment = "\n".join(action.get("text", []))
            for clause in action.get("append_when", []):
                fragment += " " + " ".join(clause.get("text", []))

        estimated_tokens = len(fragment) // 4
        assert estimated_tokens < 250, \
            f"Nudge {rule['id']!r} fragment too large: ~{estimated_tokens} tokens (expected <250)"

    print("✓ Every matched nudge fragment stays within the 250-token budget")

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

        # All should have same structure
        assert "hookSpecificOutput" in output
        assert "hookEventName" in output["hookSpecificOutput"]
        assert "additionalContext" in output["hookSpecificOutput"]

        # All should have evaluation wrapper
        context = output["hookSpecificOutput"]["additionalContext"]
        assert "EVALUATE" in context or "evaluate" in context.lower()
        assert prompt in context

    print(f"✓ Hook output consistent across {len(prompts)} different prompts")

def test_architecture_separation():
    """Test that architecture properly separates concerns"""
    # Engine entry point should exist and stay a small dispatcher (< 200 lines)
    assert ENGINE.exists(), "scripts/engine.py not found"
    engine_lines = len(ENGINE.read_text().split("\n"))
    assert engine_lines < 200, f"Engine too large: {engine_lines} lines (expected <200)"

    # The evaluation wrapper lives in the builtins module, not the engine.
    builtins_content = (PROJECT_ROOT / "scripts" / "nudge_builtins.py").read_text()
    assert "PROMPT EVALUATION" in builtins_content
    assert "PROMPT EVALUATION" not in ENGINE.read_text(), \
        "Engine should dispatch, not embed evaluation prose"

    # SKILL.md should contain research and question logic (now 4 phases)
    skill_content = (SKILL_DIR / "SKILL.md").read_text()
    assert "Phase 1" in skill_content or "phase 1" in skill_content.lower()
    assert "Phase 2" in skill_content or "phase 2" in skill_content.lower()
    assert "Research" in skill_content

    # Skill should mention being invoked for vague prompts
    assert "vague" in skill_content.lower()

    print("✓ Architecture properly separates concerns (engine dispatches, builtins/rules enrich)")

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
