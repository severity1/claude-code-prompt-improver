# Claude Code Prompt Optimizer

Automatically clarifies vague prompts before Claude Code executes them, so you get better results without back-and-forth.

## What It Does

When you submit a vague prompt like `"fix the bug"` or `"add tests"`, this hook:
- Explores your project to understand the context
- Asks targeted questions with real options from your codebase (actual file names, not generic choices)
- Creates an enriched prompt based on your answers
- Asks for your confirmation before executing

The result: Claude has all the context needed to do the work right the first time.

## How It Works

```
User submits prompt: "fix the map"
         ↓
Hook intercepts via UserPromptSubmit event
         ↓
Main Claude spawns subagent
         ↓
Subagent workflow:
  1. Explores project (Glob/Grep for map-related files)
  2. Evaluates if prompt is clear (uses AI judgment)
  3. If vague: Asks questions with actual file paths found
  4. Synthesizes enriched prompt from answers
  5. Shows optimized prompt, asks for confirmation
         ↓
User confirms optimized prompt
         ↓
Subagent returns approved prompt to main Claude
         ↓
Main Claude executes with enriched context
(subagent session discarded, context window stays clean)
```

## Architecture

**Why Subagents?**

The hook uses an isolated subagent session for optimization to keep your main Claude session clean and token-efficient.

**Design Philosophy:**

The optimizer is designed to be helpful without being annoying:
- Only asks questions when clarification would significantly improve results
- Keeps questions to 1-2 maximum (no interrogations)
- Infers context from project exploration when possible
- Errs on the side of proceeding rather than over-questioning
- "Good enough" prompts pass through unchanged

**Without subagent architecture:**
- Main session gets cluttered with exploration (file searches, questions, etc.)
- Uses 80k+ tokens: 30k exploration + 20k Q&A + 30k actual work
- Less room for complex tasks
- Optimization overhead visible in conversation

**With subagent architecture:**
- Optimization happens in isolated session (then discarded)
- Main session: 35k tokens for actual work only
- Subagent session: 40k tokens (exploration + Q&A), then thrown away
- Main session stays focused and efficient
- User sees only the final optimized prompt

**Key Components:**

1. **Hook Script** (`optimize-prompt.py`)
   - Intercepts prompts via stdin/stdout JSON
   - Wraps prompt with subagent instructions
   - Handles bypass logic (prompts starting with `!` or `/`)

2. **Subagent**
   - Explores project using available tools (Glob, Grep, Read)
   - Uses AI judgment (no hardcoded rules)
   - Asks context-aware questions with real options from codebase
   - Confirms optimized prompt with user before returning

3. **Main Session (Claude Sonnet)**
   - Receives optimized prompt from subagent
   - Executes task with full context
   - No optimization details in context window

## Why Use This

**Without optimizer:**
```bash
$ claude "fix the map"
Claude: Which map component? What's the issue?
You: The marker rendering
Claude: In which file?
You: Map.tsx
Claude: What's wrong with it?
You: Markers aren't showing...
```

**With optimizer:**
```bash
$ claude "fix the map"
Hook: Which component needs fixing?
  - src/components/Map.tsx (main map component)
  - src/components/MapMarkers.tsx (marker rendering)
  - src/stores/mapStore.ts (map state)
You: [select MapMarkers.tsx] Markers stopped showing after update
Hook: Optimized prompt: "Fix marker rendering in MapMarkers.tsx..."
You: [confirm]
Claude: [immediately starts fixing with full context]
```

## Installation

**1. Copy the hook script:**
```bash
cp hooks/optimize-prompt.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/optimize-prompt.py
```

**2. Add to your Claude settings:**

Edit `~/.claude/settings.json` and add:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/optimize-prompt.py"
          }
        ]
      }
    ]
  }
}
```

**Note:** The hook follows the [official UserPromptSubmit pattern](https://docs.claude.com/en/docs/claude-code/hooks-guide) with JSON input/output. No timeout is specified since the optimization process may need time for project exploration and user questions.

That's it. The hook will now run automatically on every prompt.

## Usage

**Normal use** - Just use Claude Code as usual:
```bash
claude "fix the bug"
claude "add tests"
claude "refactor the auth code"
```

The hook runs automatically and will ask clarifying questions if needed.

**Skip optimization** - Prefix with `!` when you want immediate execution:
```bash
claude "! add dark mode"
```

**Slash commands** - Automatically bypass optimization (e.g., `/help`, `/commit`, custom commands):
```bash
claude "/help"
claude "/commit"
```


## Examples

### Vague Request Gets Clarified

**You type:**
```bash
claude "fix the error"
```

**Hook asks:**
```
Which error needs fixing?
  ○ TypeError in src/components/Map.tsx (recent change)
  ○ API timeout in src/services/osmService.ts
  ○ Other (paste error message)
```

**You select Map.tsx and paste the error**

**Hook shows optimized prompt:**
```
Fix TypeError in src/components/Map.tsx line 42: Cannot read property
'current' of undefined when accessing map.current. Check useEffect dependencies.
```

**You confirm, Claude executes with full context**

---

### Incomplete Feature Gets Scoped

**You type:**
```bash
claude "add authentication"
```

**Hook asks:**
```
Which authentication method?
  ○ OAuth 2.0
  ○ JWT
  ○ Session cookies

What features? (select multiple)
  ☑ Login/signup UI
  ☑ Protected routes
  ☑ Token refresh
  ☑ State persistence
```

**Hook shows optimized prompt, you confirm, done**

---

### Clear Prompt Passes Through

**You type:**
```bash
claude "Fix TypeScript error in src/components/Map.tsx line 127 where
mapboxgl.Map constructor is missing the container option"
```

**Hook evaluates:** Already specific, proceeds immediately with no questions

## FAQ

**Does this work on all prompts?**
Yes, unless you prefix with `!` to bypass. The hook uses AI judgment to decide if optimization is needed.

**Will this slow down my workflow?**
Only slightly during the question phase. The actual execution is faster because Claude has better context upfront.

**Can I customize the behavior?**
The hook adapts to each project automatically by exploring your codebase and CLAUDE.md file.

**What if I don't like the optimized prompt?**
You can select "Use original instead" when the hook asks for confirmation.

**Will I get bombarded with questions?**
No. The optimizer is designed to ask at most 1-2 questions and only when absolutely necessary. If it can infer context from exploring your project, it will do that instead of asking.

## License

MIT
