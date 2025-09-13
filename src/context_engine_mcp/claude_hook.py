#!/usr/bin/env python3
"""
Context Engine MCP - Claude Code Hook
Simple flag detection and message output for Claude Code
"""

import re
import sys
import json
import yaml
from pathlib import Path

# Constants
FLAGS_YAML_PATH = Path.home() / ".context-engine" / "flags.yaml"
FLAG_PATTERN = r'--[a-zA-Z][\w-]*'
AUTO_FLAG = '--auto'
RESET_FLAG = '--reset'


def extract_potential_flags(user_input):
    """Extract potential flags from user input using regex"""
    return re.findall(FLAG_PATTERN, user_input)


def load_config():
    """Load YAML configuration file"""
    if not FLAGS_YAML_PATH.exists():
        return None

    try:
        with open(FLAGS_YAML_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def filter_valid_flags(potential_flags, valid_flags):
    """Keep only flags that exist in YAML directives"""
    return [f for f in potential_flags if f in valid_flags]


def get_auto_message(has_other_flags, other_flags, hook_messages):
    """Generate message for --auto flag"""
    if has_other_flags:
        # Auto with other flags
        config = hook_messages.get('auto_with_context', {})
        return config.get('message', '').format(
            other_flags=json.dumps(other_flags)
        )
    else:
        # Auto alone
        config = hook_messages.get('auto_authority', {})
        return config.get('message', '').format(
            flag_list=json.dumps([AUTO_FLAG]),
            flags=AUTO_FLAG
        )


def get_other_flags_message(other_flags, hook_messages):
    """Generate message for non-auto flags"""
    other_flags_set = set(other_flags)

    # Check if it's ONLY --reset
    if other_flags_set == {RESET_FLAG}:
        config = hook_messages.get('reset_protocol', {})
    # Check if --reset is with other flags
    elif RESET_FLAG in other_flags_set:
        config = hook_messages.get('reset_with_others', {})
    else:
        # Standard execution for all other cases
        config = hook_messages.get('standard_execution', {})

    message_template = config.get('message', '')
    if message_template:
        return message_template.format(
            flag_list=json.dumps(other_flags),
            flags=', '.join(other_flags)
        )
    return None


def generate_messages(flags, hook_messages):
    """Generate appropriate messages based on detected flags"""
    if not flags:
        return []

    messages = []
    detected_set = set(flags)

    # Process --auto flag independently
    if AUTO_FLAG in detected_set:
        other_flags = [f for f in flags if f != AUTO_FLAG]
        auto_message = get_auto_message(bool(other_flags), other_flags, hook_messages)
        if auto_message:
            messages.append(auto_message)
    else:
        other_flags = flags

    # Process remaining flags if any
    if other_flags:
        other_message = get_other_flags_message(other_flags, hook_messages)
        if other_message:
            messages.append(other_message)

    return messages


def process_input(user_input):
    """Main processing logic"""
    # Extract potential flags
    potential_flags = extract_potential_flags(user_input)
    if not potential_flags:
        return None

    # Load configuration
    config = load_config()
    if not config:
        return None

    # Get valid flags from directives
    directives = config.get('directives', {})
    valid_flags = set(directives.keys())

    # Filter to keep only valid flags
    flags = filter_valid_flags(potential_flags, valid_flags)
    if not flags:
        return None

    # Generate messages
    hook_messages = config.get('hook_messages', {})
    messages = generate_messages(flags, hook_messages)

    if messages:
        return {
            'flags': flags,
            'messages': messages
        }
    return None


def main():
    """Main entry point for Claude Code Hook"""
    try:
        # Read input from stdin
        user_input = sys.stdin.read().strip()

        # Process input
        result = process_input(user_input) if user_input else None

        # Output result
        if result and result.get('messages'):
            # Print messages for user
            for message in result['messages']:
                print(message)
        else:
            # No valid flags or messages
            print("{}")

        return 0

    except KeyboardInterrupt:
        # User interrupted with Ctrl+C
        print("{}")
        return 130

    except Exception as e:
        # Log error to stderr (not visible in Claude Code output)
        print(f"Hook error: {str(e)}", file=sys.stderr)
        # Return safe empty JSON for Claude
        print("{}")
        return 1


if __name__ == "__main__":
    sys.exit(main())