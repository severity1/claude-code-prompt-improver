#!/usr/bin/env python3
"""
{{HOOK_NAME}} - {{HOOK_DESCRIPTION}}

A wrapper hook that adds instructions or context to user prompts.
Supports bypass conditions for slash commands and explicit bypasses.
"""
import json
import sys


def main():
    # Load input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    prompt = input_data.get("prompt", "")

    # Escape quotes in prompt for safe embedding in wrapped instructions
    escaped_prompt = prompt.replace("\\", "\\\\").replace('"', '\\"')

    # Check for bypass conditions
    # 1. Explicit bypass with * prefix
    # 2. Slash commands (built-in or custom)
    # 3. Memorize feature (# prefix)
    if prompt.startswith("*"):
        # User explicitly bypassed - remove * prefix
        clean_prompt = prompt[1:].strip()
        print(clean_prompt)
        sys.exit(0)

    if prompt.startswith("/"):
        # Slash command - pass through unchanged
        print(prompt)
        sys.exit(0)

    if prompt.startswith("#"):
        # Memorize feature - pass through unchanged
        print(prompt)
        sys.exit(0)

    # Build the wrapper
    # CUSTOMIZE THIS SECTION with your own instructions
    wrapped_prompt = f"""CUSTOM INSTRUCTIONS

Original user request: "{escaped_prompt}"

Add your custom instructions here. For example:
- Always explain your reasoning
- Follow specific coding standards
- Use particular libraries or patterns
- Apply security checks

Then execute the original request.
"""

    print(wrapped_prompt)
    sys.exit(0)


if __name__ == "__main__":
    main()
