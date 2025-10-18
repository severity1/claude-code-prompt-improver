#!/usr/bin/env python3
"""
Claude Code Prompt Optimizer Hook
Intercepts user prompts and spawns a subagent to evaluate and optimize them.
Uses subagent for intelligent evaluation.
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
# 1. Explicit bypass with ! prefix
# 2. Slash commands (built-in or custom)
if prompt.startswith("!"):
    # User explicitly bypassed optimization - remove ! prefix
    clean_prompt = prompt[1:].strip()
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": clean_prompt,
        }
    }
    print(json.dumps(output))
    sys.exit(0)

if prompt.startswith("/"):
    # Slash command - pass through unchanged
    print(prompt)
    sys.exit(0)

# Build the optimization wrapper
wrapped_prompt = f"""PROMPT EVALUATION AND OPTIMIZATION

Original user request: "{escaped_prompt}"

ACTION REQUIRED: Spawn a subagent to evaluate if this prompt needs optimization.

Use the Task tool with this configuration:
{{
  "subagent_type": "general-purpose",
  "description": "Evaluate and optimize prompt",
  "prompt": \"\"\"You are a prompt evaluation and optimization agent for Claude Code.

Original user prompt: "{escaped_prompt}"

Your task: Evaluate if this prompt needs optimization to be more actionable and specific.

APPROACH:
1. Use your judgment and available tools to understand the project context
2. Decide if the prompt is clear enough to execute well, or if clarification would help
3. If optimization is needed, ask the user targeted questions with context-aware suggestions
4. Synthesize an enriched prompt based on their answers
5. Show the optimized prompt to the user and ask for confirmation before returning

AVOID USER FATIGUE:
- Don't be pedantic - if the prompt is "good enough", let it through
- Keep questions to a minimum (ideally 1-2 questions maximum)
- When in doubt, trust the user's intent and proceed
- If you can infer reasonable context from exploration, don't ask - just use it
- Only ask when clarification would significantly improve the outcome
- Combine related questions when possible instead of asking separately

WHEN ASKING CLARIFYING QUESTIONS:
- CRITICAL: Provide rich, specific options based on what you discovered in the codebase
- Example: Don't just ask "which file?" - search the project and offer actual file paths as options
- Example: Don't ask generic questions - tailor them to the specific project architecture you found
- Use multi-select when multiple items might be relevant
- Include contextual suggestions from what you learned exploring the project

WHEN CONFIRMING OPTIMIZED PROMPT:
- Show the user the optimized prompt you created
- Ask if they're happy with it using AskUserQuestion
- Options: "Yes, use this" | "Needs adjustment" | "Use original instead"
- If adjustment needed, ask what to change and revise
- Return the final version they approve

RETURN FORMAT:
OPTIMIZED_PROMPT:
<the final prompt - either original if already clear, or enriched version>

OPTIMIZATION_NOTES:
<brief explanation of changes or why none were needed>

CONFIDENCE: <0-100>

GUIDELINES:
- If already clear and actionable, return unchanged
- Don't over-optimize simple requests
- Focus on actionability over verbosity
- Leverage project patterns and conventions you discover
- Prefer inferring context over asking questions
- Err on the side of proceeding rather than over-questioning
- The goal is helpfulness, not perfection
\"\"\"
}}

After the subagent returns:
1. Extract the OPTIMIZED_PROMPT from its response
2. Proceed with executing that optimized prompt
3. DO NOT include the optimization process details in your main session context
4. Just execute the task as if the user provided the optimized prompt originally
"""

print(wrapped_prompt)
sys.exit(0)
