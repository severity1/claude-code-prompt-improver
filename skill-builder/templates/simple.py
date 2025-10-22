#!/usr/bin/env python3
"""
{{HOOK_NAME}} - {{HOOK_DESCRIPTION}}

A simple pass-through hook that logs prompts for debugging or monitoring.
This is a great starting point for building custom hooks.
"""
import json
import sys
from datetime import datetime
from pathlib import Path


def log_prompt(prompt: str, log_file: str = "/tmp/claude-code-hooks.log"):
    """Log the prompt to a file"""
    try:
        timestamp = datetime.now().isoformat()
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {prompt}\n")
    except Exception as e:
        print(f"Warning: Failed to log prompt: {e}", file=sys.stderr)


def main():
    # Load input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    prompt = input_data.get("prompt", "")

    # Log the prompt
    log_prompt(prompt)

    # Pass through unchanged
    print(prompt)
    sys.exit(0)


if __name__ == "__main__":
    main()
