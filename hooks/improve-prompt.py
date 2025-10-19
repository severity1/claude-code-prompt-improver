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

Trust user intent by default. Use conversation history before exploring project.

PROCEED IMMEDIATELY if:
- Detailed/specific OR you have context from conversation OR conversational (not action) OR can infer intent

ONLY ASK if genuinely vague (e.g., "fix the bug" with no context):
- Preface with brief note mentioning "Prompt Improver Hook" is seeking clarification
- Use TodoWrite to track: "Research project context to ground clarifying questions"
- Mark it in_progress and research using available tools (search, explore codebase, check external docs/sources)
- Ground your questions in what you actually find, not generic guesses
- Mark research todo as completed
- Use AskUserQuestion tool with max 1-2 questions offering specific options from your research
- Then proceed with enriched prompt

Don't announce evaluation - just proceed or ask.
"""

print(wrapped_prompt)
sys.exit(0)
