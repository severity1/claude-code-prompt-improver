# Claude Code Prompt Improver

This file provides guidance to Claude Code when working with code in this repository.

<!-- AUTO-MANAGED: project-description -->
## Overview

A declarative hook engine driven by a JSON nudge registry. One engine dispatches every hook event; each prompt-improvement capability is a data row in `nudges/<EventName>/*.json`, not a separate script. Adding an inject-context nudge is a single JSON file with zero Python changes.

**Core functionality:**
- One engine entry point (`engine.py <EventName>`) dispatched per hook event from `hooks.json`
- Reads stdin once, runs the event's rules, merges `inject_context` fragments by priority, emits one JSON object, exits 0 always
- `improve` nudge (always fires on UserPromptSubmit): evaluates clarity; clear prompts proceed, vague prompts invoke the prompt-improver skill
- `workflow` nudge: injects model-routing and plan-mode-first HITL guidance for workflow/deep-research/ultracode requests
- `plan` nudge (PreToolUse on EnterPlanMode): injects plan readability guidance
- `subagent-routing` nudge (SubagentStart): injects breadth-over-depth guidance when an Explore or Plan agent spawns
- `background-exec` nudge: self-cancelling reminder to background long-running processes (dev server, watcher) on keyword match
- Uses AskUserQuestion tool for targeted clarifying questions (1-6 questions)
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: build-commands -->
## Build & Development Commands

**Testing:**
- Run all tests: `pytest tests/` or `python -m pytest`
- Run specific test suite:
  - Engine tests (end-to-end, subprocess per event): `pytest tests/test_engine.py`
  - Rules tests (validate_rule, capability matrix, loader): `pytest tests/test_rules.py`
  - Builtins tests (improve/workflow/saved_workflow_exists): `pytest tests/test_nudge_builtins.py`
  - Skill tests: `pytest tests/test_skill.py`
  - Integration tests: `pytest tests/test_integration.py`
  - Plan guidance tests: `pytest tests/test_plan_guidance.py`

**Installation:**
- Add marketplace: `claude plugin marketplace add severity1/severity1-marketplace`
- Via marketplace: `claude plugin install prompt-improver@severity1-marketplace`
- Local dev: `claude plugin marketplace add /path/to/claude-code-prompt-improver/.dev-marketplace/.claude-plugin/marketplace.json` then `claude plugin install prompt-improver@local-dev`
- Manual: copy `scripts/engine.py`, `scripts/rules.py`, `scripts/nudge_builtins.py`, and the whole `nudges/` tree with `cp -r` (keep `scripts/` and `nudges/` siblings), then add per-event `engine.py <EventName>` dispatch entries to settings.json
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: architecture -->
## Architecture

**Engine Layer (scripts/):**
- `engine.py`: Event dispatcher and sole entry point - invoked as `engine.py <EventName>`
  - Reads stdin once; treats empty/invalid JSON as `{}` (centralizes exit-0)
  - Runs the event's rules (each wrapped in try/except so one bad rule cannot suppress others), merges `inject_context` fragments by `priority` with a blank-line join
  - `_render_action` evaluates `append_when` clauses against the rule's `match_target` value (not hardcoded prompt) - required for non-prompt targets like `agent_type`
  - Emits one `hookSpecificOutput` object; exits 0 always - missing/unknown event or no rules is a clean no-op that never reads stdin
- `rules.py`: JSON loader, `validate_rule`, the event->capability matrix, `rules_for(event)`
  - Loads/validates `nudges/<EventName>/*.json` (recursive glob); each rule's `event` field must match its parent directory name - mismatches skipped with a stderr note; files loose in `nudges/` root are also skipped; loading never raises
  - Regexes compiled once per dispatched event, not at file load
- `nudge_builtins.py`: The escape hatch - two allowlist dicts, `MATCHERS` and `HANDLERS`
  - `HANDLERS`: `improve` (clarity wrapper, owns `*`/`/`/`#` bypass), `workflow` (model-routing guidance, owns keyword/slash detection + `*`/`#` bypass)
  - `MATCHERS`: `saved_workflow_exists` (saved-workflow filesystem scan, resolves cwd/HOME at call time)
  - Referenced by string name only; unknown name = load-time skip + stderr. Never `eval`/`importlib`/`getattr`-on-path
  - Named `nudge_builtins` (not `builtins`) because the stdlib `builtins` is loaded before user code and would permanently shadow a local `builtins.py`

