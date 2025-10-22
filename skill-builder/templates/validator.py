#!/usr/bin/env python3
"""
{{HOOK_NAME}} - {{HOOK_DESCRIPTION}}

A validator hook that checks prompts against rules before execution.
Rejects prompts that don't meet criteria and provides helpful error messages.
"""
import json
import re
import sys


class ValidationError(Exception):
    """Raised when a prompt fails validation"""
    pass


def validate_prompt(prompt: str) -> None:
    """
    Validate the prompt against various rules.
    Raise ValidationError if validation fails.
    """
    # Skip validation for slash commands
    if prompt.startswith("/") or prompt.startswith("#"):
        return

    # Example validation rules - CUSTOMIZE THESE

    # Rule 1: Minimum length
    MIN_LENGTH = 3
    if len(prompt.strip()) < MIN_LENGTH:
        raise ValidationError(f"Prompt too short. Minimum {MIN_LENGTH} characters required.")

    # Rule 2: No empty prompts
    if not prompt.strip():
        raise ValidationError("Prompt cannot be empty.")

    # Rule 3: No profanity (basic example)
    # CUSTOMIZE this list or use a library for production use
    profanity_list = ["badword1", "badword2"]  # Add your own list
    for word in profanity_list:
        if word.lower() in prompt.lower():
            raise ValidationError(f"Inappropriate content detected. Please rephrase.")

    # Rule 4: Custom pattern requirement (example: must contain a verb)
    # This is just an example - customize as needed
    # if not re.search(r'\b(add|create|fix|update|delete|build|implement)\b', prompt, re.I):
    #     raise ValidationError("Please use an action verb (e.g., add, create, fix, update).")

    # Add more custom rules here
    # Examples:
    # - Require certain keywords for specific tasks
    # - Block dangerous operations
    # - Enforce naming conventions
    # - Check prompt structure


def main():
    # Load input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    prompt = input_data.get("prompt", "")

    # Validate the prompt
    try:
        validate_prompt(prompt)
    except ValidationError as e:
        # Return error to user
        error_message = f"""VALIDATION ERROR

Your prompt was rejected: {str(e)}

Original prompt: "{prompt}"

Please modify your prompt and try again.
"""
        print(error_message)
        sys.exit(0)

    # Prompt passed validation - pass through
    print(prompt)
    sys.exit(0)


if __name__ == "__main__":
    main()
