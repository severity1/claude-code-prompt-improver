#!/usr/bin/env python3
"""
{{HOOK_NAME}} - {{HOOK_DESCRIPTION}}

A conditional hook that routes prompts based on patterns or conditions.
Apply different behaviors for different types of prompts.
"""
import json
import re
import sys


def route_prompt(prompt: str) -> str:
    """
    Route the prompt based on patterns and apply appropriate transformations.
    CUSTOMIZE these rules for your use case.
    """

    # Skip routing for slash commands and memorize
    if prompt.startswith("/") or prompt.startswith("#"):
        return prompt

    # Rule 1: Code review requests
    if re.search(r'\b(review|check|analyze)\b.*\bcode\b', prompt, re.I):
        return f"""CODE REVIEW MODE

Original request: "{prompt}"

Please perform a thorough code review including:
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Security concerns
- Suggestions for improvement

Then execute the original request.
"""

    # Rule 2: Bug fix requests
    if re.search(r'\b(fix|debug|solve)\b.*\b(bug|error|issue|problem)\b', prompt, re.I):
        return f"""BUG FIX MODE

Original request: "{prompt}"

Please follow this systematic debugging process:
1. Understand the bug (read error messages, reproduce if possible)
2. Locate the root cause
3. Fix the issue
4. Test the fix
5. Explain what was wrong and how it was fixed

Then execute the original request.
"""

    # Rule 3: Feature implementation requests
    if re.search(r'\b(add|implement|create|build)\b.*\b(feature|functionality)\b', prompt, re.I):
        return f"""FEATURE IMPLEMENTATION MODE

Original request: "{prompt}"

Please follow this development process:
1. Understand the requirements
2. Plan the implementation
3. Write the code
4. Add appropriate tests
5. Update documentation if needed

Then execute the original request.
"""

    # Rule 4: Documentation requests
    if re.search(r'\b(document|comment|explain|describe)\b', prompt, re.I):
        return f"""DOCUMENTATION MODE

Original request: "{prompt}"

Please provide comprehensive documentation:
- Clear explanations
- Examples where helpful
- Follow project documentation standards
- Include relevant context

Then execute the original request.
"""

    # Rule 5: Testing requests
    if re.search(r'\b(test|spec|unit test|integration test)\b', prompt, re.I):
        return f"""TESTING MODE

Original request: "{prompt}"

Please write comprehensive tests:
- Cover edge cases
- Follow testing best practices
- Include both positive and negative cases
- Use appropriate assertions

Then execute the original request.
"""

    # Default: Pass through unchanged
    return prompt


def main():
    # Load input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    prompt = input_data.get("prompt", "")

    # Route and transform the prompt
    transformed_prompt = route_prompt(prompt)

    print(transformed_prompt)
    sys.exit(0)


if __name__ == "__main__":
    main()
