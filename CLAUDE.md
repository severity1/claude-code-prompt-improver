# Claude Code Prompt Improver

This file provides guidance to Claude Code when working with code in this repository.

<!-- AUTO-MANAGED: project-description -->
## Overview

A multi-hook plugin that enriches vague prompts and injects plan mode guidance. Uses skill-based architecture with hook-level evaluation for efficient prompt clarity assessment.

**Core functionality:**
- Intercepts prompts via UserPromptSubmit hook
- Evaluates clarity using conversation history
- Clear prompts: proceeds immediately with minimal overhead
- Vague prompts: invokes prompt-improver skill for research and clarification
- Uses AskUserQuestion tool for targeted clarifying questions (1-6 questions)
- Injects plan readability guidance via PreToolUse hook on EnterPlanMode
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: build-commands -->
## Build & Development Commands

**Testing:**
- Run all tests: `pytest tests/` or `python -m pytest`
- Run specific test suite:
  - Hook tests: `pytest tests/test_hook.py`
  - Skill tests: `pytest tests/test_skill.py`
  - Integration tests: `pytest tests/test_integration.py`
  - Plan guidance tests: `pytest tests/test_plan_guidance.py`

**Installation:**
- Add marketplace: `claude plugin marketplace add severity1/severity1-marketplace`
- Via marketplace: `claude plugin install prompt-improver@severity1-marketplace`
- Local dev: `claude plugin marketplace add /path/to/claude-code-prompt-improver/.dev-marketplace/.claude-plugin/marketplace.json` then `claude plugin install prompt-improver@local-dev`
- Manual hook: `cp scripts/improve-prompt.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/improve-prompt.py`
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: architecture -->
## Architecture

**Hook Layer (scripts/):**
- `improve-prompt.py`: Evaluation orchestrator - reads stdin JSON, writes stdout JSON
  - Handles bypass prefixes: `*` (skip), `/` (slash commands), `#` (memorize)
  - Wraps prompts with evaluation instructions for clarity assessment
  - Claude evaluates clarity using conversation history
  - If vague: instructs Claude to invoke prompt-improver skill
- `plan-guidance.py`: Plan mode guidance injector - fires on EnterPlanMode via PreToolUse
  - Consumes stdin, outputs plan readability guidance as additionalContext
  - Guidance: keep problem statement, omit decision history (rejected approaches, revision rationale), rewrite entire plan clean on revision (no append/annotation), one action per step with file paths as anchors (e.g., src/auth.ts:42), favor terse action steps

**Skill Layer (skills/prompt-improver/):**
- `SKILL.md`: Research and question workflow
  - 4-phase process: Research, Questions, Clarify, Execute
  - Assumes prompt already determined vague by hook
  - Links to reference files for progressive disclosure
- `references/`: Detailed guides loaded on-demand
  - `question-patterns.md`: Question templates and effective patterns
  - `research-strategies.md`: Context gathering strategies
  - `examples.md`: Real prompt transformations

**Directory structure:**
- `scripts/` - Hook implementations (improve-prompt.py, plan-guidance.py)
- `skills/prompt-improver/` - Skill and reference files
- `tests/` - Test suite (hook, skill, integration, plan_guidance)
- `hooks/` - Hook configuration (hooks.json, auto-discovered)
- `.claude-plugin/` - Plugin metadata
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: conventions -->
## Code Conventions

**Hook output format:**
- JSON structure following Claude Code specification
- UserPromptSubmit format: `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}`
- PreToolUse format: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "..."}}`
- Exit code 0 for all success paths
- Hook commands use `python3 || python` fallback for Windows compatibility

**Plugin auto-discovery:**
- Do NOT add `hooks` field to `plugin.json` - `hooks/hooks.json` at standard location is auto-discovered
- Do NOT add `skills` field to `plugin.json` - `skills/` directory at standard location is auto-discovered
- Integration test `test_plugin_configuration` asserts both fields are absent

**Bypass prefixes:**
- `*` prefix: Skip evaluation entirely, strip prefix from prompt
- `/` prefix: Slash commands bypass automatically
- `#` prefix: Memorize commands bypass automatically

