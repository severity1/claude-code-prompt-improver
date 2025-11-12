# Claude Code Prompt Improver

A UserPromptSubmit hook that enriches vague prompts before Claude Code executes them. Uses the AskUserQuestion tool (Claude Code 2.0.22+) for targeted clarifying questions.

![Demo](assets/demo.gif)

## What It Does

Intercepts prompts and evaluates clarity. Claude then:
- Checks if the prompt is clear using conversation history
- For clear prompts: proceeds immediately (zero overhead)
- For vague prompts: invokes the `prompt-improver` skill to create research plan, gather context, and ask 1-6 grounded questions
- Proceeds with original request using the clarification

**Result:** Better outcomes on the first try, without back-and-forth.

**v0.4.0 Update:** Skill-based architecture with hook-level evaluation achieves 31% token reduction. Clear prompts have zero skill overhead, vague prompts get comprehensive research and questioning via the skill.

## How It Works

```mermaid
sequenceDiagram
    participant User
    participant Hook
    participant Claude
    participant Skill
    participant Project

    User->>Hook: "fix the bug"
    Hook->>Claude: Evaluation prompt (~189 tokens)
    Claude->>Claude: Evaluate using conversation history
    alt Vague prompt
        Claude->>Skill: Invoke prompt-improver skill
        Skill-->>Claude: Research and question guidance
        Claude->>Claude: Create research plan (TodoWrite)
        Claude->>Project: Execute research (codebase, web, docs)
        Project-->>Claude: Context
        Claude->>User: Ask grounded questions (1-6)
        User->>Claude: Answer
        Claude->>Claude: Execute original request with answers
    else Clear prompt
        Claude->>Claude: Proceed immediately (no skill load)
    end
```

## Installation

**Requirements:** Claude Code 2.0.22+ (uses AskUserQuestion tool for targeted clarifying questions)

### Option 1: Via Marketplace (Recommended)

**1. Add the marketplace:**
```bash
claude plugin marketplace add severity1/claude-code-marketplace
```

**2. Install the plugin:**
```bash
claude plugin install prompt-improver@claude-code-marketplace
```

**3. Restart Claude Code**

Verify installation with `/plugin` command. You should see the prompt-improver plugin listed.

### Option 2: Local Plugin Installation (Recommended for Development)

**1. Clone the repository:**
```bash
git clone https://github.com/severity1/claude-code-prompt-improver.git
cd claude-code-prompt-improver
```

**2. Add the local marketplace:**
```bash
claude plugin marketplace add /absolute/path/to/claude-code-prompt-improver/.dev-marketplace/.claude-plugin/marketplace.json
```

Replace `/absolute/path/to/` with the actual path where you cloned the repository.

**3. Install the plugin:**
```bash
claude plugin install prompt-improver@local-dev
```

**4. Restart Claude Code**

Verify installation with `/plugin` command. You should see "1 plugin available, 1 already installed".

### Option 3: Manual Installation

**1. Copy the hook:**
```bash
cp scripts/improve-prompt.py ~/.claude/hooks/
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
- **Max 1-6 questions** - Enough for complex scenarios, still focused
- **Transparent** - Evaluation visible in conversation

## Architecture

**v0.4.0:** Skill-based architecture with hook-level evaluation.

**Hook (scripts/improve-prompt.py) - Evaluation Orchestrator:**
- Intercepts via stdin/stdout JSON (~70 lines)
- Handles bypass prefixes: `*`, `/`, `#`
- Wraps prompts with evaluation instructions (~189 tokens)
- Claude evaluates clarity using conversation history
- If vague: Instructs Claude to invoke `prompt-improver` skill

**Skill (skills/prompt-improver/) - Research & Question Logic:**
- **SKILL.md**: Research and question workflow (~170 lines)
  - Assumes prompt already determined vague by hook
  - 4-phase process: Research → Questions → Clarify → Execute
  - Links to reference files for progressive disclosure
- **references/**: Detailed guides loaded on-demand
  - `question-patterns.md`: Question templates (200-300 lines)
  - `research-strategies.md`: Context gathering (300-400 lines)
  - `examples.md`: Real transformations (200-300 lines)

**Flow for Clear Prompts:**
1. Hook wraps with evaluation prompt (~189 tokens)
2. Claude evaluates: prompt is clear
3. Claude proceeds immediately (no skill invocation)
4. **Total overhead: ~189 tokens**

**Flow for Vague Prompts:**
1. Hook wraps with evaluation prompt (~189 tokens)
2. Claude evaluates: prompt is vague
3. Claude invokes `prompt-improver` skill
4. Skill loads research/question guidance
5. Claude creates research plan, gathers context, asks questions
6. **Total overhead: ~189 tokens + skill load**

**Progressive Disclosure Benefits:**
- Clear prompts: Never load skill (zero skill overhead)
- Vague prompts: Only load skill and relevant reference files
- Detailed guidance available without bloating all prompts
- Zero context penalty for unused reference materials

**Why main session (not subagent)?**
- Has conversation history
- No redundant exploration
- More transparent
- More efficient overall

**Manual Skill Invocation:**
You can also invoke the skill manually without the hook:
```
Use the prompt-improver skill to research and clarify: "add authentication"
```

## Token Overhead

**v0.4.0 Update:** 31% reduction through hook-level evaluation

- **Per prompt (v0.4.0):** ~189 tokens (evaluation prompt)
- **Per prompt (v0.3.x):** ~275 tokens (embedded evaluation logic)
- **Reduction:** ~86 tokens saved per prompt (31% decrease)
- **30-message session:** ~5.7k tokens (~2.8% of 200k context, down from 4.1%)
- **Trade-off:** Minimal overhead for better first-attempt results

**Clear prompts benefit:**
- Evaluation happens in hook (~189 tokens)
- Claude proceeds immediately (no skill load)
- Zero skill overhead for clear prompts

**Vague prompts:**
- Evaluation in hook (~189 tokens)
- Skill loads only when needed for research/questions
- Progressive disclosure: reference files load on-demand

## FAQ

**Does this work on all prompts?**
Yes, unless you use bypass prefixes (`*`, `/`, `#`).

**Will it slow me down?**
Only slightly when it asks questions. Faster overall due to better context.

**Will I get bombarded with questions?**
No. It rarely intervenes, passes through most prompts, and asks max 1-6 questions.

**Can I customize behavior?**
It adapts automatically using conversation history, dynamic research planning, and CLAUDE.md.

**What if I don't want improvement?**
Use `*` prefix: `claude "* your prompt here"`

## License

MIT
