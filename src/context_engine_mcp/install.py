#!/usr/bin/env python3
"""
Installation helper script to set up Context Engine MCP
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
    target_dir = home / ".context-engine"
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
            with as_file(pkg_files('context_engine_mcp') / 'flags.yaml') as res_path:
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
            Path(sys.prefix) / "share" / "context-engine-mcp" / "flags.yaml",  # Legacy installed path
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

        module_ok = find_spec('context_engine_mcp') is not None
        exe_path = which('context-engine-mcp')

        if module_ok and exe_path:
            print(f"[OK] context-engine-mcp is importable and on PATH: {exe_path}")
            return True

        if module_ok and not exe_path:
            print("[WARN] context-engine-mcp module is importable, but entrypoint not found on PATH.")
            print("  Ensure your Python Scripts directory is on PATH, then try again.")
            print("  Example (PowerShell): $env:Path += ';' + (Split-Path $(python -c 'import sys;print(sys.executable)')) + '\\Scripts'")
            return False

        # Module not importable - likely not installed in current interpreter
        print("[WARN] context-engine-mcp is not installed in this Python environment.")
        print("  Install or upgrade via: python -m pip install -U context-engine-mcp")
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
    print("   - Python: claude mcp add -s user -- context-engine context-engine-mcp")
    print("   - UV: claude mcp add -s user -- context-engine uv run context-engine-mcp")
    print("   - Custom: claude mcp add -s user -- context-engine <your-command>")

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
        hook_file = hooks_dir / "context-engine-hook.py"

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
                   'context-engine-hook.py' in str(hook['hooks'][0].get('command', '')))
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
        flags_path = Path.home() / ".context-engine" / "flags.yaml"
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
    print("   - Command: context-engine-mcp")
    print("   - Args: []")
    print("   - Transport: stdio (default for FastMCP)")
    print("\nIf Gemini CLI supports a config file for MCP servers, add an entry ")
    print("pointing to 'context-engine-mcp'. If it supports environment variables,")
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
            "filename": "context-engine.yaml",
            "content": f"""# Context Engine MCP - Contextual flag system for AI assistants
# Context Engine MCP installation utilities
#
# ===== IMPORTANT: Choose ONE configuration below =====
# Uncomment the configuration that matches your setup:

# --- Option 1: Standard Python installation ---
name: Context Engine MCP
version: {__version__}
schema: v1
mcpServers:
- name: context-engine
  command: context-engine-mcp
  args: []
  env: {{}}

# --- Option 2: UV (Python package manager) ---
# Requires: uv in PATH or use full path like ~/.cargo/bin/uv
# name: Context Engine MCP
# version: {__version__}
# schema: v1
# mcpServers:
# - name: context-engine
#   command: uv
#   args: ["run", "context-engine-mcp"]
#   env: {{}}

# --- Option 3: Development mode (pip install -e) ---
# name: Context Engine MCP
# version: {__version__}
# schema: v1
# mcpServers:
# - name: context-engine
#   command: python
#   args: ["-m", "context_engine_mcp"]
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
        print("1. Edit ~/.continue/mcpServers/context-engine.yaml")
        print("   - Choose and uncomment ONE configuration option")
        print("2. Restart VS Code")
        print("3. Type @ in Continue chat and select 'MCP'")
    
    return success

    

