#!/usr/bin/env python3
"""
Tests for the prompt-improver skill
Tests YAML frontmatter, file structure, and content validation
"""
import re
import sys
from pathlib import Path

# Paths
SKILL_DIR = Path(__file__).parent.parent / "skills" / "prompt-improver"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"

def test_skill_directory_exists():
    """Test that skill directory exists"""
    assert SKILL_DIR.exists(), f"Skill directory not found: {SKILL_DIR}"
    assert SKILL_DIR.is_dir(), f"Skill path is not a directory: {SKILL_DIR}"
    print("✓ Skill directory exists")

def test_skill_md_exists():
    """Test that SKILL.md file exists"""
    assert SKILL_MD.exists(), f"SKILL.md not found: {SKILL_MD}"
    assert SKILL_MD.is_file(), f"SKILL.md is not a file: {SKILL_MD}"
    print("✓ SKILL.md exists")

def test_yaml_frontmatter():
    """Test that SKILL.md has valid YAML frontmatter"""
    content = SKILL_MD.read_text()

    # Check for opening ---
    assert content.startswith("---\n"), "SKILL.md must start with ---"

    # Extract frontmatter
    parts = content.split("---\n", 2)
    assert len(parts) >= 3, "Invalid YAML frontmatter format"

    frontmatter = parts[1]

    # Check required fields
    assert "name:" in frontmatter, "Frontmatter missing 'name' field"
    assert "description:" in frontmatter, "Frontmatter missing 'description' field"

    # Validate name format (lowercase, numbers, hyphens only)
    name_match = re.search(r"name:\s*(\S+)", frontmatter)
    assert name_match, "Could not parse 'name' field"

    name = name_match.group(1)
    assert name == "prompt-improver", f"Unexpected skill name: {name}"
    assert re.match(r"^[a-z0-9-]+$", name), f"Invalid name format: {name}"
    assert len(name) <= 64, f"Name too long (max 64 chars): {name}"

    # Validate description exists and is reasonable length
    desc_match = re.search(r"description:\s*(.+?)(?=\n\w+:|$)", frontmatter, re.DOTALL)
    assert desc_match, "Could not parse 'description' field"

    description = desc_match.group(1).strip()
    assert len(description) > 0, "Description is empty"
    assert len(description) <= 1024, f"Description too long (max 1024 chars): {len(description)}"

    print(f"✓ YAML frontmatter valid (name: {name}, description: {len(description)} chars)")

def test_skill_content_structure():
    """Test that SKILL.md has expected content sections"""
    content = SKILL_MD.read_text()

    # Check for main sections (updated for v0.4.0 with 4 phases)
    expected_sections = [
        "# Prompt Improver Skill",
        "## Purpose",
        "## When This Skill is Invoked",
        "## Core Workflow",
        "### Phase 1:",
        "### Phase 2:",
        "### Phase 3:",
        "### Phase 4:",
        "## Examples",
        "## Key Principles",
    ]

    for section in expected_sections:
        assert section in content, f"Missing expected section: {section}"

    print("✓ SKILL.md has expected content structure")

def test_references_directory():
    """Test that references directory exists with expected files"""
    assert REFERENCES_DIR.exists(), f"References directory not found: {REFERENCES_DIR}"
    assert REFERENCES_DIR.is_dir(), "References path is not a directory"

    expected_files = [
        "question-patterns.md",
        "research-strategies.md",
        "examples.md",
    ]

    for filename in expected_files:
        file_path = REFERENCES_DIR / filename
        assert file_path.exists(), f"Missing reference file: {filename}"
        assert file_path.is_file(), f"Reference path is not a file: {filename}"

        # Check file is not empty
        content = file_path.read_text()
        assert len(content) > 100, f"Reference file seems too small: {filename}"

    print(f"✓ References directory has all {len(expected_files)} expected files")

def test_forward_slash_paths():
    """Test that all file paths use forward slashes (Unix style)"""
    content = SKILL_MD.read_text()

    # Check for backslashes in file paths
    # Allow backslashes in code blocks but not in markdown links
    links = re.findall(r'\[.*?\]\((.*?)\)', content)

    for link in links:
        assert "\\" not in link, f"Found backslash in file path: {link}"
        assert link.startswith("references/") or link.startswith("./"), \
            f"File path should be relative: {link}"

    print("✓ All file paths use forward slashes")

def test_reference_file_structure():
    """Test that reference files have proper structure"""
    reference_files = [
        "question-patterns.md",
        "research-strategies.md",
        "examples.md",
    ]

    for filename in reference_files:
        content = (REFERENCES_DIR / filename).read_text()

        # Should start with # heading
        assert content.strip().startswith("#"), \
            f"{filename} should start with heading"

        # Should have table of contents if long enough
        if content.count("\n") > 100:
            assert "## Table of Contents" in content or "# " in content[:500], \
                f"{filename} is long but missing table of contents"

    print("✓ Reference files have proper structure")

def test_skill_references_valid():
    """Test that SKILL.md references to other files are valid"""
    content = SKILL_MD.read_text()

    # Find all markdown links
    links = re.findall(r'\[.*?\]\((.*?)\)', content)

    for link in links:
        # Skip external links
        if link.startswith("http"):
            continue

        # Resolve relative path
        referenced_file = SKILL_DIR / link
        assert referenced_file.exists(), f"Broken reference: {link} -> {referenced_file}"

    print("✓ All SKILL.md file references are valid")

def test_skill_line_count():
    """Test that SKILL.md is under recommended 500 lines"""
    content = SKILL_MD.read_text()
    line_count = content.count("\n")

    # Warning if over 500 lines (best practice)
    if line_count > 500:
        print(f"⚠  Warning: SKILL.md is {line_count} lines (recommended: <500)")
    else:
        print(f"✓ SKILL.md is {line_count} lines (under 500 line recommendation)")

def run_all_tests():
    """Run all skill tests"""
    tests = [
        test_skill_directory_exists,
        test_skill_md_exists,
        test_yaml_frontmatter,
        test_skill_content_structure,
        test_references_directory,
        test_forward_slash_paths,
        test_reference_file_structure,
        test_skill_references_valid,
        test_skill_line_count,
    ]

    print(f"Running {len(tests)} skill tests...\n")

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
        print(f"SUCCESS: All {len(tests)} skill tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    run_all_tests()