**Nudge Registry (nudges/<EventName>/*.json):**
- `nudges/UserPromptSubmit/00-improve.json` - `improve` handler, always-fires clarity wrapper
- `nudges/UserPromptSubmit/10-workflow.json` - `workflow` handler, workflow routing guidance
- `nudges/UserPromptSubmit/20-background-exec.json` - pure data, keyword match, self-cancelling reminder to background long-running processes
- `nudges/PreToolUse/00-plan.json` - pure data, matcher EnterPlanMode, plan readability guidance
- `nudges/SubagentStart/00-subagent-routing.json` - pure data, match_target agent_type, breadth-over-depth guidance for Explore/Plan agents

**Skill Layer (skills/prompt-improver/):**
- `SKILL.md`: Research and question workflow
  - 4-phase process: Research, Questions, Clarify, Execute
  - Assumes prompt already determined vague by the improve nudge
  - Links to reference files for progressive disclosure
- `references/`: Detailed guides loaded on-demand
  - `question-patterns.md`: Question templates and effective patterns
  - `research-strategies.md`: Context gathering strategies
  - `examples.md`: Real prompt transformations

**Directory structure:**
- `scripts/` - Engine implementation (engine.py, rules.py, nudge_builtins.py)
- `nudges/` - Declarative rule rows, organized as `nudges/<EventName>/*.json`
- `skills/prompt-improver/` - Skill and reference files
- `tests/` - Test suite (engine, rules, nudge_builtins, skill, integration, plan_guidance)
- `hooks/` - Hook configuration (hooks.json, auto-discovered)
- `.claude-plugin/` - Plugin metadata
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: conventions -->
## Code Conventions

**Hook output format:**
- JSON structure following Claude Code specification
- UserPromptSubmit format: `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}`
- PreToolUse/SubagentStart format: same shape with the matching `hookEventName`
- The engine echoes the dispatched event name into `hookEventName`
- Exit code 0 for all success paths and all no-op paths
- Hook commands use `python3 || python` fallback for Windows compatibility

**Declarative nudge schema (nudges/<EventName>/*.json):**
- Each rule: `id` (required), `event` (required, validated against the capability matrix), `description` (optional, never emitted)
- Exactly one of `action` (pure data: `{type: inject_context, text: [lines], append_when: [...]}`) or `handler` (string naming a callable in `nudge_builtins.HANDLERS`)
- `text` is an array of lines joined with newlines at load (clean multiline diffs)
- `append_when` clauses match against the rule's `match_target` value (not always the prompt) - required for rules with `match_target: agent_type` or `tool_name`
- Optional `criteria` (absent = always fire): `match`/`exclude` regex arrays, `match_target` (prompt|tool_name|agent_type), `non_slash`, `flags`, `builtin` (allowlisted matcher name)
- Optional `bypass` (default suppresses on `*`/`#`/empty for prompt targets; `none` disables) and `priority` (int merge order, lower first)

**Plugin auto-discovery:**
- Do NOT add `hooks` field to `plugin.json` - `hooks/hooks.json` at standard location is auto-discovered
- Do NOT add `skills` field to `plugin.json` - `skills/` directory at standard location is auto-discovered
- Integration test `test_plugin_configuration` asserts both fields are absent

**Bypass prefixes:**
- `*` prefix: Skip evaluation entirely, strip prefix from prompt (improve emits the bare prompt)
- `/` prefix: Slash commands bypass automatically
- `#` prefix: Memorize commands bypass automatically
- Default `bypass` policy in the engine suppresses prompt-targeted criteria rules on `*`/`#`/empty; handlers own their own bypass logic

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
- Engine tests run `engine.py <event>` via subprocess and validate merged JSON output
  - `test_rules_for_raising_still_exits_zero`: in-process monkeypatch; forces `rules_for` to raise, asserts `main()` still exits 0 (issue #1)
  - `test_drop_in_fixture_nudge_fires_end_to_end`: writes a fixture nudge JSON, verifies it fires on trigger and is absent on non-match, cleans up in finally (extensibility guarantee)
  - `test_append_when_respects_match_target`: fixture nudge with `match_target=agent_type` and `append_when`; verifies appended text appears when agent_type matches (issue #3)
- Builtins tests unit-test `improve`/`workflow`/`saved_workflow_exists` in-process
- Rules tests cover `validate_rule` rejection cases, the capability matrix, and the loader
- Skill tests validate file structure, frontmatter, and references
- Integration tests verify end-to-end flow and architecture separation
- Python standard library only (json, sys, subprocess, pathlib, re, copy)
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: patterns -->
## Detected Patterns

**Declarative dispatch:**
- One engine, many events: `engine.py <EventName>` runs only that event's rules
- A new inject-context capability is a `nudges/<EventName>/*.json` row, not a new script; the directory name is authoritative for the event
- Pure-data rules (action) vs escape-hatch rules (handler) - exactly one per rule
- Fragments merge by `priority` with a blank-line join, reproducing the old multi-hook concatenation

**Progressive disclosure:**
- Clear prompts: evaluation only, no skill load
- Vague prompts: evaluation + skill load + references
- Reference materials load only when needed
- Zero context penalty for unused reference materials

**Evaluation flow:**
1. Engine runs the improve nudge, which wraps the prompt with evaluation instructions
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
- Collapsed three separate hook scripts into one declarative engine driven by a JSON nudge registry; a new inject-context capability is now a data row, not a new script
- Escape-hatch module named `nudge_builtins` (not `builtins`) because the stdlib `builtins` is loaded before user code and would permanently shadow a local `builtins.py`; handlers/matchers referenced by allowlisted string name only (no eval/importlib)
- Added SubagentStart nudge (model/token-efficiency guidance per agent type) - a capability the old script layer could not express

**Evolution:**
- Started as embedded evaluation logic in hook script
- Extracted skill layer to separate evaluation (hook) from enrichment (skill)
- Added marketplace support for distribution
- Adopted subagent-first research dispatch: broad exploration (Glob, Grep, WebSearch, WebFetch, multi-file Read) routed through Task/Explore to isolate main context
- Added plan-guidance.py as a second hook script targeting plan mode entry
- Added workflow-guidance.py as a third hook script injecting model-routing guidance for dynamic workflow requests
- Refactored to a declarative engine: `improve`/`workflow` became named handlers in `nudge_builtins.py`, `plan` became a pure-data nudge row, the three scripts and their two test files were deleted, and the test harness was rewritten onto the engine/rules/builtins seams (parity verified byte-for-byte against the old scripts)
- Reorganized nudges/ from flat (`nudges/*.json`) to per-event subdirectories (`nudges/<EventName>/*.json`); the loader now globs recursively and enforces that each rule's `event` field matches its parent directory name - files loose in `nudges/` root are skipped; deleted `nudges/mcp-tools.json`
<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: best-practices -->
## Best Practices

- Keep the engine minimal - it runs on every prompt submission; never add heavy imports or network calls
- Prefer a pure-data `nudges/<EventName>/*.json` row over a new handler; reach for a handler only when bypass logic or filesystem access is genuinely needed
- Add new handlers/matchers to the `nudge_builtins` allowlist dicts by string name only - never use eval/importlib/getattr-on-path
- Never rename `nudge_builtins` to `builtins` - the stdlib module shadows any local `builtins.py` and the import silently resolves to stdlib
- Resolve cwd/HOME at call time in matchers (not module load) so tests can relocate them via monkeypatch
- A new event needs one dispatch entry in `hooks.json`, an entry in the `rules.py` capability matrix, and a `nudges/<EventName>/` subdirectory; keep tool matchers (e.g. EnterPlanMode) in `hooks.json` so the interpreter is not spawned on every tool call
- Reference files should be self-contained so they work when loaded independently
- Test bypass prefixes whenever modifying handler logic to prevent breaking slash commands
- When writing skill research steps, always pass file paths, errors, and prior decisions into every Explore prompt - Explore has no conversation history access
- Never call Glob, Grep, WebSearch, or WebFetch directly in main skill context - route them through Task/Explore to preserve context isolation
- The workflow handler gates filesystem scanning behind a leading "/" check - non-slash prompts do zero I/O; preserve this pattern
- The workflow handler uses a conditional guard in its guidance to handle false positives at the model level - preserve this pattern when modifying guidance text
- `_render_action` evaluates `append_when` clauses against the rule's `match_target` (not hardcoded prompt) - preserve this when modifying `_render_action` or rules with non-prompt targets
<!-- END AUTO-MANAGED -->

<!-- MANUAL -->
## Design Philosophy

- **Rarely intervene** - Most prompts pass through unchanged
- **Trust user intent** - Only ask when genuinely unclear
- **Use conversation history** - Avoid redundant exploration
- **Max 1-6 questions** - Enough for complex scenarios, still focused
- **Transparent** - Evaluation visible in conversation
<!-- END MANUAL -->
