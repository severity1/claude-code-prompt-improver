#!/usr/bin/env python3
"""
Claude Code Prompt Optimizer Hook
Intercepts user prompts and spawns a subagent to evaluate and optimize them.
Uses Claude Haiku subagent for intelligent evaluation.
"""
import sys
import json
from pathlib import Path


def build_optimization_wrapper(prompt: str, cwd: str) -> str:
    """
    Build the wrapped prompt that instructs Claude to spawn a subagent for evaluation.
    The subagent will intelligently decide if optimization is needed.
    """
    project_name = Path(cwd).name if cwd else "unknown"

    wrapper = f"""PROMPT EVALUATION AND OPTIMIZATION

Original user request: "{prompt}"
Project: {project_name}

ACTION REQUIRED: Spawn a subagent to evaluate if this prompt needs optimization.

Use the Task tool with this configuration:
{{
  "subagent_type": "general-purpose",
  "description": "Evaluate and optimize prompt",
  "prompt": \"\"\"You are a prompt evaluation and optimization agent for Claude Code.

Original user prompt: "{prompt}"

Your task: Evaluate if this prompt needs optimization to be more actionable and specific.

APPROACH:
1. Use your judgment and available tools to understand the project context
2. Decide if the prompt is clear enough to execute well, or if clarification would help
3. If optimization is needed, ask the user targeted questions with context-aware suggestions
4. Synthesize an enriched prompt based on their answers
5. Show the optimized prompt to the user and ask for confirmation before returning

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
\"\"\"
}}

After the subagent returns:
1. Extract the OPTIMIZED_PROMPT from its response
2. Proceed with executing that optimized prompt
3. DO NOT include the optimization process details in your main session context
4. Just execute the task as if the user provided the optimized prompt originally
"""

    return wrapper


def main():
    # Read hook input from stdin
    try:
        hook_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Fallback if stdin is not JSON
        sys.exit(0)

    prompt = hook_data.get("prompt", "")
    cwd = hook_data.get("cwd", "")

    # Check for bypass command
    if prompt.startswith("!"):
        # User explicitly bypassed optimization - pass through as-is
        clean_prompt = prompt[1:].strip()
        print(clean_prompt)
        sys.exit(0)

    # Always spawn subagent to evaluate and potentially optimize
    wrapped_prompt = build_optimization_wrapper(prompt, cwd)
    print(wrapped_prompt)
    sys.exit(0)


if __name__ == "__main__":
    main()
