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
        print(f"[OK] Backed up existing flags.yaml to {backup_file.name}")
        print(f"[OK] Updating flags.yaml with latest version")

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
        print(f"[OK] Installed flags.yaml to {target_file}")
        print("  You can edit this file to customize flag directives")
        return True
    else:
        print(f"[WARN] flags.yaml source not found in any expected location")
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
            print(f"[OK] superflag is importable and on PATH: {exe_path}")
            return True

        if module_ok and not exe_path:
            print("[WARN] superflag module is importable, but entrypoint not found on PATH.")
            print("  Ensure your Python Scripts directory is on PATH, then try again.")
            print("  Example (PowerShell): $env:Path += ';' + (Split-Path $(python -c 'import sys;print(sys.executable)')) + '\\Scripts'")
            return False

        # Module not importable - likely not installed in current interpreter
        print("[WARN] superflag is not installed in this Python environment.")
        print("  Install or upgrade via: python -m pip install -U superflag")
        return False

    except Exception as e:
        print(f"[WARN] Installation check error: {e}")
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
    """Install MCP servers using Claude CLI"""
    # Ensure Python package is installed
    ensure_safe_installation()
    
    # Inform user about context-engine setup
    print("[INFO] For context-engine MCP server:")
    print("   Choose your installation method:")
    print("   - Python: claude mcp add -s user -- superflag")
    print("   - UV: claude mcp add -s user -- uv run superflag")
    print("   - Custom: claude mcp add -s user -- <your-command>")

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

        print(f"[OK] Created hook file: {hook_file}")

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

        print(f"[OK] Registered hook in: {settings_file}")

        # 4. Verify hook installation
        if verify_claude_hook(hook_file):
            print("[OK] Hook installation verified")
            return True
        else:
            print("[WARN] Hook verification failed, but installation completed")
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
    print("\n[INFO] For Gemini CLI (generic MCP stdio):")
    print("   Register the server command in your Gemini CLI MCP configuration:")
    print("   - Command: superflag")
    print("   - Args: []")
    print("   - Transport: stdio (default for FastMCP)")
    print("\nIf Gemini CLI supports a config file for MCP servers, add an entry ")
    print("pointing to 'superflag'. If it supports environment variables,")
    print("you can set any needed env for advanced scenarios.")

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

    print("[CREATE] Creating Continue MCP configuration files...")
    print("  Location: ~/.continue/mcpServers/")

    # Define server configurations with clear examples
    servers = [
        {
            "filename": "superflag.yaml",
            "content": f"""# SuperFlag - Contextual flag system for AI assistants
# SuperFlag installation utilities
#
# ===== IMPORTANT: Choose ONE configuration below =====
# Uncomment the configuration that matches your setup:

# --- Option 1: Standard Python installation ---
name: SuperFlag MCP
version: {__version__}
schema: v1
mcpServers:
- name: context-engine
  command: superflag
  args: []
  env: {{}}

# --- Option 2: UV (Python package manager) ---
# Requires: uv in PATH or use full path like ~/.cargo/bin/uv
# name: SuperFlag MCP
# version: {__version__}
# schema: v1
# mcpServers:
# - name: context-engine
#   command: uv
#   args: ["run", "superflag"]
#   env: {{}}

# --- Option 3: Development mode (pip install -e) ---
# name: SuperFlag MCP
# version: {__version__}
# schema: v1
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
            print(f"  [OK] {server['filename']} already exists, skipping...")
            continue
            
        try:
            # Write the content directly (already in YAML format)
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(server["content"])
            print(f"  [OK] Created: {config_path}")
        except Exception as e:
            print(f"  [WARN] Failed to create {server['filename']}: {e}")
            success = False
    
    if success:
        print("\n[CONFIG] Configuration files created successfully")
        print("\nNext steps:")
        print("1. Edit ~/.continue/mcpServers/superflag.yaml")
        print("   - Choose and uncomment ONE configuration option")
        print("2. Restart VS Code")
        print("3. Type @ in Continue chat and select 'MCP'")
    
    return success

    

def install(target="claude-code"):
    """Main installation function

    Args:
        target: Installation target ('claude-code' or 'continue')
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

    target_display = {
        "claude-code": "Claude Code",
        "cn": "Continue",
        "continue": "Continue",
        "gemini-cli": "Gemini CLI",
        "gemini": "Gemini CLI"
    }.get(target, target)

    print(f"Installing for {BOLD}{target_display}{RESET}:")

    # Show what will be created/modified
    if target == "claude-code":
        print(f"  {CYAN}Files to create/modify:{RESET}")
        print(f"    * Create: ~/.superflag/flags.yaml")
        print(f"    * Create: ~/.claude/SUPERFLAG.md")
        print(f"    * Create: ~/.claude/hooks/superflag.py")
        print(f"    * Modify: ~/.claude/CLAUDE.md (add @SUPERFLAG.md)")
        print(f"    * Modify: ~/.claude/settings.json (add hook)")
    elif target in ["cn", "continue"]:
        print(f"  {CYAN}Files to create/modify:{RESET}")
        print(f"    * Create: ~/.superflag/flags.yaml")
        print(f"    * Create: ~/.continue/mcpServers/superflag.yaml")
        print(f"    * Modify: ~/.continue/config.yaml (add rules)")
    elif target in ["gemini-cli", "gemini"]:
        print(f"  {CYAN}Files to create/modify:{RESET}")
        print(f"    * Create: ~/.superflag/flags.yaml")
        print(f"    * Create: ~/.gemini/SUPERFLAG.md")
        print(f"    * Modify: ~/.gemini/GEMINI.md (add @SUPERFLAG.md)")
    print()
    
    # Get home directory for later use
    home = get_home_dir()
    
    # 1. Set up flags.yaml
    # Simplified output
    success_count = 0
    error_count = 0

    # 1. Set up flags.yaml
    if setup_flags_yaml():
        print(f"  {GREEN}[OK]{RESET} flags.yaml configured (~/.superflag/flags.yaml)")
        success_count += 1
    else:
        print(f"  {RED}[X]{RESET} flags.yaml setup failed")
        error_count += 1
    
    # 2. Install based on target
    if target == "claude-code":
        # Check for Claude CLI and install MCP servers
        if check_claude_cli():
            # Setup MCP server instruction (silently)
            install_mcp_servers_via_cli()

            # Setup CLAUDE.md
            if setup_claude_context_files():
                print(f"  {GREEN}[OK]{RESET} Context files updated (~/.claude/)")
                success_count += 1
            else:
                print(f"  {YELLOW}[!]{RESET} Context files skipped")

            # Setup Claude Code Hooks
            if setup_claude_code_hooks():
                print(f"  {GREEN}[OK]{RESET} Hook registered (~/.claude/hooks/)")
                success_count += 1
            else:
                print(f"  {YELLOW}[!]{RESET} Hook setup skipped (MCP will still work)")

            print(f"  {GREEN}[OK]{RESET} MCP server ready")
            success_count += 1
        else:
            print(f"  {RED}[X]{RESET} Claude CLI not found")
            print(f"\n{YELLOW}Install Claude Code first: npm install -g @anthropic/claude-code{RESET}")
            error_count += 1
    
    elif target == "cn":
        # Install for Continue extension
        print("\n[SETUP] Setting up MCP servers for Continue extension...")
        if setup_continue_mcp_servers():
            # Setup config.yaml with rules
            print("\n[CONFIG] Setting up global rules...")
            continue_dir = home / ".continue"
            if setup_continue_config(continue_dir):
                print("[OK] Global rules configured")
            else:
                print("[WARN] Could not configure global rules")
        else:
            print("[WARN] Failed to create Continue MCP server configurations")
    
    elif target == "gemini-cli":
        # Provide generic instructions and set up context files in ~/.gemini
        install_gemini_cli_instructions()
        print("\n[CONFIG] Setting up Gemini context files...")
        if setup_gemini_context_files():
            print("[OK] Gemini context files configured")
        else:
            print("[WARN] Could not configure Gemini context files")

    else:
        print(f"[WARN] Unknown target: {target}")
        print("Supported targets: claude-code, cn (Continue), gemini-cli")
        return
    
    print("\n[COMPLETE] Installation complete")
    
    if target == "claude-code":
        print("\n[NEXT] Next steps for Claude Code:")
        print("1. Restart Claude Code if it's running")
        print("2. Use the MCP tools in your conversations:")
        print("   - Available flags are listed in system prompt")
        print("   - get_directives(['--analyze', '--performance']) - Activate modes")
        print("   - Use '--auto' to let AI select optimal flags")
        print("\n[DOCS] Documentation: ~/.claude/SUPERFLAG.md")
    elif target == "cn":
        print("\n[NEXT] Next steps for Continue:")
        print("1. [EDIT] Edit context-engine configuration:")
        print("   ~/.continue/mcpServers/superflag.yaml")
        print("   (Choose and uncomment ONE option)")
        print("\n2. [RESTART] Restart VS Code")
        print("\n3. [CHAT] In Continue chat:")
        print("   - Type @ and select 'MCP'")
        print("   - Available server: context-engine")
        print("\n[DOCS] Configuration file: ~/.continue/mcpServers/superflag.yaml")

    elif target == "gemini-cli":
        print("\n[NEXT] Next steps for Gemini CLI:")
        print("1. Register 'superflag' as an MCP stdio server in your Gemini CLI.")
        print("2. If Gemini CLI supports config files, add it there; otherwise use the CLI's add command if available.")
        print("3. Run Gemini CLI and verify the MCP tool is available (get_directives).")
    
    print("\n[COMPLETE] SuperFlag installation completed")
    print("-" * 50)

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

def uninstall():
    """Main uninstall function - removes Context Engine from all environments"""
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
        installed_targets.append("continue")
    if (home / ".gemini" / "SUPERFLAG.md").exists():
        installed_targets.append("gemini")

    print(f"Detected installations: {', '.join(installed_targets) if installed_targets else 'None'}")
    print()
    print(f"Removing components:")

    if "claude-code" in installed_targets:
        print(f"  {CYAN}Claude Code:{RESET}")
        print(f"    * Modify: CLAUDE.md (remove @SUPERFLAG.md)")
        print(f"    * Modify: settings.json (remove hook)")
        print(f"    * Delete: SUPERFLAG.md, hooks/superflag.py")

    if "continue" in installed_targets:
        print(f"  {CYAN}Continue:{RESET}")
        print(f"    * Modify: config.yaml (remove rules)")
        print(f"    * Delete: mcpServers/superflag.yaml")

    if "gemini" in installed_targets:
        print(f"  {CYAN}Gemini CLI:{RESET}")
        print(f"    * Modify: GEMINI.md (remove @SUPERFLAG.md)")
        print(f"    * Delete: SUPERFLAG.md")

    if (home / ".superflag" / "flags.yaml").exists():
        print(f"  {CYAN}Common:{RESET}")
        print(f"    * Backup & Delete: ~/.superflag/flags.yaml")
    print()

    success_items = []
    error_items = []
    backup_path = None

    # Only clean Claude Code if it's installed
    if "claude-code" in installed_targets:
        try:
            claude_results = uninstall_claude_code()
            for result in claude_results:
                if "[COMPLETE]" in result:
                    if "Claude Code configuration" not in result:
                        continue  # Skip individual file messages
                elif "[ERROR]" in result or "[WARN]" in result:
                    error_items.append(result)
                elif "backup" in result.lower():
                    # Extract backup filename
                    if "backup_" in result:
                        backup_path = result.split("backup_")[1].split()[0]
            if any("[COMPLETE]" in r for r in claude_results):
                print(f"  {GREEN}[OK]{RESET} Claude Code cleaned")
        except Exception as e:
            print(f"  {RED}[X]{RESET} Failed to clean Claude Code")
            error_items.append(str(e))
            claude_results = []
    else:
        claude_results = []
    
    # 2. Continue cleanup
    if "continue" in installed_targets:
        try:
            continue_results = uninstall_continue()
            for result in continue_results:
                if "[COMPLETE]" in result:
                    continue
                elif "[ERROR]" in result or "[WARN]" in result:
                    error_items.append(result)
            if any("[COMPLETE]" in r for r in continue_results) or any("[INFO]" in r for r in continue_results):
                print(f"  {GREEN}[OK]{RESET} Continue cleaned")
        except Exception as e:
            print(f"  {RED}[X]{RESET} Failed to clean Continue")
            error_items.append(str(e))
            continue_results = []
    else:
        continue_results = []

    # 3. Gemini cleanup
    if "gemini" in installed_targets:
        try:
            gemini_results = uninstall_gemini()
            for result in gemini_results:
                if "[COMPLETE]" in result:
                    continue
                elif "[ERROR]" in result or "[WARN]" in result:
                    error_items.append(result)
            if any("[COMPLETE]" in r for r in gemini_results) or any("[INFO]" in r for r in gemini_results):
                print(f"  {GREEN}[OK]{RESET} Gemini cleaned")
        except Exception as e:
            print(f"  {RED}[X]{RESET} Failed to clean Gemini")
            error_items.append(str(e))
            gemini_results = []
    else:
        gemini_results = []

    # 4. Common files cleanup
    try:
        cleanup_results = cleanup_common_files()
        for result in cleanup_results:
            if "[COMPLETE]" in result:
                if "backup" in result.lower():
                    if "backup_" in result:
                        backup_path = result.split("backup_")[1].split()[0]
                continue
            elif "[ERROR]" in result or "[WARN]" in result:
                error_items.append(result)
        if any("[COMPLETE]" in r for r in cleanup_results):
            if backup_path:
                print(f"  {GREEN}[OK]{RESET} Backup created: flags.yaml.backup_{backup_path}")
            else:
                print(f"  {GREEN}[OK]{RESET} Files cleaned")
    except Exception as e:
        print(f"  {RED}[X]{RESET} Failed to clean common files")
        error_items.append(str(e))
        cleanup_results = []
    
    # Final status
    print()
    if not error_items:
        print(f"{GREEN}Uninstall complete.{RESET}")
    else:
        # Count only real errors (not INFO messages)
        real_errors = [e for e in error_items if "[ERROR]" in e or "[WARN]" in e]
        if real_errors:
            print(f"{YELLOW}Uninstall complete with {len(real_errors)} warning(s).{RESET}")
            if any("in use" in e for e in real_errors):
                print(f"Files in use will be cleaned after restart.")
        else:
            print(f"{GREEN}Uninstall complete.{RESET}")

    # Package removal instructions
    print(f"\nTo remove package:")
    print(f"  pip uninstall superflag -y")
    print(f"  pipx uninstall superflag")

    print(f"{CYAN}{'=' * width}{RESET}")
    
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
        default="claude-code",
        help="Installation target - claude-code, cn (Continue), or gemini-cli (default: claude-code)"
    )
    
    # Uninstall subcommand
    uninstall_parser = subparsers.add_parser(
        'uninstall',
        help='Uninstall SuperFlag from all environments'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'install':
            install(args.target)
            return 0
        elif args.command == 'uninstall':
            result = uninstall()
            return result if isinstance(result, int) else 0
        else:
            # Should not reach here with required=True
            print(f"Unknown command: {args.command}")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
