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
    # Get project context
    project_name = Path(cwd).name if cwd else "unknown"
    has_claude_md = (Path(cwd) / "CLAUDE.md").exists() if cwd else False

    wrapper = f"""PROMPT EVALUATION AND OPTIMIZATION

Original user request: "{prompt}"

Project: {project_name}
Has CLAUDE.md: {has_claude_md}

ACTION REQUIRED: Spawn a subagent to evaluate if this prompt needs optimization.

Use the Task tool with this configuration:
{{
  "subagent_type": "general-purpose",
  "description": "Evaluate and optimize prompt",
  "prompt": \"\"\"You are a prompt evaluation and optimization agent for Claude Code.

Original user prompt: "{prompt}"

Your task: Intelligently evaluate if this prompt needs optimization, and optimize if necessary.

EVALUATION PROCESS:

1. Gather Project Context:
   - If CLAUDE.md exists, read it for project patterns and conventions
   - Use Glob to verify any mentioned files exist (check common variations)
   - Use Grep to search for relevant code patterns
   - Check git status for recent changes (if relevant)

2. Evaluate Prompt Quality:
   ✓ Is the intent clear? (what does user want to accomplish?)
   ✓ Are targets specific? (which files/components/areas?)
   ✓ Is there enough context? (error details, requirements, constraints?)
   ✓ Is it actionable? (can you start work immediately?)

   ✗ Red flags:
   - Generic references ("the app", "the code", "it", "that thing")
   - Missing error details for fix requests
   - Missing requirements for feature requests
   - Ambiguous scope ("update the tests" - which tests?)

3. Decide if Optimization is Needed:
   - High confidence (can execute well as-is): Return original prompt
   - Medium/Low confidence (needs clarification): Optimize it

4. If Optimization Needed:
   a) Use AskUserQuestion to offer optimization:
      Question: "I can help clarify your request for better results. Optimize this prompt?"
      Options:
        - "Yes, optimize it" (gather more details)
        - "No, proceed as-is" (use original prompt)
        - "What's unclear?" (explain issues first)

   b) If user wants optimization, ask targeted questions based on what's missing:

      Missing target/scope:
      - "Which file or component should I work with?"
      - Provide options if you found candidates via Grep/Glob

      Missing error context (for fixes):
      - "Do you have error messages or logs to share?"
      - Options: [Yes, I'll paste them | It's behavioral | Check console]

      Missing requirements (for features):
      - "What should this feature include?" (multi-select)
      - Options based on common patterns: [UI components | State management | API calls | Tests | Docs]

      Missing test specifics:
      - "What type of tests?"
      - Options: [Unit tests | Integration tests | E2E tests | Component tests]

   c) Synthesize enriched prompt with:
      - Specific files/components to work with
      - Clear success criteria
      - Relevant context from CLAUDE.md
      - Error details or requirements
      - Any constraints or preferences

   d) Confirm with user before returning

5. Return Format:

   OPTIMIZED_PROMPT:
   <the final prompt - either original or enriched version>

   OPTIMIZATION_NOTES:
   <what was changed and why, or why no changes were needed>

   CONFIDENCE: <0-100>

   CONTEXT_USED:
   <list any files you read, patterns you found, etc.>

IMPORTANT:
- If prompt is already clear and specific, return it unchanged
- Don't over-optimize - sometimes simple requests are fine as-is
- Focus on making prompts actionable, not just longer
- Use project context (CLAUDE.md) to align with established patterns
\"\"\"
}}

After the subagent returns:
1. Extract the OPTIMIZED_PROMPT from its response
2. Proceed with executing that optimized prompt
3. DO NOT include the optimization process details in your main session context
4. Just execute the task as if the user provided the optimized prompt originally
"""

    if has_claude_md:
        wrapper += """

NOTE: This project has CLAUDE.md documentation. The subagent should read it
to understand project-specific patterns, conventions, and preferences.
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
