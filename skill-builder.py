#!/usr/bin/env python3
"""
Claude Code Skill Builder
A tool to help you create new Claude Code hooks easily from templates.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


class SkillBuilder:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.templates_dir = self.script_dir / "skill-builder" / "templates"
        self.metadata_file = self.templates_dir / "metadata.json"

    def load_metadata(self) -> Dict:
        """Load template metadata"""
        if not self.metadata_file.exists():
            return {}
        with open(self.metadata_file) as f:
            return json.load(f)

    def list_templates(self):
        """List all available hook templates"""
        metadata = self.load_metadata()

        if not metadata:
            print("No templates found.")
            return

        print("\nAvailable Hook Templates:\n")
        for name, info in metadata.items():
            print(f"  {name}")
            print(f"    Description: {info['description']}")
            print(f"    Use case: {info['use_case']}")
            print()

    def show_template_info(self, template_name: str):
        """Show detailed information about a template"""
        metadata = self.load_metadata()

        if template_name not in metadata:
            print(f"Error: Template '{template_name}' not found.")
            print(f"Available templates: {', '.join(metadata.keys())}")
            return 1

        info = metadata[template_name]
        print(f"\nTemplate: {template_name}\n")
        print(f"Description: {info['description']}")
        print(f"Use case: {info['use_case']}")
        print(f"\nFeatures:")
        for feature in info['features']:
            print(f"  - {feature}")

        if 'customization' in info:
            print(f"\nCustomization options:")
            for option in info['customization']:
                print(f"  - {option}")

        print(f"\nTemplate file: {template_name}.py")
        return 0

    def create_hook(self, template_name: str, output_path: Optional[str] = None, interactive: bool = True):
        """Create a new hook from a template"""
        metadata = self.load_metadata()

        if template_name not in metadata:
            print(f"Error: Template '{template_name}' not found.")
            print(f"Available templates: {', '.join(metadata.keys())}")
            return 1

        template_file = self.templates_dir / f"{template_name}.py"
        if not template_file.exists():
            print(f"Error: Template file not found: {template_file}")
            return 1

        # Read template
        with open(template_file) as f:
            template_content = f.read()

        # Get customization values
        if interactive:
            print(f"\nCreating hook from template: {template_name}")
            print(f"Description: {metadata[template_name]['description']}\n")

            # Get hook name
            hook_name = input("Enter hook name (e.g., my-validator): ").strip()
            if not hook_name:
                print("Error: Hook name is required.")
                return 1

            # Get hook description
            hook_description = input("Enter hook description: ").strip()

            # Template-specific customization
            customizations = {}
            if template_name == "wrapper":
                print("\nWrapper hook customization:")
                custom_instructions = input("Enter custom wrapping instructions (or press Enter for default): ").strip()
                if custom_instructions:
                    customizations['instructions'] = custom_instructions

            elif template_name == "validator":
                print("\nValidator hook customization:")
                validation_rules = input("Enter validation rules (comma-separated, e.g., 'no-profanity,min-length:10'): ").strip()
                if validation_rules:
                    customizations['rules'] = validation_rules

            elif template_name == "context-injector":
                print("\nContext injector customization:")
                context_source = input("Enter context source (file path or command): ").strip()
                if context_source:
                    customizations['source'] = context_source

            # Apply customizations to template
            output_content = self._apply_customizations(template_content, hook_name, hook_description, customizations)
        else:
            # Non-interactive mode: use defaults
            hook_name = f"{template_name}-hook"
            hook_description = metadata[template_name]['description']
            customizations = {}
            output_content = self._apply_customizations(template_content, hook_name, hook_description, customizations)

        # Determine output path
        if output_path is None:
            if interactive:
                default_path = f"hooks/{hook_name}.py"
                output_path = input(f"Enter output path (default: {default_path}): ").strip() or default_path
            else:
                print("Error: Output path is required in non-interactive mode.")
                return 1

        # Create output directory if needed
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write hook
        with open(output_file, 'w') as f:
            f.write(output_content)

        # Make executable
        os.chmod(output_file, 0o755)

        print(f"\n✓ Hook created successfully: {output_file}")
        print(f"\nNext steps:")
        print(f"1. Review and customize the hook: {output_file}")
        print(f"2. Add to ~/.claude/settings.json:")
        print(f'   {{\n     "hooks": {{\n       "UserPromptSubmit": [{{\n         "hooks": [{{\n           "type": "command",')
        print(f'           "command": "python3 {output_file.absolute()}"')
        print(f'         }}]\n       }}]\n     }}\n   }}')
        print(f"3. Test the hook with Claude Code")

        return 0

    def _apply_customizations(self, template: str, name: str, description: str, custom: Dict) -> str:
        """Apply customizations to template"""
        result = template

        # Replace placeholders
        result = result.replace("{{HOOK_NAME}}", name)
        result = result.replace("{{HOOK_DESCRIPTION}}", description)

        # Apply template-specific customizations
        for key, value in custom.items():
            result = result.replace(f"{{{{{key.upper()}}}}}", value)

        return result


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Skill Builder - Create hooks from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  skill-builder.py list
  skill-builder.py info wrapper
  skill-builder.py create simple
  skill-builder.py create wrapper -o hooks/my-wrapper.py
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    subparsers.add_parser('list', help='List available templates')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show template information')
    info_parser.add_argument('template', help='Template name')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new hook from template')
    create_parser.add_argument('template', help='Template name')
    create_parser.add_argument('-o', '--output', help='Output file path')
    create_parser.add_argument('--non-interactive', action='store_true', help='Non-interactive mode')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    builder = SkillBuilder()

    if args.command == 'list':
        builder.list_templates()
        return 0

    elif args.command == 'info':
        return builder.show_template_info(args.template)

    elif args.command == 'create':
        return builder.create_hook(
            args.template,
            args.output,
            interactive=not args.non_interactive
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
