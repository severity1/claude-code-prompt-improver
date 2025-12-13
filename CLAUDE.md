# Claude Code Prompt Improver

<!-- AUTO-MANAGED: project-description -->
A UserPromptSubmit hook that enriches vague prompts before Claude Code executes them. Uses skill-based architecture with hook-level evaluation for efficient prompt clarity assessment.

**Core functionality:**
- Intercepts prompts via UserPromptSubmit hook
- Evaluates clarity using conversation history
- Clear prompts: proceeds immediately (189 token overhead)
- Vague prompts: invokes prompt-improver skill for research and clarification
- Uses AskUserQuestion tool for targeted clarifying questions (1-6 questions)

**Requirements:** Claude Code 2.0.22+ (requires AskUserQuestion tool)
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: architecture -->
## Architecture

**Hook Layer (scripts/improve-prompt.py):**
- 71 lines - evaluation orchestrator
- Intercepts via stdin/stdout JSON
- Handles bypass prefixes: `*` (skip), `/` (slash commands), `#` (memorize)
- Wraps prompts with evaluation instructions (189 tokens)
- Claude evaluates clarity using conversation history
- If vague: instructs Claude to invoke prompt-improver skill

**Skill Layer (skills/prompt-improver/):**
- `SKILL.md`: Research and question workflow (170 lines)
  - 4-phase process: Research → Questions → Clarify → Execute
  - Assumes prompt already determined vague by hook
  - Links to reference files for progressive disclosure
- `references/`: Detailed guides loaded on-demand
  - `question-patterns.md`: Question templates (200-300 lines)
  - `research-strategies.md`: Context gathering (300-400 lines)
  - `examples.md`: Real transformations (200-300 lines)

**Directory structure:**
- `scripts/` - Hook implementation
- `skills/prompt-improver/` - Skill and reference files
- `tests/` - Test suite (hook, skill, integration)
- `hooks/` - Hook configuration (hooks.json)
- `.claude-plugin/` - Plugin metadata
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: build-commands -->
## Build Commands

**Testing:**
- Run all tests: `pytest tests/` or `python -m pytest`
- Run specific test suite:
  - Hook tests: `pytest tests/test_hook.py`
  - Skill tests: `pytest tests/test_skill.py`
  - Integration tests: `pytest tests/test_integration.py`

**Installation:**
- Add marketplace: `claude plugin marketplace add severity1/severity1-marketplace`
- Via marketplace: `claude plugin install prompt-improver@severity1-marketplace`
- Local dev: `claude plugin marketplace add /path/to/claude-code-prompt-improver/.dev-marketplace/.claude-plugin/marketplace.json` then `claude plugin install prompt-improver@local-dev`
- Manual hook: `cp scripts/improve-prompt.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/improve-prompt.py`
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: conventions -->
## Conventions

**Hook output format:**
- JSON structure following Claude Code specification
- Format: `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}`
- Exit code 0 for all success paths

**Bypass prefixes:**
- `*` prefix: Skip evaluation entirely
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
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: patterns -->
## Patterns

**Progressive disclosure:**
- Clear prompts: evaluation only (189 tokens), no skill load
- Vague prompts: evaluation + skill load + references
- Reference materials load only when needed
- Zero context penalty for unused reference materials

**Evaluation flow:**
1. Hook wraps prompt with evaluation instructions
2. Claude evaluates using conversation history
3. If clear: proceed immediately
4. If vague: invoke prompt-improver skill → research → questions → execute

**Research and questioning:**
- Create dynamic research plan via TodoWrite
- Research what needs clarification (not just the project)
- Ground questions in research findings (not generic assumptions)
- Support 1-6 questions for complex scenarios
- Use conversation history to avoid redundant exploration
<!-- END AUTO-MANAGED -->

<!-- MANUAL -->
## Design Philosophy

- **Rarely intervene** - Most prompts pass through unchanged
- **Trust user intent** - Only ask when genuinely unclear
- **Use conversation history** - Avoid redundant exploration
- **Max 1-6 questions** - Enough for complex scenarios, still focused
- **Transparent** - Evaluation visible in conversation
<!-- END MANUAL -->
