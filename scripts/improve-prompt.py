#!/usr/bin/env python3
"""
Claude Code Prompt Improver Hook
Intercepts user prompts and evaluates if they need enrichment before execution.
Uses main session context for intelligent, non-pedantic evaluation.
"""
import json
import sys

# Load input from stdin
try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
    sys.exit(1)

prompt = input_data.get("prompt", "")

# Escape quotes in prompt for safe embedding in wrapped instructions
escaped_prompt = prompt.replace("\\", "\\\\").replace('"', '\\"')

# Check for bypass conditions
# 1. Explicit bypass with * prefix
# 2. Slash commands (built-in or custom)
# 3. Memorize feature (# prefix)
if prompt.startswith("*"):
    # User explicitly bypassed improvement - remove * prefix
    clean_prompt = prompt[1:].strip()
    print(clean_prompt)
    sys.exit(0)

if prompt.startswith("/"):
    # Slash command - pass through unchanged
    print(prompt)
    sys.exit(0)

if prompt.startswith("#"):
    # Memorize feature - pass through unchanged
    print(prompt)
    sys.exit(0)

# Build the improvement wrapper
wrapped_prompt = f"""PROMPT EVALUATION

Original user request: "{escaped_prompt}"

EVALUATE: Is this prompt clear enough to execute, or does it need enrichment?

PROCEED IMMEDIATELY if:
- Detailed/specific OR you have sufficient context OR can infer intent

ONLY ASK if genuinely vague (e.g., "fix the bug" with no context):
- CRITICAL (NON-NEGOTIABLE) RULES:
  - Trust user intent by default. Check conversation history before doing research.
  - Do not rely on base knowledge.
  - Never skip Phase 1. Research before asking.
  - Don't announce evaluation - just proceed or ask.

- PHASE 1 - RESEARCH (DO NOT SKIP):
  1. Preface with brief note: "Prompt Improver Hook is seeking clarification because [specific reason: ambiguous scope/missing context/unclear requirements/etc]"
  2. Create research plan with TodoWrite: Ask yourself "What do I need to research to clarify this vague request?" Research WHAT NEEDS CLARIFICATION, not just the project. Use available tools: Task/Explore for codebase, WebSearch for online research (current info, common approaches, best practices, typical architectures), Read/Grep as needed
  3. Execute research
  4. Use research findings (not your training) to formulate grounded questions with specific options
  5. Mark completed

- PHASE 2 - ASK (ONLY AFTER PHASE 1):
  1. Use AskUserQuestion tool with max 1-6 questions offering specific options from your research
  2. Use the answers to execute the original user request
"""

print(wrapped_prompt)
sys.exit(0)
