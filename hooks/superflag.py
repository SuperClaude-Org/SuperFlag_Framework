#!/usr/bin/env python3
"""
SuperFlag - Claude Code Hook
Simple flag detection and message output for Claude Code
"""

import sys
import json
import yaml
import os
import copy
import re
import shutil
from pathlib import Path

# Constants
PROFILES_DIR = Path.home() / ".superflag"
PACKAGE_SUPERFLAG_DIR = Path(__file__).resolve().parent.parent / ".superflag"
PACKAGE_CONFIGS_DIR = PACKAGE_SUPERFLAG_DIR / "configs"
PROFILE_FILES = [
    "superflag.yaml",
    "claude.yaml",
    "codex.yaml",
    "continue.yaml",
    "gemini.yaml",
]
AUTO_FLAG = '--auto'
RESET_FLAG = '--reset'
DEFAULT_PROFILE = "claude"


def resolve_profiles():
    """Determine active profiles from environment (default to claude)."""
    env_value = (
        os.environ.get("SUPERFLAG_PROFILES")
        or os.environ.get("SUPERFLAG_PROFILE")
        or os.environ.get("SUPERFLAG_PLATFORM")
        or ""
    )

    profiles = [p.strip() for p in re.split(r'[;,\s]+', env_value) if p.strip()]
    if profiles:
        normalized = []
        seen = set()
        for profile in profiles:
            name = profile.replace('.yaml', '').replace('.yml', '').strip()
            if name and name not in seen:
                normalized.append(name)
                seen.add(name)
        if normalized:
            return normalized

    return [DEFAULT_PROFILE]


