# Changelog

All notable changes to the Claude Code Prompt Improver project.

## [0.3.2] - 2025-11-05

### Fixed
- Plugin hook registration by correcting marketplace source path from `./../` to `./../../` to properly resolve to project root
- Hooks now register correctly when installed as plugin (previously showed "Registered 0 hooks from 1 plugins")

### Changed
- Hook output format switched to JSON following Claude Code official specification
- Output structure: `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}`
- Exit code remains 0 for all success paths

### Added
- Local plugin installation documentation as recommended development method
- Verification instructions using `/plugin` command
- Two installation options in README: plugin (Option 1) and manual (Option 2)

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