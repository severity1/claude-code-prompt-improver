#!/usr/bin/env python3
"""
Claude Code Prompt Improver Hook
Evaluates prompts for clarity and invokes the prompt-improver skill for vague cases.
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

# Escape quotes in prompt for safe embedding
escaped_prompt = prompt.replace("\\", "\\\\").replace('"', '\\"')

def output_json(text):
    """Output text in UserPromptSubmit JSON format"""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": text
        }
    }
    print(json.dumps(output))

# Check for bypass conditions
# 1. Explicit bypass with * prefix
# 2. Slash commands (built-in or custom)
# 3. Memorize feature (# prefix)
if prompt.startswith("*"):
    # User explicitly bypassed improvement - remove * prefix
    clean_prompt = prompt[1:].strip()
    output_json(clean_prompt)
    sys.exit(0)

if prompt.startswith("/"):
    # Slash command - pass through unchanged
    output_json(prompt)
    sys.exit(0)

if prompt.startswith("#"):
    # Memorize feature - pass through unchanged
    output_json(prompt)
    sys.exit(0)

# Build the evaluation wrapper
wrapped_prompt = f"""PROMPT EVALUATION

Original user request: "{escaped_prompt}"

EVALUATE: Is this prompt clear enough to execute, or does it need enrichment?

PROCEED IMMEDIATELY if:
- Detailed/specific OR you have sufficient context OR can infer intent

ONLY USE SKILL if genuinely vague (e.g., "fix the bug" with no context):
- If vague:
  1. First, preface with brief note: "Hey! The Prompt Improver Hook flagged your prompt as a bit vague because [specific reason: ambiguous scope/missing context/unclear target/etc]."
  2. Then use the prompt-improver skill to research and generate clarifying questions
- The skill will guide you through research, question generation, and execution
- Trust user intent by default. Check conversation history before using the skill.

If clear, proceed with the original request. If vague, invoke the skill."""

output_json(wrapped_prompt)
sys.exit(0)