def ensure_bundled_files():
    """Ensure packaged profiles and configs exist in the user directory."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)

    for file_name in PROFILE_FILES:
        destination = PROFILES_DIR / file_name
        if not destination.exists():
            source = PACKAGE_SUPERFLAG_DIR / file_name
            if source.exists():
                shutil.copy2(source, destination)

    target_configs = PROFILES_DIR / "configs"
    target_configs.mkdir(parents=True, exist_ok=True)
    if PACKAGE_CONFIGS_DIR.exists():
        for entry in PACKAGE_CONFIGS_DIR.iterdir():
            destination = target_configs / entry.name
            if destination.exists():
                continue
            if entry.is_dir():
                shutil.copytree(entry, destination)
            else:
                shutil.copy2(entry, destination)


def resolve_profile_path(profile: str) -> Path:
    name = profile.strip()
    if not name:
        raise ValueError("Empty profile name")
    if not name.lower().endswith(('.yaml', '.yml')):
        name = f"{name}.yaml"
    return (PROFILES_DIR / name).resolve()


def is_yaml_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in ('.yaml', '.yml')


def collect_yaml_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    for entry in sorted(directory.iterdir()):
        if entry.is_dir():
            files.extend(collect_yaml_files(entry))
        elif is_yaml_file(entry):
            files.append(entry.resolve())
    files.sort()
    return files


def resolve_include_targets(reference: str, base_path: Path) -> list[Path]:
    ref = reference.strip()
    if not ref:
        raise ValueError(f"Empty include in {base_path}")

    candidate = Path(ref)
    if not candidate.is_absolute():
        candidate = (base_path.parent / candidate).resolve()

    if candidate.exists():
        if candidate.is_dir():
            return collect_yaml_files(candidate)
        if is_yaml_file(candidate):
            return [candidate]

    if candidate.suffix.lower() not in ('.yaml', '.yml'):
        for ext in ('.yaml', '.yml'):
            extended = Path(str(candidate) + ext)
            if extended.exists():
                if extended.is_dir():
                    return collect_yaml_files(extended)
                if is_yaml_file(extended):
                    return [extended]

    raise FileNotFoundError(f"Missing include file or directory: {reference} (resolved from {base_path})")


def merge_configs(base: dict, overlay: dict) -> dict:
    """Merge overlay configuration into base configuration."""
    result = copy.deepcopy(base)

    directives_overlay = overlay.get('directives') if isinstance(overlay, dict) else None
    if isinstance(directives_overlay, dict):
        directives = result.setdefault('directives', {})
        for flag, directive in directives_overlay.items():
            keys = expand_flag_keys(flag, directive)

            if directive is None:
                directives.pop(flag, None)
                for actual_key in keys:
                    directives.pop(actual_key, None)
                continue

            if isinstance(directive, dict):
                cleaned = clean_directive_config(directive)
                for actual_key in keys:
                    directives[actual_key] = copy.deepcopy(cleaned)
            else:
                for actual_key in keys:
                    directives[actual_key] = directive

    if isinstance(overlay, dict):
        for key, value in overlay.items():
            if key == 'directives':
                continue

            if value is None:
                result.pop(key, None)
            elif isinstance(value, dict):
                existing = result.get(key) if isinstance(result.get(key), dict) else {}
                result[key] = merge_configs(existing, value)
            else:
                result[key] = copy.deepcopy(value)

    return result


def load_profile_tree(profile_path: Path, visited: set[Path]) -> dict:
    """Recursively load a profile file and its includes."""
    resolved = profile_path.resolve()
    if resolved in visited:
        return {}
    visited.add(resolved)

    with resolved.open('r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    includes = data.pop('includes', []) or []
    combined = {}

    for include_ref in includes:
        if not isinstance(include_ref, str) or not include_ref.strip():
            continue
        targets = resolve_include_targets(include_ref, resolved)
        for include_path in targets:
            if not include_path.exists():
                raise FileNotFoundError(f"Missing include file: {include_path}")
            combined = merge_configs(combined, load_profile_tree(include_path, visited))

    combined = merge_configs(combined, data)
    return combined


def load_config():
    """Load YAML configuration using profile includes."""
    ensure_bundled_files()

    profiles = resolve_profiles()
    if not profiles:
        return None

    config: dict = {}
    visited: set[Path] = set()

    try:
        for profile in profiles:
            profile_path = resolve_profile_path(profile)
            if not profile_path.exists():
                raise FileNotFoundError(f"Missing profile file: {profile_path}")
            config = merge_configs(config, load_profile_tree(profile_path, visited))
    except (FileNotFoundError, yaml.YAMLError):
        return None

    normalize_directives(config)
    return config


def expand_flag_keys(raw_key, directive):
    """Split combined flag keys and include aliases/variations."""
    if not isinstance(raw_key, str):
        raw_key = str(raw_key)

    keys = set()
    for match in re.findall(r'--[^,|\s]+', raw_key):
        trimmed = match.strip()
        if trimmed:
            keys.add(trimmed)

    if not keys:
        for part in re.split(r'[,|]', raw_key):
            trimmed = part.strip()
            if trimmed:
                keys.add(trimmed)

    if isinstance(directive, dict):
        for alias_field in ('aliases', 'variations'):
            aliases = directive.get(alias_field)
            if not isinstance(aliases, (list, tuple)):
                continue

            for alias in aliases:
                if not isinstance(alias, str):
                    continue
                trimmed = alias.strip()
                if trimmed:
                    keys.add(trimmed)

    return list(keys)


def clean_directive_config(directive: dict) -> dict:
    """Remove alias metadata from a directive entry."""
    cleaned = {}
    for key, value in directive.items():
        if key in ('aliases', 'variations'):
            continue
        cleaned[key] = copy.deepcopy(value)
    return cleaned


def normalize_directives(config: dict) -> None:
    """Ensure directives map contains individual flag keys only."""
    directives = config.get('directives')
    if not isinstance(directives, dict):
        return

    normalized = {}
    for raw_key, directive in directives.items():
        keys = expand_flag_keys(raw_key, directive)

        if directive is None:
            for key in keys:
                normalized[key] = None
            continue

        if isinstance(directive, dict):
            cleaned = clean_directive_config(directive)
            for key in keys:
                normalized[key] = copy.deepcopy(cleaned)
        else:
            for key in keys:
                normalized[key] = directive

    config['directives'] = normalized


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
