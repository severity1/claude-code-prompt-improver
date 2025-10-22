#!/usr/bin/env python3
"""
{{HOOK_NAME}} - {{HOOK_DESCRIPTION}}

A context injector hook that automatically adds contextual information to prompts.
Can load context from files, commands, or environment variables.
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load_context_from_file(file_path: str) -> str:
    """Load context from a file"""
    try:
        with open(file_path) as f:
            return f.read().strip()
    except Exception as e:
        print(f"Warning: Failed to load context from {file_path}: {e}", file=sys.stderr)
        return ""


def load_context_from_command(command: str) -> str:
    """Load context from a shell command"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Warning: Failed to load context from command: {e}", file=sys.stderr)
        return ""


def get_project_context() -> str:
    """
    Get context about the current project.
    CUSTOMIZE this function to return relevant context for your use case.
    """
    context_parts = []

    # Example: Add git branch info
    git_branch = load_context_from_command("git branch --show-current 2>/dev/null")
    if git_branch:
        context_parts.append(f"Git branch: {git_branch}")

    # Example: Add project name from directory
    project_name = Path.cwd().name
    context_parts.append(f"Project: {project_name}")

    # Example: Add timestamp
    context_parts.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Example: Load context from a file (e.g., .claude-context)
    context_file = Path.cwd() / ".claude-context"
    if context_file.exists():
        file_context = load_context_from_file(str(context_file))
        if file_context:
            context_parts.append(f"Custom context:\n{file_context}")

    # Example: Add environment-specific context
    env = os.getenv("ENV", "development")
    context_parts.append(f"Environment: {env}")

    # Add more context sources as needed:
    # - Read from package.json, pyproject.toml, etc.
    # - Get recent git commits
    # - Load team conventions
    # - Include external API data
    # - Add user-specific preferences

    return "\n".join(context_parts)


def main():
    # Load input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    prompt = input_data.get("prompt", "")

    # Skip context injection for slash commands and memorize
    if prompt.startswith("/") or prompt.startswith("#"):
        print(prompt)
        sys.exit(0)

    # Get context
    context = get_project_context()

    # Inject context into prompt
    # You can customize how context is added to the prompt
    if context:
        enhanced_prompt = f"""Context for this request:
{context}

User request: {prompt}

Please consider the above context when executing the request.
"""
    else:
        # No context available, pass through
        enhanced_prompt = prompt

    print(enhanced_prompt)
    sys.exit(0)


if __name__ == "__main__":
    main()