def install(target="claude-code"):
    """Main installation function
    
    Args:
        target: Installation target ('claude-code' or 'continue')
    """
    print(f"\n[SETUP] Setting up Context Engine MCP for {target}...")
    print("=" * 50)
    
    # Get home directory for later use
    home = get_home_dir()
    
    # 1. Set up flags.yaml
    print("\n[INSTALL] Installing flags.yaml...")
    if setup_flags_yaml():
        print("[OK] flags.yaml installed successfully")
    else:
        print("[WARN] Could not install flags.yaml")
    
    # 2. Install based on target
    if target == "claude-code":
        # Check for Claude CLI and install MCP servers
        print("\n[CHECK] Checking for Claude CLI...")
        if check_claude_cli():
            print("[OK] Claude CLI found")
            
            # Setup MCP server instruction
            install_mcp_servers_via_cli()
            
            # Setup CLAUDE.md
            print("\n[CONFIG] Setting up Claude context files...")
            if setup_claude_context_files():
                print("[OK] Claude context files configured")
            else:
                print("[WARN] Could not configure Claude context files")

            # Setup Claude Code Hooks
            print("\n[HOOKS] Setting up Claude Code hooks...")
            if setup_claude_code_hooks():
                print("[OK] Claude Code hooks installed successfully")
            else:
                print("[WARN] Could not setup Claude Code hooks (MCP will still work)")
        else:
            print("[WARN] Claude CLI not found")
            print("\nClaude Code CLI is required for MCP server installation.")
            print("Please install Claude Code first:")
            print("  npm install -g @anthropic/claude-code")
            print("\nAfter installing Claude Code, run 'context-engine-install' again.")
    
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
        print("\n[DOCS] Documentation: ~/.claude/CONTEXT-ENGINE.md")
    elif target == "cn":
        print("\n[NEXT] Next steps for Continue:")
        print("1. [EDIT] Edit context-engine configuration:")
        print("   ~/.continue/mcpServers/context-engine.yaml")
        print("   (Choose and uncomment ONE option)")
        print("\n2. [RESTART] Restart VS Code")
        print("\n3. [CHAT] In Continue chat:")
        print("   - Type @ and select 'MCP'")
        print("   - Available server: context-engine")
        print("\n[DOCS] Configuration file: ~/.continue/mcpServers/context-engine.yaml")

    elif target == "gemini-cli":
        print("\n[NEXT] Next steps for Gemini CLI:")
        print("1. Register 'context-engine-mcp' as an MCP stdio server in your Gemini CLI.")
        print("2. If Gemini CLI supports config files, add it there; otherwise use the CLI's add command if available.")
        print("3. Run Gemini CLI and verify the MCP tool is available (get_directives).")
    
    print("\n[COMPLETE] Context Engine MCP installation completed")
    print("-" * 50)

