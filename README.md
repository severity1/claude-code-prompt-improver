# Claude Code Prompt Optimizer

A sophisticated hook system for Claude Code that automatically evaluates and optimizes vague user prompts using subagent architecture.

## Overview

This hook intercepts user prompts before Claude Code processes them, evaluates if they need clarification, and uses a dedicated subagent to gather context and optimize the prompt. This keeps your main session's context window clean while ensuring you always get the best results.

## Features

- **Intelligent Evaluation**: Analyzes prompts for clarity, specificity, and actionability
- **Subagent Architecture**: Uses isolated sessions for optimization to preserve main context
- **Interactive Clarification**: Uses AskUserQuestion picker UI for smooth user experience
- **Project-Aware**: Reads CLAUDE.md and explores codebase for context
- **Configurable**: Easy bypass mechanisms and customization options
- **Token Efficient**: Keeps main session lean by offloading exploration to subagents

## How It Works

```
User: "fix the map"
    ↓
Hook intercepts and wraps prompt
    ↓
Main Claude spawns optimization subagent
    ↓
Subagent:
  - Reads project docs (CLAUDE.md)
  - Explores codebase (Glob/Grep)
  - Asks clarifying questions (AskUserQuestion)
  - Builds enriched prompt
    ↓
Main Claude receives optimized prompt
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

Just use Claude Code normally. The optimizer runs automatically on vague prompts:

```bash
claude "fix the bug"
# → Optimizer asks: "Which bug? In which file?"

claude "add tests"
# → Optimizer asks: "What kind of tests? For which components?"
```

### Bypass Optimization

Start your prompt with `!` to skip optimization:

```bash
claude "! add dark mode"
# → Executes immediately without optimization
```

### Always Optimize

Start with `@strict` to force optimization even on clear prompts:

```bash
claude "@strict implement user authentication"
# → Always asks clarifying questions
```

## Configuration

### Optimization Thresholds

Edit `optimize-prompt.py` to customize when optimization triggers:

```python
# Prompt length threshold
MIN_WORDS = 5  # Prompts under this are always optimized

# Auto-bypass for detailed prompts
DETAILED_THRESHOLD = 15  # Prompts over this with file refs bypass
```

### Project-Specific Patterns

The hook automatically reads `CLAUDE.md` if it exists and injects project-specific reminders:

```python
# Example: For a React project
if "React" in claude_md_content:
    wrapper += """
Project uses React + TypeScript.
Remind user about component patterns from CLAUDE.md.
"""
```

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

### Decision Tree

The hook uses a simple heuristic for initial triage:

```python
if word_count < 3:
    # Always optimize
elif word_count < 5 and no_file_references:
    # Likely needs optimization
elif word_count > 15 and has_specifics:
    # Probably good as-is
else:
    # Let subagent decide
```

The subagent then does deep evaluation with full project context.

## Examples

### Example 1: Vague Fix Request

```
User: "fix the error"

Subagent:
1. Reads CLAUDE.md
2. Checks recent git changes
3. Asks: "What error? Do you have error messages?"
4. User: "TypeError in Map.tsx"
5. Asks: "Can you paste the error?"
6. User: [pastes error]

Optimized: "Fix TypeError in Map.tsx line 42: Cannot read property
'current' of undefined. This occurs when accessing map.current before
initialization. Check useEffect dependencies."
```

### Example 2: Incomplete Feature Request

```
User: "add authentication"

Subagent:
1. Checks package.json (no auth libraries)
2. Reads CLAUDE.md (no auth patterns documented)
3. Asks: "Which auth method?"
   Options: [OAuth 2.0 | JWT | Session cookies]
4. User: "JWT"
5. Asks: "What should it include?" (multi-select)
   Options: [Login UI | Signup UI | Protected routes | Token refresh]
6. User: [selects all]

Optimized: "Implement JWT authentication system:
- Add login/signup UI components
- Create auth context/store for token management
- Add route protection HOC
- Implement token refresh logic
- Persist auth state to localStorage"
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
│   └── optimize-prompt.py          # Main hook script
├── examples/
│   ├── settings.json               # Example hook config
│   └── project-claude-md.example   # Example CLAUDE.md
├── tests/
│   └── test-prompts.md             # Test cases
├── docs/
│   └── architecture.md             # Detailed design docs
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

## Roadmap

- [ ] Confidence scoring system
- [ ] Learning from past optimizations
- [ ] Multi-language support (Python, Node.js, etc.)
- [ ] Template library for common prompt patterns
- [ ] Analytics dashboard for optimization metrics
- [ ] Integration with Claude Code analytics

## Contributing

Contributions welcome! Please see issues for current priorities.

## License

MIT

## Credits

Created from brainstorming session about improving Claude Code UX through intelligent prompt optimization with subagent architecture.
