#!/usr/bin/env python3
"""
Installation helper script to set up SuperFlag
"""

import os
import shutil
from pathlib import Path
import json
import sys
import time
import subprocess
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import psutil
except ImportError:
    psutil = None
try:
    from .prompts import setup_claude_context_files, setup_continue_config, setup_gemini_context_files
    from .environment_detector import EnvironmentDetector
    from .mcp_manager import MCPManager
except ImportError:
    # For direct script execution
    from prompts import setup_claude_context_files, setup_continue_config, setup_gemini_context_files
    from environment_detector import EnvironmentDetector
    from mcp_manager import MCPManager


class Style:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


PLATFORM_CHOICES: Sequence[Tuple[str, str, str]] = (
    ("1", "claude-code", "Claude Code"),
    ("2", "gemini-cli", "Gemini CLI"),
    ("3", "cn", "Continue"),
)

DISPLAY_NAMES: Dict[str, str] = {code: label for _, code, label in PLATFORM_CHOICES}
MENU_INDEX: Dict[str, str] = {code: key for key, code, _ in PLATFORM_CHOICES}
TARGET_ALIASES: Dict[str, str] = {
    "continue": "cn",
    "gemini": "gemini-cli",
    "claude": "claude-code",
}

SUPERFLAG_HOOK_SENTINEL = "superflag.py"
CONTEXT_REFERENCE = "@SUPERFLAG.md"


def normalize_target(target: str) -> str:
    normalized = (target or "").lower()
    return TARGET_ALIASES.get(normalized, normalized)


def display_name_for(target: str) -> str:
    resolved = normalize_target(target)
    return DISPLAY_NAMES.get(resolved, target)


def _is_superflag_hook(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    hooks = entry.get("hooks")
    if not isinstance(hooks, list) or not hooks:
        return False
    command = str(hooks[0].get("command", ""))
    return SUPERFLAG_HOOK_SENTINEL in command


def scrub_superflag_hooks(entries: Iterable[Any]) -> Tuple[List[Any], bool]:
    cleaned: List[Any] = []
    removed = False
    for entry in entries or []:
        if _is_superflag_hook(entry):
            removed = True
            continue
        cleaned.append(entry)
    return cleaned, removed


def strip_reference_markers(content: str, reference: str = CONTEXT_REFERENCE) -> Tuple[str, bool]:
    updated = content
    for pattern in (f"\n\n{reference}", f"\n{reference}", reference):
        updated = updated.replace(pattern, "")
    return updated, updated != content


def remove_context_reference(path: Path, reference: str = CONTEXT_REFERENCE) -> bool:
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")
    updated, changed = strip_reference_markers(content, reference)
    if changed:
        path.write_text(updated, encoding="utf-8")
    return changed


def get_home_dir():
    """Get the user's home directory"""
    return Path.home()


def setup_flags_yaml():
    """Copy flags.yaml to user's home directory for editing"""
    home = get_home_dir()
    target_dir = home / ".superflag"
    target_dir.mkdir(parents=True, exist_ok=True)

    target_file = target_dir / "flags.yaml"

    # Always update to latest flags.yaml (backup if exists)
    if target_file.exists():
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = target_dir / f"flags.yaml.backup_{timestamp}"
        shutil.copy2(target_file, backup_file)
        # Silently backup and update

    # Prefer packaged resource (works from wheels)
    source_file = None
    try:
        from importlib.resources import files as pkg_files, as_file
        try:
            with as_file(pkg_files('superflag') / 'flags.yaml') as res_path:
                if res_path.exists():
                    source_file = res_path
        except Exception:
            pass
    except Exception:
        pass

    # Fallbacks for dev/editable installs
    if source_file is None:
        possible_paths = [
            Path(__file__).parent / 'flags.yaml',  # flags.yaml placed inside package
            Path(__file__).parent.parent.parent / "flags.yaml",  # Development root
            Path(sys.prefix) / "share" / "superflag" / "flags.yaml",  # Legacy installed path
        ]
        for path in possible_paths:
            if path.exists():
                source_file = path
                break

    if source_file:
        shutil.copy2(source_file, target_file)
        return True
    else:
        return False

def check_claude_cli():
    """Check if Claude CLI is installed without spawning it"""
    try:
        from shutil import which
        return which('claude') is not None
    except Exception as e:
        print(f"Debug: Claude CLI check failed: {e}")
        return False


def ensure_safe_installation():
    """Verify installation state without executing the MCP server.

    Best practice: avoid spawning long-running entrypoints or self-reinstalling.
    We check import availability and entrypoint presence on PATH.
    """
    try:
        from importlib.util import find_spec
        from shutil import which

        module_ok = find_spec('superflag') is not None
        exe_path = which('superflag')

        if module_ok and exe_path:
            return True

        # Return false for any issues (will be handled by caller)
        return False

    except Exception as e:
        return False

def stop_mcp_server(server_name):
    """Stop a running MCP server"""
    import subprocess
    try:
        # Try to stop the server
        result = subprocess.run(['claude', 'mcp', 'stop', server_name],
                              capture_output=True, text=True, shell=True, timeout=5)
        if result.returncode == 0:
            print(f"[OK] Stopped {server_name} server")
            return True
    except:
        pass
    return False

def install_mcp_servers_via_cli():
    """Install MCP servers using Claude CLI with auto-detection"""
    # Ensure Python package is installed (silently)
    ensure_safe_installation()

    # Detect installation method
    detector = EnvironmentDetector()
    detection = detector.detect()

    # Get the appropriate command
    if detection['method'] == 'not_installed':
        return False, "SuperFlag not installed"

    command = detection['command']

    # Register with MCP manager
    mcp_manager = MCPManager()
    success, message = mcp_manager.register_claude_mcp(command)

    return success, message

def setup_claude_code_hooks():
    """Setup Claude Code Hooks for automatic flag detection"""
    home = get_home_dir()
    claude_dir = home / ".claude"

    # Check if Claude Code is installed
    if not claude_dir.exists():
        print("[WARN] Claude Code directory not found (~/.claude missing)")
        return False

    try:
        # 1. Create hooks directory
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # 2. Copy hook file
        hook_file = hooks_dir / "superflag.py"

        # Read the hook content from our package
        try:
            # Try to import and use the hook from our package
            from . import claude_hook
            import inspect
            hook_content = inspect.getsource(claude_hook)
        except ImportError:
            # If import fails, use embedded content
            hook_content = get_hook_content()

        # Write hook file
        with open(hook_file, 'w', encoding='utf-8') as f:
            f.write(hook_content)

        # Hook file created successfully

        # 3. Update settings.json to register the hook
        settings_file = claude_dir / "settings.json"
        settings = {}

        # Load existing settings if they exist
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                try:
                    settings = json.load(f)
                except json.JSONDecodeError:
                    settings = {}

        hooks_section = settings.setdefault('hooks', {})
        submit_hooks = hooks_section.get('UserPromptSubmit', [])
        cleaned_hooks, _ = scrub_superflag_hooks(submit_hooks)
        hooks_section['UserPromptSubmit'] = cleaned_hooks

        hooks_section['UserPromptSubmit'].append({
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": f'python "{hook_file}"'
                }
            ]
        })

        # Save updated settings
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)

        # Hook registered in settings

        # 4. Verify hook installation
        verify_claude_hook(hook_file)  # Verify silently
        return True

    except Exception as e:
        print(f"[ERROR] Failed to setup Claude Code hooks: {e}")
        return False

