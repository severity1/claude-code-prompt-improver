# Claude Code Skill Builder

A tool to help you create custom Claude Code hooks easily from templates.

## What is the Skill Builder?

The Skill Builder is a CLI tool that helps you create new Claude Code hooks without writing boilerplate code. It provides templates for common hook patterns and an interactive wizard to customize them for your needs.

## Quick Start

### 1. List Available Templates

```bash
./skill-builder.py list
```

This shows all available hook templates with descriptions.

### 2. View Template Details

```bash
./skill-builder.py info wrapper
```

Get detailed information about a specific template.

### 3. Create a New Hook

```bash
./skill-builder.py create simple
```

This launches an interactive wizard that guides you through creating a new hook.

## Available Templates

### 1. **simple** - Basic Pass-Through Hook

A minimal hook that logs prompts and passes them through unchanged.

**Use cases:**
- Starting point for custom hooks
- Debugging and monitoring
- Learning how hooks work

**Features:**
- Logs prompts to a file
- Basic error handling
- Clean structure for extending

**Example:**
```bash
./skill-builder.py create simple
# Creates a hook that logs all prompts to /tmp/claude-code-hooks.log
```

---

### 2. **wrapper** - Prompt Wrapper Hook

Wraps user prompts with additional instructions or context (like the improve-prompt.py hook).

**Use cases:**
- Add systematic instructions to all prompts
- Enforce coding standards
- Apply consistent guidelines

**Features:**
- Bypass conditions (*, /, # prefixes)
- Safe string escaping
- Customizable wrapper text

**Example:**
```bash
./skill-builder.py create wrapper
# Creates a hook that adds custom instructions to every prompt
```

**Customization example:**
```python
wrapped_prompt = f"""SECURITY REVIEW MODE

Original request: "{escaped_prompt}"

Before executing, please:
1. Check for security vulnerabilities
2. Validate all inputs
3. Follow OWASP best practices

Then execute the original request.
"""
```

---

### 3. **validator** - Input Validation Hook

Validates prompts against rules before execution.

**Use cases:**
- Enforce prompt standards
- Block inappropriate content
- Require certain patterns or keywords

**Features:**
- Configurable validation rules
- Helpful error messages
- Extensible rule system

**Example:**
```bash
./skill-builder.py create validator
# Creates a hook that validates prompts against custom rules
```

**Customization example:**
```python
# Add custom validation rules
if len(prompt) < 10:
    raise ValidationError("Please provide more details (min 10 characters)")

if not re.search(r'\b(add|fix|update|create)\b', prompt, re.I):
    raise ValidationError("Please start with an action verb")
```

---

### 4. **context-injector** - Automatic Context Hook

Automatically adds contextual information to prompts.

**Use cases:**
- Add project information automatically
- Include environment details
- Inject external data or configurations

**Features:**
- Load context from files or commands
- Git branch, project name, timestamps
- Extensible context sources

**Example:**
```bash
./skill-builder.py create context-injector
# Creates a hook that adds project context to every prompt
```

**Customization example:**
```python
# Add custom context sources
def get_project_context():
    context = []

    # Load from package.json
    if Path("package.json").exists():
        with open("package.json") as f:
            data = json.load(f)
            context.append(f"Project: {data['name']} v{data['version']}")

    # Add team conventions
    if Path(".conventions.md").exists():
        with open(".conventions.md") as f:
            context.append(f"Team conventions:\n{f.read()}")

    return "\n".join(context)
```

---

### 5. **conditional** - Conditional Routing Hook

Routes prompts to different behaviors based on patterns.

**Use cases:**
- Apply different rules for different prompt types
- Specialized handling for code reviews, bug fixes, etc.
- Context-aware prompt transformation

**Features:**
- Pattern matching with regex
- Multiple routing rules
- Fallback behavior

**Example:**
```bash
./skill-builder.py create conditional
# Creates a hook that routes prompts based on content
```

**Customization example:**
```python
# Add custom routing rules
if re.search(r'\brefactor\b', prompt, re.I):
    return f"""REFACTORING MODE

Please refactor with focus on:
- Code readability
- Maintainability
- Performance
- Design patterns

Original request: {prompt}
"""
```

## Usage Examples

### Interactive Mode (Recommended)

```bash
./skill-builder.py create wrapper
```

The wizard will ask you:
1. Hook name (e.g., "security-wrapper")
2. Hook description
3. Template-specific customizations
4. Output path (default: hooks/your-hook-name.py)

### Non-Interactive Mode

```bash
./skill-builder.py create simple -o hooks/my-logger.py --non-interactive
```

Creates a hook from template without prompts (uses default values).

## Installing Your Hook

After creating a hook, add it to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/your/hook.py"
      }]
    }]
  }
}
```

**Multiple hooks:**
```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [
        {
          "type": "command",
          "command": "python3 ~/.claude/hooks/validator.py"
        },
        {
          "type": "command",
          "command": "python3 ~/.claude/hooks/context-injector.py"
        },
        {
          "type": "command",
          "command": "python3 ~/.claude/hooks/improve-prompt.py"
        }
      ]
    }]
  }
}
```

Hooks run in order - output of one becomes input to the next.

## Customizing Templates

All templates are designed to be customized:

1. **Start with a template** - Get the basic structure
2. **Modify the logic** - Add your specific rules and behavior
3. **Test thoroughly** - Ensure it works with various inputs
4. **Share with team** - Commit to your project's hooks directory

## Hook Development Tips

### 1. Always Handle JSON I/O

```python
import json
import sys

