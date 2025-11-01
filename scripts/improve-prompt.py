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

# Escape prompt for safe embedding in XML structure within Python f-string
def escape_for_xml(text):
    """Escape text for XML content while maintaining Python f-string compatibility."""
    return (text
        .replace("\\", "\\\\")  # Escape backslashes for Python f-string
        .replace("&", "&amp;")   # Escape ampersands for XML (must be first XML escape)
        .replace("<", "&lt;")    # Escape less-than for XML
        .replace(">", "&gt;"))   # Escape greater-than for XML

escaped_prompt = escape_for_xml(prompt)

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

# Build the improvement wrapper with XML structure
wrapped_prompt = f"""<prompt_evaluation>
<original_request>{escaped_prompt}</original_request>

<evaluation_framework>
<goal>Determine if prompt needs enrichment to achieve successful first-attempt execution</goal>

<output>Either (a) proceed immediately with clear prompt, or (b) ask 1-6 grounded questions based on research</output>

<limits>
- Max 1-6 questions in Phase 2
- Research before asking (no base knowledge assumptions)
- Respect conversation context and history
- Honor bypass prefixes (*, /, #)
</limits>

<data>
Available context sources:
- User prompt content and clarity
- Conversation history
- Codebase context (via Task/Explore, Grep, Read)
- External research (via WebSearch)
</data>

<evaluation>
Prompt clarity sufficient? Context available in conversation? Intent inferable from history?
</evaluation>
</evaluation_framework>

<evaluation_criteria>
Is this prompt clear enough to execute, or does it need enrichment?

<proceed_immediately>
- Detailed/specific OR you have sufficient context OR can infer intent
</proceed_immediately>

<clarification_required>
Only if genuinely vague (e.g., "fix the bug" with no context)
</clarification_required>
</evaluation_criteria>

<critical_rules>
- Trust user intent by default. Check conversation history before doing research.
- Do not rely on base knowledge.
- Never skip Phase 1. Research before asking.
- Don't announce evaluation - just proceed or ask.
</critical_rules>

<phase_1_research>
<required>DO NOT SKIP</required>

<steps>
1. Preface with brief note: "Prompt Improver Hook is seeking clarification because [specific reason: ambiguous scope/missing context/unclear requirements/etc]"
2. Create research plan with TodoWrite: Ask yourself "What do I need to research to clarify this vague request?" Research WHAT NEEDS CLARIFICATION, not just the project. Use available tools: Task/Explore for codebase, WebSearch for online research (current info, common approaches, best practices, typical architectures), Read/Grep as needed
3. Execute research
4. Use research findings (not your training) to formulate grounded questions with specific options
5. Mark completed
</steps>

<research_execution>
Execute research efficiently:
- Use parallel tool calls when researching independent aspects
- Example: Run WebSearch + Task/Explore + Grep simultaneously
- Only sequence tools when they have dependencies
- Maximize throughput by batching independent operations
</research_execution>
</phase_1_research>

<context_management>
Monitor your token budget during research phase:
- Keep research findings concise and high-signal
- Prioritize most relevant context over exhaustive exploration
- If approaching token limits, summarize and proceed
- Aim for minimal necessary context to formulate questions
</context_management>

<phase_2_ask>
<prerequisite>Only after Phase 1</prerequisite>

<steps>
1. Use AskUserQuestion tool with max 1-6 questions offering specific options from your research
2. Use the answers to execute the original user request
</steps>
</phase_2_ask>
</prompt_evaluation>"""

print(wrapped_prompt)
sys.exit(0)
