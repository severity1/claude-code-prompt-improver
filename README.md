# Claude Code Prompt Improver

A UserPromptSubmit hook that enriches vague prompts before Claude Code executes them.

## What It Does

Intercepts prompts and wraps them with evaluation instructions. Claude then:
- Checks if the prompt is clear using conversation history
- For vague prompts: asks 1-2 targeted questions with context from your codebase
- Proceeds with original or enriched prompt

**Result:** Better outcomes on the first try, without back-and-forth.

## How It Works

```
User: "fix the bug"
         ↓
Hook wraps with evaluation instructions (~250 tokens)
         ↓
Claude evaluates using conversation history
         ↓
Vague? → Explores project → Asks question(s) → Proceeds
Clear? → Proceeds immediately
```

## Installation

**1. Copy the hook:**
```bash
cp hooks/improve-prompt.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/improve-prompt.py
```

**2. Update `~/.claude/settings.json`:**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/improve-prompt.py"
          }
        ]
      }
    ]
  }
}
```

Done. The hook runs automatically on every prompt.

## Usage

**Normal use:**
```bash
claude "fix the bug"      # Hook evaluates, may ask questions
claude "add tests"        # Hook evaluates, may ask questions
```

**Bypass prefixes:**
```bash
claude "* add dark mode"                    # * = skip evaluation
claude "/help"                              # / = slash commands bypass
claude "# remember to use rg over grep"     # # = memorize bypass
```

## Example

**Vague prompt:**
```bash
$ claude "fix the error"
```

Claude asks:
```
Which error needs fixing?
  ○ TypeError in src/components/Map.tsx (recent change)
  ○ API timeout in src/services/osmService.ts
  ○ Other (paste error message)
```

You select an option, Claude proceeds with full context.

**Clear prompt:**
```bash
$ claude "Fix TypeError in src/components/Map.tsx line 127 where mapboxgl.Map constructor is missing container option"
```

Claude proceeds immediately without questions.

## Design Philosophy

- **Rarely intervene** - Most prompts pass through unchanged
- **Trust user intent** - Only ask when genuinely unclear
- **Use conversation history** - Avoid redundant exploration
- **Max 1-2 questions** - No interrogations
- **Transparent** - Evaluation visible in conversation

## Architecture

**Hook (improve-prompt.py):**
- Intercepts via stdin/stdout JSON
- Bypasses: `*`, `/`, `#` prefixes
- Wraps other prompts with evaluation instructions (~250 tokens)

**Main Claude Session:**
- Evaluates using conversation history first
- Explores project only if needed
- Asks minimal questions via AskUserQuestion tool
- Proceeds with original or enriched prompt

**Why main session (not subagent)?**
- Has conversation history
- No redundant exploration
- More transparent
- More efficient overall

## Token Overhead

- **Per wrapped prompt:** ~250-280 tokens
- **30-message session:** ~7.5k tokens (~4% of 200k context)
- **Trade-off:** Small overhead for better first-attempt results

## FAQ

**Does this work on all prompts?**
Yes, unless you use bypass prefixes (`*`, `/`, `#`).

**Will it slow me down?**
Only slightly when it asks questions. Faster overall due to better context.

**Will I get bombarded with questions?**
No. It rarely intervenes, passes through most prompts, and asks max 1-2 questions.

**Can I customize behavior?**
It adapts automatically using conversation history, codebase exploration, and CLAUDE.md.

**What if I don't want optimization?**
Use `*` prefix: `claude "* your prompt here"`

## License

MIT