**File paths:**
- Use forward slashes (Unix-style) per Claude Code standards
- All paths in plugin configuration use forward slashes

**Skill structure:**
- YAML frontmatter with name and description
- Skill name: lowercase, hyphens, max 64 chars
- Description: under 1024 chars, includes activation triggers
- Reference files: self-contained, one-level deep
- Writing style: imperative/infinitive form (avoid "you/your")

**Testing:**
- Tests use pytest-compatible functions (no test classes)
- Hook tests run the script via subprocess and validate JSON output
- Skill tests validate file structure, frontmatter, and references
- Integration tests verify end-to-end flow and architecture separation
- Python standard library only (json, sys, subprocess, pathlib, re)
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: patterns -->
## Detected Patterns

**Progressive disclosure:**
- Clear prompts: evaluation only, no skill load
- Vague prompts: evaluation + skill load + references
- Reference materials load only when needed
- Zero context penalty for unused reference materials

**Evaluation flow:**
1. Hook wraps prompt with evaluation instructions
2. Claude evaluates using conversation history
3. If clear: proceed immediately
4. If vague: invoke prompt-improver skill, then research, questions, execute

**Research and questioning:**
- Create dynamic research plan via TodoWrite
- Research what needs clarification (not just the project)
- Ground questions in research findings (not generic assumptions)
- Support 1-6 questions for complex scenarios
- Use conversation history to avoid redundant exploration

**Tool dispatch model (skill research phase):**
- Task/Explore is the primary research carrier for broad codebase exploration
- Glob, Grep, WebSearch, WebFetch, and multi-file Read must be dispatched via Task/Explore - never called directly in main context
- Bash (git commands) runs in main context only - Explore agents cannot run Bash
- Explore agents are context-blind (no access to prior conversation turns) - every Explore prompt must include relevant context explicitly
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: git-insights -->
## Git Insights

**Key architectural decisions:**
- Migrated from hook-only to skill-based architecture for significant token reduction on clear prompts
- Auto-discovery: both `hooks/hooks.json` and `skills/` at standard locations remove need for `hooks` or `skills` fields in `plugin.json`
- Plugin distributed via severity1-marketplace for easy installation
- Progressive disclosure pattern chosen to minimize context overhead for the common case (clear prompts)
- Added PreToolUse/EnterPlanMode hook to inject plan readability guidance without modifying the skill layer

**Evolution:**
- Started as embedded evaluation logic in hook script
- Extracted skill layer to separate evaluation (hook) from enrichment (skill)
- Added marketplace support for distribution
- Adopted subagent-first research dispatch: broad exploration (Glob, Grep, WebSearch, WebFetch, multi-file Read) routed through Task/Explore to isolate main context
- Added plan-guidance.py as a second hook script targeting plan mode entry
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: best-practices -->
## Best Practices

- Keep hook script minimal - it runs on every prompt submission
- Never add heavy imports or network calls to the hook script
- Reference files should be self-contained so they work when loaded independently
- Test bypass prefixes whenever modifying hook logic to prevent breaking slash commands
- When adding new bypass prefixes, update both the hook script and the conventions section
- When writing skill research steps, always pass file paths, errors, and prior decisions into every Explore prompt - Explore has no conversation history access
- Never call Glob, Grep, WebSearch, or WebFetch directly in main skill context - route them through Task/Explore to preserve context isolation
<!-- END AUTO-MANAGED -->

<!-- MANUAL -->
## Design Philosophy

- **Rarely intervene** - Most prompts pass through unchanged
- **Trust user intent** - Only ask when genuinely unclear
- **Use conversation history** - Avoid redundant exploration
- **Max 1-6 questions** - Enough for complex scenarios, still focused
- **Transparent** - Evaluation visible in conversation
<!-- END MANUAL -->
