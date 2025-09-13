#!/usr/bin/env python3
"""
Context Engine MCP - Claude Code Hook
Simple flag detection and message output for Claude Code
"""

import sys
import json
import yaml
from pathlib import Path

# Constants
FLAGS_YAML_PATH = Path.home() / ".context-engine" / "flags.yaml"
AUTO_FLAG = '--auto'
RESET_FLAG = '--reset'
EMPTY_JSON = '{}'
EXIT_SUCCESS = 0
EXIT_INTERRUPT = 130
EXIT_ERROR = 1


def load_config():
    """Load YAML configuration file

    Returns:
        dict: Configuration dictionary or None if loading fails
    """
    if not FLAGS_YAML_PATH.exists():
        return None

    try:
        with open(FLAGS_YAML_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, IOError) as e:
        print(f"Config load error: {e}", file=sys.stderr)
        return None


def extract_valid_flags(user_input, valid_flags):
    """Extract flags using simple 'in' check - 100% coverage"""
    # Use set to avoid duplicates, then convert back to list
    found_flags = [flag for flag in valid_flags if flag in user_input]
    # Preserve order from valid_flags but remove duplicates
    return list(dict.fromkeys(found_flags))


def get_auto_message(has_other_flags, other_flags, hook_messages):
    """Generate message for --auto flag"""
    if has_other_flags:
        # Auto with other flags
        config = hook_messages.get('auto_with_context', {})
        # Format as comma-separated list instead of JSON array
        other_flags_str = ', '.join(other_flags)
        return config.get('message', '').format(
            other_flags=other_flags_str
        )
    else:
        # Auto alone
        config = hook_messages.get('auto_authority', {})
        # No formatting needed for auto alone message
        return config.get('message', '')


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
        # Format as comma-separated list instead of JSON array
        return message_template.format(
            flag_list=', '.join(other_flags),
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
        # When --auto is detected, only show auto-related messages (skip other flags)
    else:
        # Process remaining flags only if --auto is not present
        other_flags = flags
        if other_flags:
            other_message = get_other_flags_message(other_flags, hook_messages)
            if other_message:
                messages.append(other_message)

    return messages


def process_input(user_input):
    """Main processing logic"""
    # Load configuration
    config = load_config()
    if not config:
        return None

    # Get valid flags from directives
    directives = config.get('directives', {})
    valid_flags = set(directives.keys())

    # Extract valid flags directly (100% coverage approach)
    flags = extract_valid_flags(user_input, valid_flags)
    if not flags:
        return None

    # Generate messages
    hook_messages = config.get('hook_messages', {})
    messages = generate_messages(flags, hook_messages)

    if messages:
        return {'messages': messages}
    return None


def parse_input(data):
    """Parse input data which may be JSON or plain text"""
    if not data:
        return ""

    # Try JSON parsing for Claude Code input format
    if data.startswith('{') and data.endswith('}'):
        try:
            parsed = json.loads(data)
            # Extract prompt/message/input field
            return parsed.get('prompt', parsed.get('message', parsed.get('input', data)))
        except json.JSONDecodeError:
            return data
    return data


def format_output(messages):
    """Format messages for output"""
    if not messages:
        return ""

    if isinstance(messages, list):
        return "\n".join([m for m in messages if m])
    return str(messages)


def main():
    """Main entry point for Claude Code Hook"""
    try:
        # Read and parse input
        data = sys.stdin.read().strip()
        user_input = parse_input(data)

        # Process input
        result = process_input(user_input) if user_input else None

        # Output result (JSON only for Claude)
        if result and result.get('messages'):
            pass  # Skip user-visible output
        print(EMPTY_JSON)

        return EXIT_SUCCESS

    except KeyboardInterrupt:
        print(EMPTY_JSON)
        return EXIT_INTERRUPT

    except Exception as e:
        # Log error to stderr
        print(f"Hook error: {str(e)}", file=sys.stderr)
        print(EMPTY_JSON)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
