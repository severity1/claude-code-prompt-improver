# Claude Code Prompt Optimizer

A hook system for Claude Code that automatically evaluates and optimizes vague user prompts using subagent architecture.

## Overview

This hook intercepts user prompts before Claude Code processes them and uses a dedicated subagent to evaluate if clarification would help. The subagent explores the project, asks context-aware questions, and synthesizes an enriched prompt. This keeps your main session's context window clean while ensuring you get the best results.

## Features

- **AI-Powered Evaluation**: Uses Claude's judgment to decide if optimization would help
- **Subagent Architecture**: Isolated sessions for optimization preserve main context window
- **Context-Aware Suggestions**: Questions include actual file paths and options discovered from your codebase
- **Project-Aware**: Leverages CLAUDE.md and explores your specific project structure
- **No Hardcoded Rules**: Relies on Claude's intelligence, not brittle heuristics
- **Token Efficient**: Keeps main session lean by offloading exploration to subagents

## How It Works

```
User: "fix the map"
    ↓
Hook wraps prompt (always evaluates)
    ↓
Main Claude spawns evaluation subagent
    ↓
Subagent uses judgment to:
  - Explore project context
  - Decide if optimization needed
  - If yes: Ask questions with SPECIFIC options from codebase
  - Build enriched prompt
  - Show optimized prompt and ask user for confirmation
    ↓
Main Claude receives approved prompt
    ↓
Executes task with full context (clean session)
```

## Installation

1. **Install the hook:**
   ```bash
   cp hooks/optimize-prompt.py ~/.claude/hooks/
   chmod +x ~/.claude/hooks/optimize-prompt.py
   ```

2. **Configure Claude Code:**

   Add to `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "UserPromptSubmit": [
         {
           "matcher": "*",
           "hooks": [
             {
               "type": "command",
               "command": "python3 ~/.claude/hooks/optimize-prompt.py",
               "timeout": 2
             }
           ]
         }
       ]
     }
   }
   ```

3. **Optional: Project-specific config:**

   For project-specific optimization, copy to `.claude/settings.json` in your project.

## Usage

### Default Behavior

Just use Claude Code normally. The optimizer runs automatically on prompts:

```bash
claude "fix the bug"
# → Optimizer explores codebase, finds recent error logs
# → Asks: "Which bug?" with options based on what it found

claude "add tests"
# → Optimizer searches for test files and testable components
# → Asks: "Add tests for which component?" with actual component names
```

### Bypass Optimization

Start your prompt with `!` to skip evaluation entirely:

```bash
claude "! add dark mode"
# → Executes immediately without subagent evaluation
```

## Configuration

### How Evaluation Works

The hook **always** spawns a subagent to evaluate prompts (unless bypassed with `!`). The subagent uses its judgment and available tools to decide if optimization is needed - no hardcoded rules or thresholds.

