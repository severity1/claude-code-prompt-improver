# Changelog

All notable changes to the Claude Code Prompt Improver project.

## [0.4.0] - 2025-11-12

### Major Changes - Skill-Based Architecture with Hook-Level Evaluation

**Architectural refactoring separating evaluation (hook) from research/questioning (skill).**

### Added
- **Skill Structure**: New `skills/prompt-improver/` directory for research and question logic
  - `SKILL.md`: Research and question workflow with YAML frontmatter (~170 lines)
  - `references/question-patterns.md`: Question templates and best practices (200-300 lines)
  - `references/research-strategies.md`: Context gathering approaches (300-400 lines)
  - `references/examples.md`: Real-world transformations (200-300 lines)
- **Skills Configuration**: Added `skills` field to `.claude-plugin/plugin.json` pointing to `./skills/prompt-improver`
- **Casual Preface**: Added friendly notification when prompt is flagged as vague ("Hey! The Prompt Improver Hook flagged your prompt as a bit vague because [reason].") for transparent, approachable clarification process
- **Test Suite**: Comprehensive testing infrastructure
  - `tests/test_hook.py`: Hook bypass logic, evaluation prompt, JSON output (8 tests)
  - `tests/test_skill.py`: YAML validation, file structure, content validation (9 tests)
  - `tests/test_integration.py`: End-to-end flow, plugin config, token overhead (7 tests)
- **Progressive Disclosure**: Skill and reference files load only when prompt is vague
- **Manual Skill Invocation**: Can invoke skill independently: `Use the prompt-improver skill to research and clarify...`

### Changed
- **Hook Architecture**: Refactored `scripts/improve-prompt.py` from 82 to ~71 lines
  - Hook now contains evaluation prompt (~189 tokens)
  - Claude evaluates clarity using conversation history
  - If clear: proceeds immediately (no skill invocation)
  - If vague: Claude invokes skill for research/questions
  - Retains bypass prefix handling (`*`, `/`, `#`)
- **Skill Purpose**: Assumes prompt already determined vague
  - 4-phase workflow: Research → Questions → Clarify → Execute
  - Removed evaluation phase (handled by hook)
  - Focused on systematic research and question generation
- **SKILL.md Writing Style**: Improved to use imperative/infinitive form (removed "you/your" language) per skill-creator best practices
  - Enhanced Phase 1 Research to emphasize checking conversation history first, then reviewing codebase
  - Reorganized Phase 1 with clearer structure: conversation history → codebase review → additional context → document findings
  - Updated YAML frontmatter description to use third-person form
- **Token Overhead**: Reduced from ~275 tokens to ~189 tokens per prompt (31% reduction)
  - Clear prompts: ~189 tokens (evaluation only, no skill load)
  - Vague prompts: ~189 tokens + skill load
  - 30-message session: ~5.7k tokens (down from ~8.3k, 2.8% vs 4.1% of 200k context)
- **Plugin Version**: Updated to 0.4.0
- **Plugin Description**: Updated to reflect skill-based architecture
- **README**: Extensively updated with new architecture documentation
  - Updated "How It Works" diagram showing hook-level evaluation
  - Architecture section explaining hook evaluates, skill enriches
  - Token overhead showing 31% reduction
  - Clear vs vague prompt flows
  - Progressive disclosure benefits
  - Manual skill invocation examples

### Fixed
- Removed `hooks` field from plugin.json to prevent duplicate hooks file error (the standard `hooks/hooks.json` location is auto-discovered by Claude Code)

### Removed
- "Integration with Hook" section from SKILL.md (architectural details not needed for skill execution)
- Unused `evaluation-criteria.md` reference file (evaluation now handled by hook, not skill)

### Benefits
- **Efficient for Clear Prompts**: Evaluation overhead only (~189 tokens), no skill load
- **Comprehensive for Vague Prompts**: Full skill guidance for research and questions
- **Maintainability**: Logic in markdown, easier to update and extend
- **Reusability**: Skill can be invoked manually or by other workflows
- **Testability**: 24 tests (100% passing) validate all components
- **Progressive Disclosure**: Reference materials load only when needed
- **Separation of Concerns**: Hook evaluates, skill provides research/question guidance