# Read
input_data = json.load(sys.stdin)
prompt = input_data.get("prompt", "")

# Write
print(prompt)  # or modified_prompt
sys.exit(0)
```

### 2. Escape Strings for Wrapped Prompts

```python
escaped = prompt.replace("\\", "\\\\").replace('"', '\\"')
```

### 3. Support Bypass Conditions

```python
# Let slash commands and memorize pass through
if prompt.startswith("/") or prompt.startswith("#"):
    print(prompt)
    sys.exit(0)
```

### 4. Handle Errors Gracefully

```python
try:
    # Your logic
except Exception as e:
    print(f"Error in hook: {e}", file=sys.stderr)
    print(prompt)  # Pass through on error
    sys.exit(0)
```

### 5. Test with Edge Cases

- Empty prompts
- Very long prompts
- Special characters
- Multi-line prompts
- Unicode characters

## Advanced: Creating Custom Templates

You can add your own templates to `skill-builder/templates/`:

1. Create `your-template.py` with placeholders:
   - `{{HOOK_NAME}}` - Replaced with user's hook name
   - `{{HOOK_DESCRIPTION}}` - Replaced with description
   - `{{CUSTOM_PLACEHOLDER}}` - For template-specific customizations

2. Add metadata to `metadata.json`:
```json
{
  "your-template": {
    "description": "Brief description",
    "use_case": "When to use this template",
    "features": ["Feature 1", "Feature 2"],
    "customization": ["What can be customized"]
  }
}
```

3. (Optional) Add custom prompts in `skill-builder.py`:
```python
elif template_name == "your-template":
    custom_value = input("Enter custom value: ").strip()
    customizations['custom'] = custom_value
```

## Examples from the Community

### Example 1: Code Standard Enforcer

```python
# Created with: ./skill-builder.py create wrapper
wrapped_prompt = f"""CODE STANDARDS

Original: "{escaped_prompt}"

Follow our standards:
- Use TypeScript strict mode
- All functions must have JSDoc
- Max line length: 100
- Use async/await (no .then())

Execute the request following these standards.
"""
```

### Example 2: Test-First Development Hook

```python
# Created with: ./skill-builder.py create conditional
if re.search(r'\b(add|create|implement)\b', prompt, re.I):
    return f"""TEST-FIRST DEVELOPMENT

Original: "{prompt}"

Please:
1. Write tests FIRST
2. Implement to pass tests
3. Refactor if needed

Execute the request using TDD.
"""
```

### Example 3: Security-First Hook

```python
# Created with: ./skill-builder.py create validator
SECURITY_KEYWORDS = ['eval', 'exec', 'os.system', 'subprocess.shell']
for keyword in SECURITY_KEYWORDS:
    if keyword in prompt.lower():
        raise ValidationError(
            f"Potentially unsafe operation: {keyword}. "
            f"Please confirm this is intentional and necessary."
        )
```

## Troubleshooting

### Hook not running?

1. Check `~/.claude/settings.json` syntax
2. Ensure hook has execute permissions: `chmod +x hook.py`
3. Test hook manually:
   ```bash
   echo '{"prompt":"test"}' | python3 hook.py
   ```

### Hook breaking prompts?

1. Check for JSON syntax errors in output
2. Ensure you're not printing debug info to stdout
3. Use stderr for logging: `print("debug", file=sys.stderr)`

### Multiple hooks conflicting?

Remember hooks run in sequence. Output of hook1 → Input of hook2.

Debug by testing each hook individually.

## Contributing

Have a useful template? Submit a PR with:
1. Template file in `skill-builder/templates/`
2. Metadata entry in `metadata.json`
3. Example usage in this README

## Resources

- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [Hooks Guide](https://docs.claude.com/claude-code/hooks)
- [Example Hooks](https://github.com/anthropics/claude-code-examples)

## License

MIT - Same as the claude-code-prompt-improver project.