def verify_claude_hook(hook_file: Path) -> bool:
    """Verify that the Claude Code hook is properly installed"""
    try:
        # Check hook file exists and is readable
        if not hook_file.exists():
            return False

        # Try to run the hook with test input
        result = subprocess.run(
            [sys.executable, str(hook_file)],
            input="test --auto --analyze",
            text=True,
            capture_output=True,
            timeout=5
        )

        # Check if it runs without error
        if result.returncode not in [0, 1, 130]:
            return False

        # Check if flags.yaml exists
        flags_path = Path.home() / ".superflag" / "flags.yaml"
        if not flags_path.exists():
            print("[INFO] flags.yaml will be created during setup")

        return True

    except Exception as e:
        print(f"[DEBUG] Hook verification error: {e}", file=sys.stderr)
        return False

def get_hook_content() -> str:
    """Get the hook content from the actual source file"""
    try:
        # Always use the actual claude_hook.py file
        from . import claude_hook
        hook_path = Path(claude_hook.__file__)
        with open(hook_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Could not read claude_hook.py: {e}")
        # Return minimal fallback that just passes through
        return '''#!/usr/bin/env python3
# Fallback hook - installation error
import sys
print("{}")
sys.exit(0)
'''

def install_gemini_cli_instructions():
    """Show instructions to register the MCP server with Gemini CLI.

    We don't modify Gemini CLI config files here. This prints clear, minimal
    steps so users can register the stdio MCP server command.
    """
    # Instructions will be shown in the final output
    pass

def setup_continue_mcp_servers():
    """Set up Continue extension MCP server configurations with auto-detection"""
    # Get current version dynamically
    try:
        from .__version__ import __version__
    except ImportError:
        __version__ = "unknown"

    home = get_home_dir()
    continue_dir = home / ".continue" / "mcpServers"

    # Create directory if it doesn't exist
    continue_dir.mkdir(parents=True, exist_ok=True)

    # Detect installation method
    detector = EnvironmentDetector()
    detection = detector.detect()
    command_spec = detector.get_command_spec(detection)
    method = detection.get('method', 'unknown')

    if command_spec:
        command = command_spec.executable
        args = list(command_spec.args)
    else:
        command = 'superflag'
        args = []

    if method == 'pipx' or (method == 'pip' and detection.get('in_path')):
        detected_note = f"# Auto-detected: {method} installation"
    elif method == 'uv':
        detected_note = "# Auto-detected: uv installation"
    elif method == 'pip' and not detection.get('in_path'):
        detected_note = "# Auto-detected: pip installation (not in PATH)"
    elif method == 'not_installed':
        detected_note = "# Default configuration (modify if needed)"
        command = 'superflag'
        args = []
    else:
        detected_note = "# Default configuration (modify if needed)"

    # Define server configuration with auto-detected values
    servers = [
        {
            "filename": "superflag.yaml",
            "content": f"""# SuperFlag - Contextual flag system for AI assistants
# SuperFlag installation utilities
#
{detected_note}

name: SuperFlag MCP
version: {__version__}
schema: v1
mcpServers:
- name: context-engine
  command: {command}
  args: {args}
  env: {{}}

# ===== Alternative configurations (if auto-detection was incorrect) =====

# --- Option 1: Standard Python installation (pipx or pip with PATH) ---
# mcpServers:
# - name: context-engine
#   command: superflag
#   args: []
#   env: {{}}

# --- Option 2: UV (Python package manager) ---
# mcpServers:
# - name: context-engine
#   command: uv
#   args: ["run", "superflag"]
#   env: {{}}

# --- Option 3: pip without PATH ---
# mcpServers:
# - name: context-engine
#   command: python
#   args: ["-m", "superflag"]
#   env: {{}}
"""
        }
    ]

    # Write each server configuration
    success = True
    for server in servers:
        config_path = continue_dir / server["filename"]

        # Skip if file already exists
        if config_path.exists():
            continue

        try:
            # Write the content directly (already in YAML format)
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(server["content"])
        except Exception as e:
            success = False

    # Return success status for caller to handle

    return success


def select_uninstall_platforms(installed_targets):
    """Interactive platform selection for uninstallation"""
    normalized: List[str] = []
    seen = set()
    for target in installed_targets or []:
        canonical = normalize_target(target)
        if canonical not in seen:
            normalized.append(canonical)
            seen.add(canonical)

    print(f"{Style.CYAN}Select what to remove:{Style.RESET}")

    options: List[Tuple[str, str]] = []
    for canonical in normalized:
        key = MENU_INDEX.get(canonical, str(len(options) + 1))
        label = display_name_for(canonical)
        print(f"  {Style.BOLD}{key}{Style.RESET}) {label}")
        options.append((key, canonical))

    print(f"  {Style.BOLD}a{Style.RESET}) All detected platforms")
    print(f"\n{Style.YELLOW}Enter your choice (e.g., '1', '2,3', 'a'):{Style.RESET} ", end='')

    choice = input().strip().lower()

    if choice in {'a', 'all'}:
        return normalized

    selected: List[str] = []
    tokens = [token for token in choice.replace(' ', '').split(',') if token]
    for token in tokens:
        for key, code in options:
            if token == key:
                selected.append(code)
                break

    if not selected:
        if normalized:
            print(f"{Style.YELLOW}No valid selection. Defaulting to all detected platforms.{Style.RESET}")
        return normalized

    return selected


def select_platforms():
    """Interactive platform selection for installation"""
    print(f"{Style.CYAN}Select installation targets:{Style.RESET}")
    for key, code, label in PLATFORM_CHOICES:
        print(f"  {Style.BOLD}{key}{Style.RESET}) {label}")
    print(f"  {Style.BOLD}a{Style.RESET}) All platforms")
    print(f"\n{Style.YELLOW}Enter your choice (e.g., '1', '2,3', 'a'):{Style.RESET} ", end='')

    choice = input().strip().lower()

    if choice in {'a', 'all'}:
        return [code for _, code, _ in PLATFORM_CHOICES]

    selected: List[str] = []
    tokens = [token for token in choice.replace(' ', '').split(',') if token]
    for token in tokens:
        for key, code, _ in PLATFORM_CHOICES:
            if token == key:
                selected.append(code)
                break

    if not selected:
        print(f"{Style.YELLOW}No selection made. Defaulting to Claude Code.{Style.RESET}")
        return ['claude-code']

    ordered: List[str] = []
    seen = set()
    for code in selected:
        if code not in seen:
            ordered.append(code)
            seen.add(code)
    return ordered



def install_single_target(target):
    """Install SuperFlag for a single target platform"""
    canonical = normalize_target(target)
    display = display_name_for(canonical)
    print(f"\n{Style.BOLD}Installing for {display}...{Style.RESET}")

    home = get_home_dir()
    tasks = []

    if canonical == 'claude-code':
        if check_claude_cli():
            mcp_success, mcp_message = install_mcp_servers_via_cli()

            if setup_claude_context_files():
                tasks.append(("Context files", "OK", "~/.claude/"))
            else:
                tasks.append(("Context files", "SKIP", "Already configured"))

            if setup_claude_code_hooks():
                tasks.append(("Hook system", "OK", "~/.claude/hooks/"))
            else:
                tasks.append(("Hook system", "SKIP", "MCP will still work"))

            if mcp_success:
                if "already" in mcp_message.lower():
                    tasks.append(("MCP server", "SKIP", "Already registered"))
                else:
                    tasks.append(("MCP server", "OK", "Auto-registered"))
            else:
                tasks.append(("MCP server", "MANUAL", "Manual registration needed"))
        else:
            tasks.append(("Claude CLI", "FAIL", "Not installed"))
            print(f"\n{Style.YELLOW}Install Claude Code first: npm install -g @anthropic/claude-code{Style.RESET}")

    elif canonical == 'cn':
        if setup_continue_mcp_servers():
            tasks.append(("MCP config", "OK", "~/.continue/mcpServers/"))
            continue_dir = home / ".continue"
            if setup_continue_config(continue_dir):
                tasks.append(("Global rules", "OK", "~/.continue/config.yaml"))
            else:
                tasks.append(("Global rules", "SKIP", "Manual config needed"))
        else:
            tasks.append(("MCP config", "FAIL", "Could not create files"))

    elif canonical == 'gemini-cli':
        if setup_gemini_context_files():
            tasks.append(("Context files", "OK", "~/.gemini/"))
        else:
            tasks.append(("Context files", "FAIL", "Setup failed"))

        detector = EnvironmentDetector()
        detection = detector.detect()
        if detection.get('method') != 'not_installed':
            spec = detector.get_command_spec(detection)
            mcp_manager = MCPManager()
            if spec:
                success, message = mcp_manager.register_gemini_mcp(spec.executable, list(spec.args))
            else:
                success, message = mcp_manager.register_gemini_mcp('superflag', [])

            if success:
                if "already" in message.lower():
                    tasks.append(("MCP server", "SKIP", "Already registered"))
                else:
                    tasks.append(("MCP server", "OK", "Auto-configured"))
            else:
                tasks.append(("MCP server", "MANUAL", "Manual config needed"))
        else:
            tasks.append(("MCP server", "FAIL", "SuperFlag not installed"))

    else:
        tasks.append(("Target", "FAIL", f"Unknown target '{target}'"))

    return tasks, display


def install(target=None):
    """Main installation function with interactive mode."""
    from .__version__ import __version__

    width = 60
    print()
    print(f"{Style.CYAN}{'=' * width}{Style.RESET}")
    print(f"{Style.CYAN}{f'SuperFlag v{__version__} - Installer'.center(width)}{Style.RESET}")
    print(f"{Style.CYAN}{'Contextual AI Enhancement Framework'.center(width)}{Style.RESET}")
    print(f"{Style.CYAN}{'<thecurrent.lim@gmail.com>'.center(width)}{Style.RESET}")
    print(f"{Style.CYAN}{'=' * width}{Style.RESET}")
    print()

    if target is None:
        if not installed_targets:
            print("No SuperFlag installations detected.")
            print()
            print(f"{Style.YELLOW}Note: Shared files (~/.superflag/) will still be cleaned{Style.RESET}")
            canonical_targets: List[str] = []
        else:
            detected_labels = ", ".join(display_name_for(t) for t in installed_targets)
            print(f"Detected: {detected_labels}")
            canonical_targets = select_uninstall_platforms(installed_targets)
    elif isinstance(target, str):
        selected_targets = [target]
    elif isinstance(target, list):
        selected_targets = target
    else:
        print(f"{Style.RED}Invalid target type{Style.RESET}")
        return

    canonical_targets: List[str] = []
    for entry in selected_targets:
        canonical = normalize_target(entry)
        if canonical and canonical not in canonical_targets:
            canonical_targets.append(canonical)

    flags_setup = bool(setup_flags_yaml())

    all_results: List[Tuple[str, str, List[Tuple[str, str, str]]]] = []
    for canonical in canonical_targets:
        tasks, display_name = install_single_target(canonical)
        all_results.append((canonical, display_name, tasks))

    print()
    print(f"{Style.CYAN}Installation Results:{Style.RESET}")

    if flags_setup:
        print(f"  {Style.GREEN}✓{Style.RESET} {'flags.yaml':<15} ~/.superflag/flags.yaml")
    else:
        print(f"  {Style.RED}✗{Style.RESET} {'flags.yaml':<15} Setup failed")

    for _, platform_name, tasks in all_results:
        if not tasks:
            continue
        print()
        print(f"  {Style.BOLD}{platform_name}:{Style.RESET}")
        for task_name, status, details in tasks:
            if status == 'OK':
                print(f"    {Style.GREEN}✓{Style.RESET} {task_name:<13} {details}")
            elif status == 'SKIP':
                print(f"    {Style.YELLOW}⚠{Style.RESET} {task_name:<13} {details}")
            elif status == 'MANUAL':
                print(f"    {Style.YELLOW}⚡{Style.RESET} {task_name:<13} {details}")
            else:
                print(f"    {Style.RED}✗{Style.RESET} {task_name:<13} {details}")

    total_ok = sum(len([t for t in tasks if t[1] == 'OK']) for _, _, tasks in all_results)
    if flags_setup:
        total_ok += 1

    if total_ok > 0:
        print()
        print(f"{Style.GREEN}Installation complete ({total_ok} components configured){Style.RESET}")
        print()
        print(f"{Style.BOLD}Next Steps:{Style.RESET}")
        step_num = 1

        for canonical, _, tasks in all_results:
            if canonical == 'claude-code':
                mcp_manager = MCPManager()
                if not mcp_manager.check_claude_mcp_registered():
                    mcp_task = [t for t in tasks if t[0] == 'MCP server']
                    if mcp_task and mcp_task[0][1] == 'MANUAL':
                        detector = EnvironmentDetector()
                        mcp_command = detector.get_mcp_install_command()
                        print(f"{step_num}. {Style.BOLD}[Claude Code]{Style.RESET} Register MCP server:")
                        if mcp_command:
                            print(f"   {Style.GREEN}{mcp_command}{Style.RESET}")
                        else:
                            print(f"   {Style.YELLOW}claude mcp add superflag -s user superflag{Style.RESET}")
                        step_num += 1

            elif canonical == 'cn':
                detector = EnvironmentDetector()
                detection = detector.detect()
                if detection.get('method') != 'not_installed':
                    print(f"{step_num}. {Style.BOLD}[Continue]{Style.RESET} MCP auto-configured in ~/.continue/mcpServers/")
                else:
                    print(f"{step_num}. {Style.BOLD}[Continue]{Style.RESET} Edit ~/.continue/mcpServers/superflag.yaml")
                step_num += 1

            elif canonical == 'gemini-cli':
                mcp_manager = MCPManager()
                if not mcp_manager.check_gemini_mcp_registered():
                    mcp_task = [t for t in tasks if t[0] == 'MCP server']
                    if mcp_task and mcp_task[0][1] == 'MANUAL':
                        print(f"{step_num}. {Style.BOLD}[Gemini CLI]{Style.RESET} Check ~/.gemini/settings.json")
                        step_num += 1

        print(f"{step_num}. Restart your AI assistant(s)")
        print(f"{step_num + 1}. Use MCP tools: get_directives(['--analyze', '--performance'])")
        print()
        print(f"{Style.CYAN}Documentation: ~/.claude/SUPERFLAG.md{Style.RESET}")
    else:
        print()
        print(f"{Style.YELLOW}Installation completed with issues. Check error messages above.{Style.RESET}")
def kill_context_engine_processes():
    """Kill running superflag server processes without killing shells or self

    Safety rules:
    - Skip current PID
    - Skip common shells (bash, zsh, sh, fish, powershell, cmd)
    - Only kill if the executable is python* with a cmdline referencing superflag
      or if the executable itself is superflag
    """
    killed = []

    # Skip process killing in CI environment to avoid self-termination
    if os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true':
        return ["[INFO] Skipping process termination in CI environment"]

    if psutil is None:
        return ["[INFO] psutil not available - manual process termination may be needed"]

    try:
        current_pid = os.getpid()
        shell_names = {
            'bash', 'zsh', 'sh', 'fish', 'pwsh', 'powershell', 'cmd', 'cmd.exe', 'dash'
        }

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                pid = proc.info.get('pid')
                if pid == current_pid:
                    continue

                cmdline = proc.info.get('cmdline') or []
                name = (proc.info.get('name') or '').lower()

                if name in shell_names:
                    # Never kill shells even if their command string mentions our name
                    continue

                exe = ''
                if cmdline:
                    exe = os.path.basename(cmdline[0]).lower()
                if not exe:
                    exe = name

                joined = ' '.join(cmdline).lower()

                # Skip the uninstall command itself
                if 'uninstall' in joined:
                    continue

                is_server_wrapper = (
                    'superflag' in exe or 'superflag' in name
                )
                is_python_running_server = (
                    exe.startswith('python') and (
                        'superflag' in joined
                    )
                )

                if not (is_server_wrapper or is_python_running_server):
                    continue

                proc.kill()
                killed.append(f"[COMPLETE] Killed process {proc.info.get('name', 'unknown')} (PID: {pid})")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed:
            time.sleep(1)

        return killed if killed else ["[INFO] No superflag processes found running"]

    except Exception as e:
        return [f"[WARN] Error killing processes: {str(e)}"]

def delete_with_retry(file_path, max_retries=3):
    """Delete file with retry logic for locked files"""
    for attempt in range(max_retries):
        try:
            if file_path.exists():
                file_path.unlink()
                return True, f"[COMPLETE] Removed {file_path}"
            else:
                return True, f"[INFO] File not found: {file_path}"
        except PermissionError as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            return False, f"[ERROR] Could not delete {file_path} (in use): {str(e)}"
        except Exception as e:
            return False, f"[ERROR] Error deleting {file_path}: {str(e)}"

    return False, f"[ERROR] Failed to delete {file_path} after {max_retries} attempts"

def uninstall_claude_code():
    """Remove Context Engine from Claude Code configuration"""
    results = []
    home = get_home_dir()

    # First kill any running processes
    results.extend(kill_context_engine_processes())

    try:
        # 1. Remove @SUPERFLAG.md reference from CLAUDE.md
        claude_md = home / ".claude" / "CLAUDE.md"
        if claude_md.exists():
            if remove_context_reference(claude_md):
                results.append("[COMPLETE] Removed @SUPERFLAG.md reference from CLAUDE.md")
            else:
                results.append("[INFO] @SUPERFLAG.md reference not found in CLAUDE.md")

        # 2. Remove hook from Claude Code settings.json
        settings_path = home / ".claude" / "settings.json"
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # Remove from UserPromptSubmit array
                if 'hooks' in settings and 'UserPromptSubmit' in settings['hooks']:
                    cleaned_hooks, removed = scrub_superflag_hooks(settings['hooks']['UserPromptSubmit'])

                    if removed:
                        settings['hooks']['UserPromptSubmit'] = cleaned_hooks
                        with open(settings_path, 'w', encoding='utf-8') as f:
                            json.dump(settings, f, indent=2)
                        results.append("[COMPLETE] Removed Context Engine hook from settings.json")
                    else:
                        results.append("[INFO] Context Engine hook not found in settings.json")
                else:
                    results.append("[INFO] No UserPromptSubmit hooks found in settings.json")
            except Exception as e:
                results.append(f"[WARNING] Error removing hook from settings: {str(e)}")

        # 3. Remove hook file
        hook_file = home / ".claude" / "hooks" / "superflag.py"
        if hook_file.exists():
            success, message = delete_with_retry(hook_file)
            results.append(message)
        else:
            results.append("[INFO] Hook file not found")

        # 4. Remove SUPERFLAG.md file with retry
        context_engine_md = home / ".claude" / "SUPERFLAG.md"
        success, message = delete_with_retry(context_engine_md)
        results.append(message)

        # 5. Remove MCP server registration
        mcp_manager = MCPManager()
        mcp_success, mcp_message = mcp_manager.unregister_claude_mcp()
        if mcp_success:
            results.append(f"[COMPLETE] {mcp_message}")
        else:
            results.append(f"[WARNING] {mcp_message}")

    except Exception as e:
        results.append(f"[ERROR] Error removing Claude Code config: {str(e)}")

    return results

def uninstall_continue():
    """Remove Context Engine rules from Continue configuration"""
    results = []
    home = get_home_dir()

    # 1. Try to remove Continue config rules
    continue_config_path = home / ".continue" / "config.yaml"
    if continue_config_path.exists():
        try:
            import yaml

            with open(continue_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}

            if 'rules' in config:
                original_count = len(config['rules'])
                # Filter out Context Engine rules - only check for Context Engine specific content
                config['rules'] = [
                    rule for rule in config['rules']
                    if not (isinstance(rule, str) and "Context Engine" in rule) and
                       not (isinstance(rule, dict) and rule.get('name') == "Context Engine Flags")
                ]

                if len(config['rules']) < original_count:
                    with open(continue_config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
                    results.append("[COMPLETE] Removed Context Engine rules from Continue config")
                else:
                    results.append("[INFO] Context Engine rules not found in Continue config")
            else:
                results.append("[INFO] No rules section in Continue config")

        except yaml.YAMLError as e:
            # If YAML parsing fails, try text-based removal
            try:
                with open(continue_config_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Find and remove SuperFlag MCP Protocol section
                new_lines = []
                skip_current_rule = False

                for i, line in enumerate(lines):
                    # Check if this line starts a rule item
                    if line.startswith('- '):
                        # Check if this rule contains Context Engine content
                        # It might be an escaped string on one line
                        if ("Context Engine" in line or
                            "get_directives" in line):
                            skip_current_rule = True
                            continue
                        else:
                            skip_current_rule = False
                            new_lines.append(line)
                    elif skip_current_rule:
                        # Skip continuation lines of the current rule
                        if line.startswith('  ') or line.strip() == '':
                            continue
                        else:
                            # This line doesn't belong to the rule
                            skip_current_rule = False
                            new_lines.append(line)
                    else:
                        # Keep all other lines
                        new_lines.append(line)

                # Write back the cleaned content
                with open(continue_config_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                results.append("[COMPLETE] Removed Context Engine rules from Continue config (text-based)")

            except Exception as text_error:
                results.append(f"[WARN] Could not clean Continue config.yaml: {str(e)}")

        except Exception as e:
            results.append(f"[WARN] Error processing Continue config: {str(e)}")
    else:
        results.append("[INFO] Continue config not found")

    # 2. Remove MCP server configuration with retry (always attempt this)
    try:
        context_engine_yaml = home / ".continue" / "mcpServers" / "superflag.yaml"
        success, message = delete_with_retry(context_engine_yaml)
        results.append(message)
    except Exception as e:
        results.append(f"[WARN] Error removing MCP server file: {str(e)}")

    return results

def uninstall_gemini():
    """Remove Context Engine references from Gemini configuration (~/.gemini)

    - Remove @SUPERFLAG.md reference from GEMINI.md (if present)
    - Remove SUPERFLAG.md file
    - Be forgiving if files/dirs don't exist
    """
    results = []
    home = get_home_dir()

    try:
        gemini_md = home / ".gemini" / "GEMINI.md"
        if gemini_md.exists():
            if remove_context_reference(gemini_md):
                results.append("[COMPLETE] Removed @SUPERFLAG.md reference from GEMINI.md")
            else:
                results.append("[INFO] @SUPERFLAG.md reference not found in GEMINI.md")

        context_engine_md = home / ".gemini" / "SUPERFLAG.md"
        success, message = delete_with_retry(context_engine_md)
        results.append(message)

        # Remove MCP server registration
        mcp_manager = MCPManager()
        mcp_success, mcp_message = mcp_manager.unregister_gemini_mcp()
        if mcp_success:
            results.append(f"[COMPLETE] {mcp_message}")
        else:
            results.append(f"[WARNING] {mcp_message}")

    except Exception as e:
        results.append(f"[ERROR] Error removing Gemini config: {str(e)}")

    return results

def cleanup_common_files():
    """Clean up common files and executables"""
    results = []

    try:
        # Kill any remaining processes first
        results.extend(kill_context_engine_processes())

        # Check for executable files in Scripts folder
        import sys
        scripts_dir = Path(sys.executable).parent / "Scripts"

        for exe_name in ["superflag.exe", "superflag.bat"]:
            exe_path = scripts_dir / exe_name
            success, message = delete_with_retry(exe_path)
            results.append(message)

        # Remove .superflag directory with backup
        home = get_home_dir()
        context_dir = home / ".superflag"
        if context_dir.exists():
            try:
                # Backup flags.yaml if it exists
                flags_file = context_dir / "flags.yaml"
                if flags_file.exists():
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_file = home / f"flags.yaml.backup_{timestamp}"
                    shutil.copy2(flags_file, backup_file)
                    results.append(f"[COMPLETE] Backed up flags.yaml to ~/{backup_file.name}")

                # Remove the entire .superflag directory
                shutil.rmtree(context_dir)
                results.append("[COMPLETE] Removed ~/.superflag directory (flags.yaml, etc.)")
            except Exception as e:
                results.append(f"[WARN] Could not remove .superflag directory: {str(e)}")
        else:
            results.append("[INFO] .superflag directory not found")

        results.append("[INFO] Run 'pip uninstall superflag -y' to remove Python package")

    except Exception as e:
        results.append(f"[ERROR] Error cleaning up files: {str(e)}")

    return results

def uninstall(target=None):
    """Main uninstall function - removes SuperFlag with interactive mode."""
    from .__version__ import __version__

    width = 60
    print()
    print(f"{Style.CYAN}{'=' * width}{Style.RESET}")
    print(f"{Style.CYAN}{f'SuperFlag v{__version__} - Uninstaller'.center(width)}{Style.RESET}")
    print(f"{Style.CYAN}{'Removing all SuperFlag components'.center(width)}{Style.RESET}")
    print(f"{Style.CYAN}{'<thecurrent.lim@gmail.com>'.center(width)}{Style.RESET}")
    print(f"{Style.CYAN}{'=' * width}{Style.RESET}")
    print()

    home = get_home_dir()
    installed_targets: List[str] = []

    if (home / '.claude' / 'SUPERFLAG.md').exists() or (home / '.claude' / 'hooks' / 'superflag.py').exists():
        installed_targets.append('claude-code')
    if (home / '.continue' / 'mcpServers' / 'superflag.yaml').exists():
        installed_targets.append('cn')
    if (home / '.gemini' / 'SUPERFLAG.md').exists():
        installed_targets.append('gemini-cli')

    if target is None:
        if not installed_targets:
            print("No SuperFlag installations detected.")
            print()
            print(f"{Style.YELLOW}Note: Shared files (~/.superflag/) will still be cleaned{Style.RESET}")
            canonical_targets: List[str] = []
        else:
            detected_labels = ", ".join(display_name_for(t) for t in installed_targets)
            print(f"Detected: {detected_labels}")
            canonical_targets = select_uninstall_platforms(installed_targets)
    elif isinstance(target, str):
        canonical_targets = [normalize_target(target)]
    elif isinstance(target, list):
        canonical_targets = [normalize_target(t) for t in target]
    else:
        print(f"{Style.RED}Invalid target type{Style.RESET}")
        return

    canonical_targets = [t for t in canonical_targets if t]

    print()

    cleanup_tasks: List[Tuple[str, str, str]] = []
    backup_path = None

    if 'claude-code' in canonical_targets:
        try:
            claude_results = uninstall_claude_code()
            success = any("[COMPLETE]" in r for r in claude_results)
            errors = [r for r in claude_results if "[ERROR]" in r or "[WARN]" in r]

            if success:
                cleanup_tasks.append(("Claude Code", "OK", "Hooks and context files removed"))
            elif errors:
                cleanup_tasks.append(("Claude Code", "WARN", f"{len(errors)} warnings"))
            else:
                cleanup_tasks.append(("Claude Code", "SKIP", "No changes needed"))
        except Exception:
            cleanup_tasks.append(("Claude Code", "FAIL", "Cleanup failed"))

    if 'cn' in canonical_targets:
        try:
            continue_results = uninstall_continue()
            success = any("[COMPLETE]" in r for r in continue_results)
            errors = [r for r in continue_results if "[ERROR]" in r or "[WARN]" in r]

            if success:
                cleanup_tasks.append(("Continue", "OK", "MCP config and rules removed"))
            elif errors:
                cleanup_tasks.append(("Continue", "WARN", f"{len(errors)} warnings"))
            else:
                cleanup_tasks.append(("Continue", "SKIP", "No changes needed"))
        except Exception:
            cleanup_tasks.append(("Continue", "FAIL", "Cleanup failed"))

    if 'gemini-cli' in canonical_targets:
        try:
            gemini_results = uninstall_gemini()
            success = any("[COMPLETE]" in r for r in gemini_results)
            errors = [r for r in gemini_results if "[ERROR]" in r or "[WARN]" in r]

            if success:
                cleanup_tasks.append(("Gemini CLI", "OK", "Context files removed"))
            elif errors:
                cleanup_tasks.append(("Gemini CLI", "WARN", f"{len(errors)} warnings"))
            else:
                cleanup_tasks.append(("Gemini CLI", "SKIP", "No changes needed"))
        except Exception:
            cleanup_tasks.append(("Gemini CLI", "FAIL", "Cleanup failed"))

    try:
        cleanup_results = cleanup_common_files()
        success = any("[COMPLETE]" in r for r in cleanup_results)
        errors = [r for r in cleanup_results if "[ERROR]" in r or "[WARN]" in r]

        for result in cleanup_results:
            if "backup_" in result:
                backup_path = result.split("backup_")[1].split()[0]
                break

        if success:
            if backup_path:
                cleanup_tasks.append(("Shared files", "OK", f"Backed up as flags.yaml.backup_{backup_path}"))
            else:
                cleanup_tasks.append(("Shared files", "OK", "~/.superflag/ removed"))
        elif errors:
            cleanup_tasks.append(("Shared files", "WARN", "Some files may remain"))
        else:
            cleanup_tasks.append(("Shared files", "SKIP", "No files found"))
    except Exception:
        cleanup_tasks.append(("Shared files", "FAIL", "Cleanup failed"))

    print(f"{Style.CYAN}Cleanup Results:{Style.RESET}")
    for task_name, status, details in cleanup_tasks:
        if status == 'OK':
            print(f"  {Style.GREEN}✓{Style.RESET} {task_name:<15} {details}")
        elif status == 'WARN':
            print(f"  {Style.YELLOW}⚠{Style.RESET} {task_name:<15} {details}")
        elif status == 'SKIP':
            print(f"  {Style.YELLOW}○{Style.RESET} {task_name:<15} {details}")
        else:
            print(f"  {Style.RED}✗{Style.RESET} {task_name:<15} {details}")

    success_count = len([t for t in cleanup_tasks if t[1] == 'OK'])
    warn_count = len([t for t in cleanup_tasks if t[1] == 'WARN'])

    print()
    if warn_count == 0:
        print(f"{Style.GREEN}Uninstall complete ({success_count} components cleaned){Style.RESET}")
    else:
        print(f"{Style.YELLOW}Uninstall complete with {warn_count} warning(s){Style.RESET}")
        print("Some files may require manual removal or system restart")

    print()
    print(f"{Style.BOLD}To remove package:{Style.RESET}")
    print("  pip uninstall superflag -y")
    print("  pipx uninstall superflag")
    print()
    print(f"{Style.CYAN}{'=' * width}{Style.RESET}")
    return 0
def main():
    """Main CLI entry point with subcommands"""
    import argparse

    try:
        from .__version__ import __version__
    except ImportError:
        __version__ = "unknown"

    parser = argparse.ArgumentParser(
        prog="context-engine",
        description="SuperFlag - Contextual flag system for AI assistants"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"superflag {__version__}"
    )

    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        required=True
    )

    # Install subcommand
    install_parser = subparsers.add_parser(
        'install',
        help='Install SuperFlag'
    )
    install_parser.add_argument(
        "--target",
        choices=["claude-code", "cn", "gemini-cli"],
        help="Installation target (if not specified, interactive mode)"
    )

    # Uninstall subcommand
    uninstall_parser = subparsers.add_parser(
        'uninstall',
        help='Uninstall SuperFlag'
    )
    uninstall_parser.add_argument(
        "--target",
        choices=["claude-code", "cn", "gemini-cli"],
        help="Uninstall target (if not specified, interactive mode)"
    )

    args = parser.parse_args()

    if args.command == 'install':
        # Use interactive mode if no target specified
        install(args.target if hasattr(args, 'target') and args.target else None)
    elif args.command == 'uninstall':
        return uninstall(args.target if hasattr(args, 'target') and args.target else None)

if __name__ == "__main__":
    sys.exit(main())