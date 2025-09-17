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

try:
    import psutil
except ImportError:
    psutil = None
try:
    from .prompts import setup_claude_context_files, setup_continue_config, setup_gemini_context_files
except ImportError:
    # For direct script execution
    from prompts import setup_claude_context_files, setup_continue_config, setup_gemini_context_files

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

        # Add or update hooks section
        if 'hooks' not in settings:
            settings['hooks'] = {}

        # Register our hook in UserPromptSubmit array
        if 'UserPromptSubmit' not in settings['hooks']:
            settings['hooks']['UserPromptSubmit'] = []

        # Remove any existing context-engine hooks first
        settings['hooks']['UserPromptSubmit'] = [
            hook for hook in settings['hooks']['UserPromptSubmit']
            if not (isinstance(hook, dict) and
                   'hooks' in hook and
                   len(hook['hooks']) > 0 and
                   'superflag.py' in str(hook['hooks'][0].get('command', '')))
        ]

        # Add our hook
        settings['hooks']['UserPromptSubmit'].append({
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
    """Set up Continue extension MCP server configurations"""
    # Get current version dynamically
    try:
        from .__version__ import __version__
    except ImportError:
        __version__ = "unknown"

    home = get_home_dir()
    continue_dir = home / ".continue" / "mcpServers"

    # Create directory if it doesn't exist
    continue_dir.mkdir(parents=True, exist_ok=True)

    # Default to python -m superflag for consistency
    command = 'python'
    args = ['-m', 'superflag']
    detected_note = "# Default configuration"

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

# --- Option 2: pip without PATH ---
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
    # ANSI color codes
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Always show all platforms with consistent numbering
    platforms = {
        '1': ('claude-code', 'Claude Code'),
        '2': ('gemini-cli', 'Gemini CLI'),
        '3': ('cn', 'Continue'),
    }

    print(f"{CYAN}Select what to remove:{RESET}")

    # Show all platforms, marking which ones are installed
    for num, (code, name) in platforms.items():
        if code in installed_targets:
            print(f"  {BOLD}{num}{RESET}) {name} {GREEN}[installed]{RESET}")
        else:
            print(f"  {BOLD}{num}{RESET}) {name}")

    print(f"  {BOLD}a{RESET}) All detected platforms")
    print(f"\n{YELLOW}Enter your choice (e.g., '1', '2,3', 'a'):{RESET} ", end='')

    choice = input().strip().lower()

    # Handle special cases
    if choice == 'a' or choice == 'all':
        return installed_targets

    # Handle single or multiple selection
    selected = []
    for char in choice.replace(' ', '').split(','):
        if char in platforms:
            code = platforms[char][0]
            if code in installed_targets:
                selected.append(code)

    # Default to all if nothing selected
    if not selected:
        print(f"{YELLOW}No valid selection. Defaulting to all detected platforms.{RESET}")
        return installed_targets

    return selected


def select_platforms():
    """Interactive platform selection for installation"""
    # ANSI color codes
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    platforms = {
        '1': ('claude-code', 'Claude Code'),
        '2': ('gemini-cli', 'Gemini CLI'),
        '3': ('cn', 'Continue'),
    }

    print(f"{CYAN}Select installation targets:{RESET}")
    print(f"  {BOLD}1{RESET}) Claude Code")
    print(f"  {BOLD}2{RESET}) Gemini CLI")
    print(f"  {BOLD}3{RESET}) Continue")
    print(f"  {BOLD}a{RESET}) All platforms")
    print(f"\n{YELLOW}Enter your choice (e.g., '1', '2,3', 'a'):{RESET} ", end='')

    choice = input().strip().lower()

    # Handle special cases
    if choice == 'a' or choice == 'all':
        return [code for code, _ in platforms.values()]

    # Handle single or multiple selection
    selected = []
    for char in choice.replace(' ', '').split(','):
        if char in platforms:
            selected.append(platforms[char][0])

    # Default to Claude Code if nothing selected
    if not selected:
        print(f"{YELLOW}No selection made. Defaulting to Claude Code.{RESET}")
        return ['claude-code']

    return selected


def install_single_target(target):
    """Install SuperFlag for a single target platform"""
    from .__version__ import __version__

    # ANSI color codes
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    target_display = {
        "claude-code": "Claude Code",
        "cn": "Continue",
        "continue": "Continue",
        "gemini-cli": "Gemini CLI",
        "gemini": "Gemini CLI"
    }.get(target, target)

    print(f"\n{BOLD}Installing for {target_display}...{RESET}")

    # Get home directory for later use
    home = get_home_dir()

    # Track installation progress
    tasks = []

    # 1. Set up flags.yaml (only once for all targets)
    # This is handled in the main install() function

    # 2. Install based on target
    if target == "claude-code":
        # Check for Claude CLI
        if check_claude_cli():
            # Setup CLAUDE.md
            if setup_claude_context_files():
                tasks.append(("Context files", "OK", "~/.claude/"))
            else:
                tasks.append(("Context files", "SKIP", "Already configured"))

            # Setup Claude Code Hooks
            if setup_claude_code_hooks():
                tasks.append(("Hook system", "OK", "~/.claude/hooks/"))
            else:
                tasks.append(("Hook system", "SKIP", "MCP will still work"))

            # Manual MCP registration required
            tasks.append(("MCP server", "MANUAL", "Manual registration required"))
        else:
            tasks.append(("Claude CLI", "FAIL", "Not installed"))
            print(f"\n{YELLOW}Install Claude Code first: npm install -g @anthropic/claude-code{RESET}")

    elif target == "cn":
        # Install for Continue extension
        if setup_continue_mcp_servers():
            tasks.append(("MCP config", "OK", "~/.continue/mcpServers/"))
            # Setup config.yaml with rules
            continue_dir = home / ".continue"
            if setup_continue_config(continue_dir):
                tasks.append(("Global rules", "OK", "~/.continue/config.yaml"))
            else:
                tasks.append(("Global rules", "SKIP", "Manual config needed"))
        else:
            tasks.append(("MCP config", "FAIL", "Could not create files"))

    elif target == "gemini-cli":
        # Set up context files in ~/.gemini
        if setup_gemini_context_files():
            tasks.append(("Context files", "OK", "~/.gemini/"))
        else:
            tasks.append(("Context files", "FAIL", "Setup failed"))

        # Manual MCP registration required
        tasks.append(("MCP server", "MANUAL", "Manual configuration required"))

    # Return results for aggregation
    return tasks, target_display


def install(target=None):
    """Main installation function with interactive mode

    Args:
        target: Installation target(s). If None, prompts for selection.
                Can be a string or list of strings.
    """
    from .__version__ import __version__

    # ANSI color codes
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Print banner with center alignment
    width = 60
    print(f"\n{CYAN}{'=' * width}{RESET}")
    print(f"{CYAN}{f'SuperFlag v{__version__} - Installer'.center(width)}{RESET}")
    print(f"{CYAN}{'Contextual AI Enhancement Framework'.center(width)}{RESET}")
    print(f"{CYAN}{'<thecurrent.lim@gmail.com>'.center(width)}{RESET}")
    print(f"{CYAN}{'=' * width}{RESET}\n")

    # Determine targets
    if target is None:
        # Interactive mode
        targets = select_platforms()
    elif isinstance(target, str):
        # Single target from CLI
        targets = [target]
    elif isinstance(target, list):
        # Multiple targets
        targets = target
    else:
        print(f"{RED}Invalid target type{RESET}")
        return

    # Set up flags.yaml once for all targets
    flags_setup = False
    if setup_flags_yaml():
        flags_setup = True

    # Install for each selected target
    all_results = []
    for target in targets:
        tasks, display_name = install_single_target(target)
        all_results.append((display_name, tasks))

    # Display consolidated results
    print(f"\n{CYAN}Installation Results:{RESET}")

    # Show flags.yaml status (common for all)
    if flags_setup:
        print(f"  {GREEN}✓{RESET} {'flags.yaml':<15} ~/.superflag/flags.yaml")
    else:
        print(f"  {RED}✗{RESET} {'flags.yaml':<15} Setup failed")

    # Show results for each platform
    for platform_name, tasks in all_results:
        if tasks:
            print(f"\n  {BOLD}{platform_name}:{RESET}")
            for task_name, status, details in tasks:
                if status == "OK":
                    print(f"    {GREEN}✓{RESET} {task_name:<13} {details}")
                elif status == "SKIP":
                    print(f"    {YELLOW}⚠{RESET} {task_name:<13} {details}")
                elif status == "MANUAL":
                    print(f"    {YELLOW}⚡{RESET} {task_name:<13} {details}")
                else:
                    print(f"    {RED}✗{RESET} {task_name:<13} {details}")

    # Calculate success
    total_ok = sum(len([t for t in tasks if t[1] == "OK"]) for _, tasks in all_results)
    if flags_setup:
        total_ok += 1

    if total_ok > 0:
        print(f"\n{GREEN}Installation complete ({total_ok} components configured){RESET}")

        # Show next steps for each installed platform
        print(f"\n{BOLD}Next Steps:{RESET}")
        step_num = 1

        for platform_name, tasks in all_results:
            platform_key = None
            for target in targets:
                if platform_name == {"claude-code": "Claude Code", "cn": "Continue",
                                   "continue": "Continue", "gemini-cli": "Gemini CLI"}.get(target):
                    platform_key = target
                    break

            if platform_key == "claude-code":
                mcp_task = [t for t in tasks if t[0] == "MCP server"]
                if mcp_task and mcp_task[0][1] == "MANUAL":
                    print(f"{step_num}. {BOLD}[Claude Code]{RESET} Register MCP server:")
                    print(f"   {GREEN}claude mcp add superflag -s user \"python -m superflag\"{RESET}")
                    step_num += 1

            elif platform_key == "cn":
                print(f"{step_num}. {BOLD}[Continue]{RESET} MCP configured in ~/.continue/mcpServers/superflag.yaml")
                step_num += 1

            elif platform_key == "gemini-cli":
                mcp_task = [t for t in tasks if t[0] == "MCP server"]
                if mcp_task and mcp_task[0][1] == "MANUAL":
                    print(f"{step_num}. {BOLD}[Gemini CLI]{RESET} Check ~/.gemini/settings.json")
                    step_num += 1

        print(f"{step_num}. Restart your AI assistant(s)")
        print(f"{step_num + 1}. Test with a prompt like: \"Fix this bug --auto\" or \"--analyze --strict\"")

        print(f"\n{CYAN}Documentation: ~/.claude/SUPERFLAG.md{RESET}")
    else:
        print(f"\n{YELLOW}Installation completed with issues. Check error messages above.{RESET}")

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
            content = claude_md.read_text(encoding='utf-8')
            if "@SUPERFLAG.md" in content:
                new_content = content.replace("\n\n@SUPERFLAG.md", "").replace("\n@SUPERFLAG.md", "").replace("@SUPERFLAG.md", "")
                claude_md.write_text(new_content, encoding='utf-8')
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
                    original_count = len(settings['hooks']['UserPromptSubmit'])

                    # Filter out our hook
                    settings['hooks']['UserPromptSubmit'] = [
                        hook for hook in settings['hooks']['UserPromptSubmit']
                        if not (isinstance(hook, dict) and
                               'hooks' in hook and
                               len(hook['hooks']) > 0 and
                               'superflag.py' in str(hook['hooks'][0].get('command', '')))
                    ]

                    if len(settings['hooks']['UserPromptSubmit']) < original_count:
                        # Write updated settings
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

        # 5. MCP server registration must be removed manually
        results.append("[INFO] MCP server must be removed manually with: claude mcp remove superflag")

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
            content = gemini_md.read_text(encoding='utf-8')
            if "@SUPERFLAG.md" in content:
                new_content = (
                    content
                    .replace("\n\n@SUPERFLAG.md", "")
                    .replace("\n@SUPERFLAG.md", "")
                    .replace("@SUPERFLAG.md", "")
                )
                gemini_md.write_text(new_content, encoding='utf-8')
                results.append("[COMPLETE] Removed @SUPERFLAG.md reference from GEMINI.md")
            else:
                results.append("[INFO] @SUPERFLAG.md reference not found in GEMINI.md")

        context_engine_md = home / ".gemini" / "SUPERFLAG.md"
        success, message = delete_with_retry(context_engine_md)
        results.append(message)

        # MCP server registration must be removed manually
        results.append("[INFO] MCP server must be removed manually from ~/.gemini/settings.json")

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
    """Main uninstall function - removes SuperFlag with interactive mode

    Args:
        target: Uninstall target(s). If None, prompts for selection.
                Can be a string or list of strings.
    """
    from .__version__ import __version__

    # ANSI color codes
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Print banner with center alignment
    width = 60
    print(f"\n{CYAN}{'=' * width}{RESET}")
    print(f"{CYAN}{f'SuperFlag v{__version__} - Uninstaller'.center(width)}{RESET}")
    print(f"{CYAN}{'Removing all SuperFlag components'.center(width)}{RESET}")
    print(f"{CYAN}{'<thecurrent.lim@gmail.com>'.center(width)}{RESET}")
    print(f"{CYAN}{'=' * width}{RESET}\n")

    # Detect what's actually installed
    home = get_home_dir()
    installed_targets = []

    if (home / ".claude" / "SUPERFLAG.md").exists() or (home / ".claude" / "hooks" / "superflag.py").exists():
        installed_targets.append("claude-code")
    if (home / ".continue" / "mcpServers" / "superflag.yaml").exists():
        installed_targets.append("cn")
    if (home / ".gemini" / "SUPERFLAG.md").exists():
        installed_targets.append("gemini-cli")

    # Determine targets to remove
    if target is None:
        # Interactive mode - let user select from installed targets
        if not installed_targets:
            print(f"No SuperFlag installations detected.")
            print(f"\n{YELLOW}Note: Shared files (~/.superflag/) will still be cleaned{RESET}")
            targets = []  # Just clean shared files
        else:
            print(f"Detected: {', '.join(installed_targets)}")
            targets = select_uninstall_platforms(installed_targets)
    elif isinstance(target, str):
        targets = [target]
    elif isinstance(target, list):
        targets = target
    else:
        print(f"{RED}Invalid target type{RESET}")
        return

    print()

    # Track cleanup progress
    cleanup_tasks = []
    backup_path = None

    # Process each selected target
    if "claude-code" in targets:
        try:
            claude_results = uninstall_claude_code()
            success = any("[COMPLETE]" in r for r in claude_results)
            errors = [r for r in claude_results if "[ERROR]" in r or "[WARN]" in r]

            # Check for MCP info message
            mcp_message = None
            for r in claude_results:
                if "MCP server must be removed manually" in r:
                    mcp_message = "MCP: Remove manually with 'claude mcp remove superflag'"
                    break

            if success:
                if mcp_message:
                    cleanup_tasks.append(("Claude Code", "OK", "Hooks and context files removed"))
                    cleanup_tasks.append(("", "INFO", mcp_message))
                else:
                    cleanup_tasks.append(("Claude Code", "OK", "Hooks and context files removed"))
            elif errors:
                cleanup_tasks.append(("Claude Code", "WARN", f"{len(errors)} warnings"))
            else:
                cleanup_tasks.append(("Claude Code", "SKIP", "No changes needed"))

        except Exception as e:
            cleanup_tasks.append(("Claude Code", "FAIL", "Cleanup failed"))

    if "cn" in targets:
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

        except Exception as e:
            cleanup_tasks.append(("Continue", "FAIL", "Cleanup failed"))

    if "gemini-cli" in targets:
        try:
            gemini_results = uninstall_gemini()
            success = any("[COMPLETE]" in r for r in gemini_results)
            errors = [r for r in gemini_results if "[ERROR]" in r or "[WARN]" in r]

            # Check for MCP info message
            mcp_message = None
            for r in gemini_results:
                if "MCP server must be removed manually" in r:
                    mcp_message = "MCP: Edit ~/.gemini/settings.json manually"
                    break

            if success:
                if mcp_message:
                    cleanup_tasks.append(("Gemini CLI", "OK", "Context files removed"))
                    cleanup_tasks.append(("", "INFO", mcp_message))
                else:
                    cleanup_tasks.append(("Gemini CLI", "OK", "Context files removed"))
            elif errors:
                cleanup_tasks.append(("Gemini CLI", "WARN", f"{len(errors)} warnings"))
            else:
                cleanup_tasks.append(("Gemini CLI", "SKIP", "No changes needed"))

        except Exception as e:
            cleanup_tasks.append(("Gemini CLI", "FAIL", "Cleanup failed"))

    # Common files cleanup (always run)
    try:
        cleanup_results = cleanup_common_files()
        success = any("[COMPLETE]" in r for r in cleanup_results)
        errors = [r for r in cleanup_results if "[ERROR]" in r or "[WARN]" in r]

        # Extract backup info
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

    except Exception as e:
        cleanup_tasks.append(("Shared files", "FAIL", "Cleanup failed"))

    # Display results in structured format
    print(f"{CYAN}Cleanup Results:{RESET}")
    for task_name, status, details in cleanup_tasks:
        if status == "OK":
            print(f"  {GREEN}✓{RESET} {task_name:<15} {details}")
        elif status == "WARN":
            print(f"  {YELLOW}⚠{RESET} {task_name:<15} {details}")
        elif status == "SKIP":
            print(f"  {YELLOW}○{RESET} {task_name:<15} {details}")
        elif status == "INFO":
            print(f"    {YELLOW}→{RESET} {details}")
        else:
            print(f"  {RED}✗{RESET} {task_name:<15} {details}")

    # Final status
    success_count = len([t for t in cleanup_tasks if t[1] == "OK"])
    warn_count = len([t for t in cleanup_tasks if t[1] == "WARN"])

    print()
    if warn_count == 0:
        print(f"{GREEN}Uninstall complete ({success_count} components cleaned){RESET}")
    else:
        print(f"{YELLOW}Uninstall complete with {warn_count} warning(s){RESET}")
        print(f"Some files may require manual removal or system restart")

    # Package removal instructions
    print(f"\n{BOLD}To remove package:{RESET}")
    print(f"  pip uninstall superflag -y")
    print(f"  pipx uninstall superflag")

    print(f"\n{CYAN}{'=' * width}{RESET}")

    # Return 0 for successful uninstall
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