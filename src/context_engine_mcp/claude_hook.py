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


def load_config():
    """Load YAML configuration file"""
    if not FLAGS_YAML_PATH.exists():
        return None

    try:
        with open(FLAGS_YAML_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
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
    else:
        other_flags = flags

    # Process remaining flags if any (but not when --auto is present)
    if other_flags and AUTO_FLAG not in detected_set:
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
    # messages = generate_messages(flags, hook_messages)
    messages = generate_messages(flags, hook_messages)

    if messages:
        return {
            # 'flags': flags,
            'messages': messages
        }
    return None


def main():
    """Main entry point for Claude Code Hook"""
    try:
        # Read input from stdin
        data = sys.stdin.read().strip()

        # Parse input - Claude Code may send JSON
        user_input = ""
        if data:
            # Try JSON parsing first (like hook_handler.py)
            if data.startswith('{') and data.endswith('}'):
                try:
                    parsed = json.loads(data)
                    # Extract prompt/message/input field
                    user_input = parsed.get('prompt', parsed.get('message', parsed.get('input', data)))
                except json.JSONDecodeError:
                    user_input = data
            else:
                user_input = data

        # Process input
        result = process_input(user_input) if user_input else None

        # Output result
        if result and result.get('messages'):
            # Plain text 출력용 메시지 준비 (JSON에는 포함 안 함)
            display_message = ""
            if isinstance(result.get('messages'), list):
                display_message = "\n".join([m for m in result['messages'] if m])
            else:
                display_message = str(result.get('messages', ''))

            # Plain text만 출력 (JSON 제거)
            if display_message:
                print(display_message)

            # JSON 출력 제거 - Claude가 plain text도 파싱할 수 있음
            # print(json.dumps(result, ensure_ascii=False))
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