def kill_context_engine_processes():
    """Kill running context-engine-mcp server processes without killing shells or self

    Safety rules:
    - Skip current PID
    - Skip common shells (bash, zsh, sh, fish, powershell, cmd)
    - Only kill if the executable is python* with a cmdline referencing context_engine_mcp
      or if the executable itself is context-engine-mcp
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
                    'context-engine-mcp' in exe or 'context-engine-mcp' in name
                )
                is_python_running_server = (
                    exe.startswith('python') and (
                        'context-engine-mcp' in joined or 'context_engine_mcp' in joined
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

        return killed if killed else ["[INFO] No context-engine-mcp processes found running"]

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
        # 1. Remove @CONTEXT-ENGINE.md reference from CLAUDE.md
        claude_md = home / ".claude" / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text(encoding='utf-8')
            if "@CONTEXT-ENGINE.md" in content:
                new_content = content.replace("\n\n@CONTEXT-ENGINE.md", "").replace("\n@CONTEXT-ENGINE.md", "").replace("@CONTEXT-ENGINE.md", "")
                claude_md.write_text(new_content, encoding='utf-8')
                results.append("[COMPLETE] Removed @CONTEXT-ENGINE.md reference from CLAUDE.md")
            else:
                results.append("[INFO] @CONTEXT-ENGINE.md reference not found in CLAUDE.md")

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
                               'context-engine-hook.py' in str(hook['hooks'][0].get('command', '')))
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
        hook_file = home / ".claude" / "hooks" / "context-engine-hook.py"
        if hook_file.exists():
            success, message = delete_with_retry(hook_file)
            results.append(message)
        else:
            results.append("[INFO] Hook file not found")

        # 4. Remove CONTEXT-ENGINE.md file with retry
        context_engine_md = home / ".claude" / "CONTEXT-ENGINE.md"
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
                
                # Find and remove Context Engine MCP Protocol section
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
        context_engine_yaml = home / ".continue" / "mcpServers" / "context-engine.yaml"
        success, message = delete_with_retry(context_engine_yaml)
        results.append(message)
    except Exception as e:
        results.append(f"[WARN] Error removing MCP server file: {str(e)}")
    
    return results

def uninstall_gemini():
    """Remove Context Engine references from Gemini configuration (~/.gemini)

    - Remove @CONTEXT-ENGINE.md reference from GEMINI.md (if present)
    - Remove CONTEXT-ENGINE.md file
    - Be forgiving if files/dirs don't exist
    """
    results = []
    home = get_home_dir()

    try:
        gemini_md = home / ".gemini" / "GEMINI.md"
        if gemini_md.exists():
            content = gemini_md.read_text(encoding='utf-8')
            if "@CONTEXT-ENGINE.md" in content:
                new_content = (
                    content
                    .replace("\n\n@CONTEXT-ENGINE.md", "")
                    .replace("\n@CONTEXT-ENGINE.md", "")
                    .replace("@CONTEXT-ENGINE.md", "")
                )
                gemini_md.write_text(new_content, encoding='utf-8')
                results.append("[COMPLETE] Removed @CONTEXT-ENGINE.md reference from GEMINI.md")
            else:
                results.append("[INFO] @CONTEXT-ENGINE.md reference not found in GEMINI.md")

        context_engine_md = home / ".gemini" / "CONTEXT-ENGINE.md"
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
        
        for exe_name in ["context-engine-mcp.exe", "context-engine-mcp.bat"]:
            exe_path = scripts_dir / exe_name
            success, message = delete_with_retry(exe_path)
            results.append(message)
        
        # Remove .context-engine directory with backup
        home = get_home_dir()
        context_dir = home / ".context-engine"
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
                
                # Remove the entire .context-engine directory
                shutil.rmtree(context_dir)
                results.append("[COMPLETE] Removed ~/.context-engine directory (flags.yaml, etc.)")
            except Exception as e:
                results.append(f"[WARN] Could not remove .context-engine directory: {str(e)}")
        else:
            results.append("[INFO] .context-engine directory not found")
        
        results.append("[INFO] Run 'pip uninstall context-engine-mcp -y' to remove Python package")
        
    except Exception as e:
        results.append(f"[ERROR] Error cleaning up files: {str(e)}")
    
    return results

def uninstall():
    """Main uninstall function - removes Context Engine from all environments"""
    print("Uninstalling Context Engine MCP...")
    print("Force-killing processes and immediately removing files...")

    try:
        # 1. Claude Code cleanup
        print("\nCleaning up Claude Code configuration...")
        claude_results = uninstall_claude_code()
        for result in claude_results:
            print(f"  {result}")
    except Exception as e:
        print(f"  [ERROR] Failed to clean Claude Code: {str(e)}")
        claude_results = []
    
    # 2. Continue cleanup
    try:
        print("\nCleaning up Continue configuration...")
        continue_results = uninstall_continue()
        for result in continue_results:
            print(f"  {result}")
    except Exception as e:
        print(f"  [ERROR] Failed to clean Continue: {str(e)}")
        continue_results = []

    # 3. Gemini cleanup
    try:
        print("\nCleaning up Gemini configuration...")
        gemini_results = uninstall_gemini()
        for result in gemini_results:
            print(f"  {result}")
    except Exception as e:
        print(f"  [ERROR] Failed to clean Gemini: {str(e)}")
        gemini_results = []

    # 4. Common files cleanup
    try:
        print("\nCleaning up common files...")
        cleanup_results = cleanup_common_files()
        for result in cleanup_results:
            print(f"  {result}")
    except Exception as e:
        print(f"  [ERROR] Failed to clean common files: {str(e)}")
        cleanup_results = []
    
    # Check for any failures
    all_results = claude_results + continue_results + gemini_results + cleanup_results
    failures = [r for r in all_results if r.startswith("[ERROR]")]
    
    if failures:
        print(f"\nWARNING: {len(failures)} items could not be removed (files may be in use)")
        print("These will be cleaned up after restarting Claude Code/Continue")
    
    print("\nContext Engine MCP uninstall complete")
    
    print("Run 'pip uninstall context-engine-mcp -y' to remove Python package")
    print("Manually remove MCP server: claude mcp remove context-engine")
    print("No restart needed - files unlocked immediately")
    
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
        description="Context Engine MCP - Contextual flag system for AI assistants"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"context-engine-mcp {__version__}"
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        required=True
    )
    
    # Install subcommand
    install_parser = subparsers.add_parser(
        'install',
        help='Install Context Engine MCP'
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
        help='Uninstall Context Engine MCP from all environments'
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