**Benefits:**
- Adapts to context (what's clear in one project may be vague in another)
- Learns from project patterns (CLAUDE.md, architecture, conventions)
- No maintenance of brittle heuristics
- Smarter decisions than word-count rules

### Context-Aware Suggestions

The key feature is **rich, specific suggestions** based on actual discovery:

**Bad (generic):**
```
Question: "Which file should I work with?"
Options: [File 1 | File 2 | File 3]
```

**Good (context-aware):**
```
Question: "Which map component should I fix?"
Options:
  - src/components/Map.tsx (main map component)
  - src/components/MapMarkers.tsx (marker rendering)
  - src/stores/mapStore.ts (map state management)
```

The subagent searches your codebase first, then offers actual findings as options.

## Architecture

### Subagent Benefits

**Without Subagent:**
```
Main Session: 80k tokens used
├─ Prompt exploration: 30k
├─ User Q&A: 20k
└─ Actual work: 30k
Risk: Context limit, less room for complex tasks
```

**With Subagent:**
```
Main Session: 35k tokens used
└─ Actual work: 35k (optimization details not included)

Subagent Session: 40k tokens used (then discarded)
├─ Project exploration: 20k
├─ User Q&A: 15k
└─ Prompt synthesis: 5k
```

### Evaluation Approach

The hook **always** spawns a subagent (no pre-filtering). The subagent then:

1. **Explores** - Uses judgment and tools to understand project context
2. **Evaluates** - Decides if the prompt is clear enough to execute well
3. **Optimizes (if needed)** - Asks targeted questions with context-specific options
4. **Confirms** - Shows optimized prompt and asks user for approval
5. **Returns** - Approved prompt or original (with confidence score)

No prescriptive steps - the subagent adapts its approach to the specific prompt and project.

## Examples

### Example 1: Vague Fix Request

```
User: "fix the error"

Subagent:
1. Checks recent git changes → finds modified files
2. Greps for error patterns → finds try/catch blocks
3. Asks: "Which error?" with options:
   - TypeError in src/components/Map.tsx (recent change)
   - API timeout in src/services/osmService.ts (has error handling)
   - [Other - paste error message]
4. User selects Map.tsx
5. Asks to paste error if available
6. User: [pastes TypeError details]
7. Subagent synthesizes and shows:
   "Fix TypeError in src/components/Map.tsx line 42: Cannot read
   property 'current' of undefined when accessing map.current. This
   occurs during component initialization. Check useEffect dependencies."
8. Asks: "Happy with this optimized prompt?"
   Options: [Yes, use this | Needs adjustment | Use original instead]
9. User: "Yes, use this"

Optimized prompt sent to main Claude session.
```

### Example 2: Incomplete Feature Request

```
User: "add authentication"

Subagent:
1. Checks package.json → no auth libraries found
2. Reads CLAUDE.md → no auth patterns documented
3. Globs for auth files → none exist (new feature)
4. Asks: "Which authentication method?"
   Options: [OAuth 2.0 | JWT | Session cookies]
5. User: "JWT"
6. Asks: "What should it include?" (multi-select)
   Options based on typical JWT patterns:
   - Login/signup UI components
   - Protected route wrapper
   - Token refresh logic
   - Auth state persistence
7. User: [selects all]
8. Subagent synthesizes and shows:
   "Implement JWT authentication system:
   - Add login/signup UI components
   - Create auth context for token management
   - Add protected route HOC/wrapper
   - Implement token refresh logic
   - Persist auth state to localStorage
   Follow project patterns from CLAUDE.md for state management."
9. Asks: "Happy with this optimized prompt?"
   User: "Yes, use this"

Optimized prompt sent to main Claude session.
```

### Example 3: Already Clear Prompt

```
User: "Fix the TypeScript error in src/components/Map.tsx line 127
where mapboxgl.Map constructor is missing the container option"

Subagent:
1. Evaluates: Specific file, line number, exact error, clear fix
2. Returns: Original prompt unchanged (high confidence)

Main Claude: Proceeds immediately with fix
```

## Development

### Project Structure

```
claude-prompt-optimizer/
├── hooks/
│   └── optimize-prompt.py          # Main hook script (102 lines)
├── examples/
│   ├── settings.json               # Example hook config
│   └── project-claude-md.example   # Example CLAUDE.md
├── tests/
│   └── test-prompts.md             # Test cases
├── README.md
└── LICENSE
```

### Testing

Test the hook with various prompt types:

```bash
# Test vague prompts
python3 hooks/optimize-prompt.py < test-inputs/vague.json

# Test detailed prompts
python3 hooks/optimize-prompt.py < test-inputs/detailed.json
```

See `tests/test-prompts.md` for comprehensive test cases.

## Key Principle

**Don't be prescriptive** - Trust Claude to use its judgment and tools appropriately.

**Do emphasize** - Questions must include rich, context-specific suggestions based on actual codebase discovery, not generic options.

## License

MIT

## Credits

Created from brainstorming session about improving Claude Code UX through intelligent prompt optimization with subagent architecture.