### Technical Details
- All file paths use forward slashes (Unix-style) per Claude Code standards
- YAML frontmatter follows official skill specification (name, description)
- Skill name follows constraints: lowercase, hyphens, max 64 chars
- Description under 1024 chars, includes activation triggers
- Reference files self-contained and one-level deep
- Backward compatible: bypass mechanisms unchanged
- All 24 tests passing (8 hook + 9 skill + 7 integration)

## [0.3.2] - 2025-11-05

### Fixed
- Plugin hook registration by correcting marketplace source path from `./../` to `./../../` to properly resolve to project root
- Hooks now register correctly when installed as plugin (previously showed "Registered 0 hooks from 1 plugins")

### Changed
- Hook output format switched to JSON following Claude Code official specification
- Output structure: `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}`
- Exit code remains 0 for all success paths
- Local plugin installation now uses marketplace commands instead of manual settings.json editing

### Added
- Marketplace installation as recommended Option 1 (via severity1/claude-code-marketplace)
- Local plugin installation documentation using marketplace commands as Option 2 (recommended for development)
- Manual hook installation as Option 3 (fallback method)
- Verification instructions using `/plugin` command

## [0.3.1] - 2025-10-24

### Added
- Local development installation section in README with .dev-marketplace setup
- Hooks field in plugin.json to enable automatic hook installation

### Changed
- Simplified plugin.json metadata (removed homepage, repository, license, keywords)
- Updated README installation instructions (removed marketplace section, not yet available)

### Removed
- marketplace.json from .claude-plugin/ (plugin not ready for public marketplace)
- Unnecessary matcher field from hooks.json

## [0.3.0] - 2025-10-20

### Added
- Dynamic research planning based on vague prompts via TodoWrite
- Structured research and question phases in evaluation workflow
- Support for 1-6 questions (increased from 1-2) to handle complex scenarios
- Explicit grounding requirement: questions based on research findings, not generic guesses

### Changed
- Evaluation wrapper now creates custom research plans based on what needs clarification
- Research phase expanded to support any research method (codebase, web, docs, etc.)
- Removed prescriptive language about specific research tools
- Updated PROCEED criteria: "sufficient context" instead of "context from conversation"
- Token overhead increased to ~300 tokens (from ~250) due to enhanced instructions
- Final step clarified: "execute original user request" instead of "proceed with enriched prompt"

### Improved
- More flexible and adaptive to different types of vague prompts
- Better grounding of clarifying questions in actual project context
- Clearer separation between research and questioning phases
- Numbered steps in Phase 1 and Phase 2 for better structure and clarity
- Preface moved to Phase 1 with context requirement explaining why clarification is needed
- Added specific examples for clarification reasons (ambiguous scope, missing context, unclear requirements)
- Critical rules repositioned under "ONLY ASK" section for better visibility during vague prompt evaluation
- Added "Do not rely on base knowledge" rule to prevent pattern-matching from training instead of research
- Step 2 clarified: "Research WHAT NEEDS CLARIFICATION, not just the project" with emphasis on online research for common approaches/best practices
- Step 3 simplified to "Execute research" (removed redundant warning)
- Step 4 explicitly requires using "research findings (not your training)" to prevent premature assumptions
- Specified recommended tools: Task/Explore for codebase, WebSearch for online research, Read/Grep as needed

## [0.2.0] - 2025-10-20

### Added
- Demo gif showing hook in action
- Mermaid sequence diagram in README
- Documentation of Claude Code 2.0.22+ requirement

### Changed
- Renamed project from "optimizer" to "improver" for accuracy
- Simplified bypass output to use plain text consistently
- Updated demo gif speed to 1.5x for more concise demonstration

### Fixed
- LICENSE copyright updated to use GitHub handle

## [0.1.0] - 2025-10-18

### Added
- Main-session evaluation approach (vs. subagent)
- Bypass prefixes: `*` (skip evaluation), `/` (slash commands), `#` (memorize)
- AskUserQuestion tool integration for targeted clarifying questions
- Conversation history awareness to avoid redundant exploration
- Safety improvements and official hook pattern compliance

### Changed
- Refactored from subagent to main-session evaluation
- Moved from heuristic evaluation to context-aware evaluation
- Simplified to non-prescriptive approach with confirmation step

### Removed
- Subagent-based evaluation (moved to main session)
- Heuristic-based prompt classification