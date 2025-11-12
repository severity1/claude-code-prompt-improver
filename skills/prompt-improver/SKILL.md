---
name: prompt-improver
description: This skill enriches vague prompts with targeted research and clarification before execution. Should be used when a prompt is determined to be vague and requires systematic research, question generation, and execution guidance.
---

# Prompt Improver Skill

## Purpose

Transform vague, ambiguous prompts into actionable, well-defined requests through systematic research and targeted clarification. This skill is invoked when the hook has already determined a prompt needs enrichment.

## When This Skill is Invoked

**Automatic invocation:**
- UserPromptSubmit hook evaluates prompt
- Hook determines prompt is vague (missing specifics, context, or clear target)
- Hook invokes this skill to guide research and questioning

**Manual invocation:**
- To enrich a vague prompt with research-based questions
- When building or testing prompt evaluation systems
- When prompt lacks sufficient context even with conversation history

**Assumptions:**
- Prompt has already been identified as vague
- Evaluation phase is complete (done by hook)
- Proceed directly to research and clarification

## Core Workflow

This skill follows a 4-phase approach to prompt enrichment:

### Phase 1: Research

Create a dynamic research plan using TodoWrite before asking questions.

**Research Plan Template:**
1. **Check conversation history first** - Avoid redundant exploration if context already exists
2. **Review codebase** if needed:
   - Task/Explore for architecture and project structure
   - Grep/Glob for specific patterns, related files
   - Check git log for recent changes
   - Search for errors, failing tests, TODO/FIXME comments
3. **Gather additional context** as needed:
   - Read local documentation files
   - WebFetch for online documentation
   - WebSearch for best practices, common approaches, current information
4. **Document findings** to ground questions in actual project context

**Critical Rules:**
- NEVER skip research
- Check conversation history before exploring codebase
- Questions must be grounded in actual findings, not assumptions or base knowledge

For detailed research strategies, patterns, and examples, see [references/research-strategies.md](references/research-strategies.md).

### Phase 2: Generate Targeted Questions

Based on research findings, formulate 1-6 questions that will clarify the ambiguity.

**Question Guidelines:**
- **Grounded**: Every option comes from research (codebase findings, documentation, common patterns)
- **Specific**: Avoid vague options like "Other approach"
- **Multiple choice**: Provide 2-4 concrete options per question
- **Focused**: Each question addresses one decision point
- **Contextual**: Include brief explanations of trade-offs

**Number of Questions:**
- **1-2 questions**: Simple ambiguity (which file? which approach?)
- **3-4 questions**: Moderate complexity (scope + approach + validation)
- **5-6 questions**: Complex scenarios (major feature with multiple decision points)

For question templates, effective patterns, and examples, see [references/question-patterns.md](references/question-patterns.md).

### Phase 3: Get Clarification

Use the AskUserQuestion tool to present your research-grounded questions.

**AskUserQuestion Format:**
```
- question: Clear, specific question ending with ?
- header: Short label (max 12 chars) for UI display
- multiSelect: false (unless choices aren't mutually exclusive)
- options: Array of 2-4 specific choices from research
  - label: Concise choice text (1-5 words)
  - description: Context about this option (trade-offs, implications)
```

**Important:** Always include multiSelect field (true/false). User can always select "Other" for custom input.

### Phase 4: Execute with Context

Proceed with the original user request using:
- Original prompt intent
- Clarification answers from user
- Research findings and context
- Conversation history

Execute the request as if it had been clear from the start.

## Examples

### Example 1: Skill Invocation → Research → Questions → Execution

**Hook evaluation:** Determined prompt is vague
**Original prompt:** "fix the bug"
**Skill invoked:** Yes (prompt lacks target and context)

**Research plan:**
1. Check conversation history for recent errors
2. Explore codebase for failing tests
3. Grep for TODO/FIXME comments
4. Check git log for recent problem areas

**Research findings:**
- Recent conversation mentions login failures
- auth.py:145 has try/catch swallowing errors
- Tests failing in test_auth.py

**Questions generated:**
1. Which bug are you referring to?
   - Login authentication failure (auth.py:145)
   - Session timeout issues (session.py:89)
   - Other

**User answer:** Login authentication failure

**Execution:** Fix the error handling in auth.py:145 that's causing login failures

### Example 2: Clear Prompt (Skill Not Invoked)

**Original prompt:** "Refactor the getUserById function in src/api/users.ts to use async/await instead of promises"

**Hook evaluation:** Passes all checks
- Specific target: getUserById in src/api/users.ts
- Clear action: refactor to async/await
- Success criteria: use async/await instead of promises

**Skill invoked:** No (prompt is clear, proceeds immediately without skill invocation)

For comprehensive examples showing various prompt types and transformations, see [references/examples.md](references/examples.md).

## Key Principles

1. **Assume Vagueness**: Skill is only invoked for vague prompts (evaluation done by hook)
2. **Research First**: Always gather context before formulating questions
3. **Ground Questions**: Use research findings, not assumptions or base knowledge
4. **Be Specific**: Provide concrete options from actual codebase/context
5. **Stay Focused**: Max 1-6 questions, each addressing one decision point
6. **Systematic Approach**: Follow 4-phase workflow (Research → Questions → Clarify → Execute)

## Progressive Disclosure

This SKILL.md contains the core workflow and essentials. For deeper guidance:

- **Research strategies**: [references/research-strategies.md](references/research-strategies.md)
- **Question patterns**: [references/question-patterns.md](references/question-patterns.md)
- **Comprehensive examples**: [references/examples.md](references/examples.md)

Load these references only when detailed guidance is needed on specific aspects of prompt improvement.
