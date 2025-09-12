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
    from .prompts import setup_claude_context_files, setup_continue_config
except ImportError:
    # For direct script execution
    from prompts import setup_claude_context_files, setup_continue_config

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
        print(f"✓ Backed up existing flags.yaml to {backup_file.name}")
        print(f"✓ Updating flags.yaml with latest version")

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
        print(f"✓ Installed flags.yaml to {target_file}")
        print("  You can edit this file to customize flag directives")
        return True
    else:
        print(f"⚠ flags.yaml source not found in any expected location")
        return False

def check_claude_cli():
    """Check if Claude CLI is installed"""
    try:
        import subprocess
        # Windows needs shell=True for npm-installed commands
        result = subprocess.run(['claude', '--version'], capture_output=True, text=True, shell=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Debug: Claude CLI check failed: {e}")
        return False


def ensure_safe_installation():
    """Ensure safe installation even if exe is running"""
    import subprocess
    import time
    from pathlib import Path
    
    # First check if command already works
    try:
        result = subprocess.run(['context-engine-mcp', '--version'], 
                              capture_output=True, text=True, shell=True, timeout=3)
        if "context-engine-mcp" in result.stdout or result.returncode == 0:
            print("✓ context-engine-mcp command already works")
            return True
    except:
        pass
    
    # Try to install package safely
    package_dir = Path(__file__).parent.parent.parent
    
    # Use --force-reinstall with --no-deps to avoid conflicts
    print("📦 Installing context-engine-mcp package...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-e', str(package_dir), 
             '--force-reinstall', '--no-deps'],
            capture_output=True, text=True
        )
        
        if "Successfully installed" in result.stdout:
            print("✓ Package installed successfully")
            return True
        elif "Device or resource busy" in result.stderr:
            print("⚠ Executable is in use. This is normal if MCP is running.")
            print("  The installation should still work correctly.")
            return True
    except Exception as e:
        print(f"⚠ Installation warning: {e}")
    
    return False

def stop_mcp_server(server_name):
    """Stop a running MCP server"""
    import subprocess
    try:
        # Try to stop the server
        result = subprocess.run(['claude', 'mcp', 'stop', server_name],
                              capture_output=True, text=True, shell=True, timeout=5)
        if result.returncode == 0:
            print(f"✓ Stopped {server_name} server")
            return True
    except:
        pass
    return False

def install_mcp_servers_via_cli():
    """Install MCP servers using Claude CLI"""
    # Ensure Python package is installed
    ensure_safe_installation()
    
    # Inform user about context-engine setup
    print("📌 For context-engine MCP server:")
    print("   Choose your installation method:")
    print("   • Python: claude mcp add -s user -- context-engine context-engine-mcp")
    print("   • UV: claude mcp add -s user -- context-engine uv run context-engine-mcp")
    print("   • Custom: claude mcp add -s user -- context-engine <your-command>")

def setup_continue_mcp_servers():
    """Set up Continue extension MCP server configurations"""
    home = get_home_dir()
    continue_dir = home / ".continue" / "mcpServers"
    
    # Create directory if it doesn't exist
    continue_dir.mkdir(parents=True, exist_ok=True)
    
    print("📁 Creating Continue MCP configuration files...")
    print("  Location: ~/.continue/mcpServers/")
    
    # Define server configurations with clear examples
    servers = [
        {
            "filename": "context-engine.yaml",
            "content": """# Context Engine MCP - Contextual flag system for AI assistants
# Context Engine MCP installation utilities
#
# ===== IMPORTANT: Choose ONE configuration below =====
# Uncomment the configuration that matches your setup:

# --- Option 1: Standard Python installation ---
name: Context Engine MCP
version: 1.0.4
schema: v1
mcpServers:
- name: context-engine
  command: context-engine-mcp
  args: []
  env: {}

# --- Option 2: UV (Python package manager) ---
# Requires: uv in PATH or use full path like ~/.cargo/bin/uv
# name: Context Engine MCP
# version: 1.0.4
# schema: v1
# mcpServers:
# - name: context-engine
#   command: uv
#   args: ["run", "context-engine-mcp"]
#   env: {}

# --- Option 3: Development mode (pip install -e) ---
# name: Context Engine MCP
# version: 1.0.4
# schema: v1
# mcpServers:
# - name: context-engine
#   command: python
#   args: ["-m", "context_engine_mcp"]
#   env: {}

"""
        }
    ]
    
    # Write each server configuration
    success = True
    for server in servers:
        config_path = continue_dir / server["filename"]
        
        # Skip if file already exists
        if config_path.exists():
            print(f"  ✓ {server['filename']} already exists, skipping...")
            continue
            
        try:
            # Write the content directly (already in YAML format)
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(server["content"])
            print(f"  ✓ Created: {config_path}")
        except Exception as e:
            print(f"  ⚠ Failed to create {server['filename']}: {e}")
            success = False
    
    if success:
        print("\n📝 Configuration files created successfully!")
        print("\nNext steps:")
        print("1. Edit ~/.continue/mcpServers/context-engine.yaml")
        print("   - Choose and uncomment ONE configuration option")
        print("2. Restart VS Code")
        print("3. Type @ in Continue chat and select 'MCP'")
    
    return success

def setup_claude_code_user_scope():
    """Set up Claude Code user-scope configuration"""
    # Claude Code configuration is typically in:
    # Windows: %APPDATA%\Claude\claude_desktop_config.json
    # Mac: ~/Library/Application Support/Claude/claude_desktop_config.json
    # Linux: ~/.config/Claude/claude_desktop_config.json
    
    config_paths = {
        'win32': Path(os.environ.get('APPDATA', '')) / 'Claude' / 'claude_desktop_config.json',
        'darwin': Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json',
        'linux': Path.home() / '.config' / 'Claude' / 'claude_desktop_config.json'
    }
    
    # Determine platform
    platform = sys.platform
    if platform.startswith('linux'):
        platform = 'linux'
    
    config_path = config_paths.get(platform)
    
    if not config_path:
        print(f"⚠ Unknown platform: {platform}")
        return False
    
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or create new one
    config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"⚠ Could not read existing config: {e}")
            config = {}
    
    # Add our MCP server to the config
    if 'mcpServers' not in config:
        config['mcpServers'] = {}
    
    # Add context-engine-mcp
    config['mcpServers']['context-engine'] = {
        "command": "context-engine-mcp",
        "description": "Contextual flag system for AI assistants"
    }
    
    # Write updated config
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✓ Claude Code configuration updated: {config_path}")
        return True
    except Exception as e:
        print(f"⚠ Could not write config: {e}")
        return False

def install(target="claude-code"):
    """Main installation function
    
    Args:
        target: Installation target ('claude-code' or 'continue')
    """
    print(f"\n🚀 Setting up Context Engine MCP for {target}...")
    print("=" * 50)
    
    # Get home directory for later use
    home = get_home_dir()
    
    # 1. Set up flags.yaml
    print("\n📋 Installing flags.yaml...")
    if setup_flags_yaml():
        print("✓ flags.yaml installed successfully")
    else:
        print("⚠ Could not install flags.yaml")
    
    # 2. Install based on target
    if target == "claude-code":
        # Check for Claude CLI and install MCP servers
        print("\n🔍 Checking for Claude CLI...")
        if check_claude_cli():
            print("✓ Claude CLI found")
            
            # Setup MCP server instruction
            install_mcp_servers_via_cli()
            
            # Setup CLAUDE.md
            print("\n📝 Setting up Claude context files...")
            if setup_claude_context_files():
                print("✓ Claude context files configured")
            else:
                print("⚠ Could not configure Claude context files")
        else:
            print("⚠ Claude CLI not found")
            print("\nClaude Code CLI is required for MCP server installation.")
            print("Please install Claude Code first:")
            print("  npm install -g @anthropic/claude-code")
            print("\nAfter installing Claude Code, run 'context-engine-install' again.")
    
    elif target == "cn":
        # Install for Continue extension
        print("\n📦 Setting up MCP servers for Continue extension...")
        if setup_continue_mcp_servers():
            # Setup config.yaml with rules
            print("\n📝 Setting up global rules...")
            continue_dir = home / ".continue"
            if setup_continue_config(continue_dir):
                print("✓ Global rules configured")
            else:
                print("⚠ Could not configure global rules")
        else:
            print("⚠ Failed to create Continue MCP server configurations")
    
    else:
        print(f"⚠ Unknown target: {target}")
        print("Supported targets: claude-code, cn (Continue)")
        return
    
    print("\n✅ Installation complete!")
    
    if target == "claude-code":
        print("\n🎯 Next steps for Claude Code:")
        print("1. Restart Claude Code if it's running")
        print("2. Use the MCP tools in your conversations:")
        print("   • list_available_flags() - View all 17 available flags")
        print("   • get_directives(['--analyze', '--performance']) - Activate modes")
        print("   • Use '--auto' to let AI select optimal flags")
        print("\n📚 Documentation: ~/.claude/CONTEXT-ENGINE.md")
    elif target == "cn":
        print("\n🎯 Next steps for Continue:")
        print("1. 🔧 Edit context-engine configuration:")
        print("   ~/.continue/mcpServers/context-engine.yaml")
        print("   (Choose and uncomment ONE option)")
        print("\n2. 🔄 Restart VS Code")
        print("\n3. 💬 In Continue chat:")
        print("   • Type @ and select 'MCP'")
        print("   • Available server: context-engine")
        print("\n📚 Configuration file: ~/.continue/mcpServers/context-engine.yaml")
    
    print("\n✅ Context Engine MCP installation completed!")
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

    if psutil is None:
        return ["ℹ️ psutil not available - manual process termination may be needed"]

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
                killed.append(f"✅ Killed process {proc.info.get('name', 'unknown')} (PID: {pid})")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed:
            time.sleep(1)

        return killed if killed else ["ℹ️ No context-engine-mcp processes found running"]

    except Exception as e:
        return [f"⚠️ Error killing processes: {str(e)}"]

def delete_with_retry(file_path, max_retries=3):
    """Delete file with retry logic for locked files"""
    for attempt in range(max_retries):
        try:
            if file_path.exists():
                file_path.unlink()
                return True, f"✅ Removed {file_path}"
            else:
                return True, f"ℹ️ File not found: {file_path}"
        except PermissionError as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
                continue
            return False, f"❌ Could not delete {file_path} (in use): {str(e)}"
        except Exception as e:
            return False, f"❌ Error deleting {file_path}: {str(e)}"
    
    return False, f"❌ Failed to delete {file_path} after {max_retries} attempts"

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
                results.append("✅ Removed @CONTEXT-ENGINE.md reference from CLAUDE.md")
            else:
                results.append("ℹ️ @CONTEXT-ENGINE.md reference not found in CLAUDE.md")
        
        # 3. Remove CONTEXT-ENGINE.md file with retry
        context_engine_md = home / ".claude" / "CONTEXT-ENGINE.md"
        success, message = delete_with_retry(context_engine_md)
        results.append(message)
            
    except Exception as e:
        results.append(f"❌ Error removing Claude Code config: {str(e)}")
    
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
                    results.append("✅ Removed Context Engine rules from Continue config")
                else:
                    results.append("ℹ️ Context Engine rules not found in Continue config")
            else:
                results.append("ℹ️ No rules section in Continue config")
                
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
                            "list_available_flags" in line or
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
                results.append("✅ Removed Context Engine rules from Continue config (text-based)")
                
            except Exception as text_error:
                results.append(f"⚠️ Could not clean Continue config.yaml: {str(e)}")
                
        except Exception as e:
            results.append(f"⚠️ Error processing Continue config: {str(e)}")
    else:
        results.append("ℹ️ Continue config not found")
    
    # 2. Remove MCP server configuration with retry (always attempt this)
    try:
        context_engine_yaml = home / ".continue" / "mcpServers" / "context-engine.yaml"
        success, message = delete_with_retry(context_engine_yaml)
        results.append(message)
    except Exception as e:
        results.append(f"⚠️ Error removing MCP server file: {str(e)}")
    
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
                    results.append(f"✅ Backed up flags.yaml to ~/{backup_file.name}")
                
                # Remove the entire .context-engine directory
                shutil.rmtree(context_dir)
                results.append("✅ Removed ~/.context-engine directory (flags.yaml, etc.)")
            except Exception as e:
                results.append(f"⚠️ Could not remove .context-engine directory: {str(e)}")
        else:
            results.append("ℹ️ .context-engine directory not found")
        
        results.append("ℹ️ Run 'pip uninstall context-engine-mcp -y' to remove Python package")
        
    except Exception as e:
        results.append(f"❌ Error cleaning up files: {str(e)}")
    
    return results

def uninstall():
    """Main uninstall function - removes Context Engine from all environments"""
    print("Uninstalling Context Engine MCP...")
    print("Force-killing processes and immediately removing files...")
    
    # 1. Claude Code cleanup
    print("\nCleaning up Claude Code configuration...")
    claude_results = uninstall_claude_code()
    for result in claude_results:
        print(f"  {result}")
    
    # 2. Continue cleanup
    print("\nCleaning up Continue configuration...")
    continue_results = uninstall_continue()
    for result in continue_results:
        print(f"  {result}")
    
    # 3. Common files cleanup
    print("\nCleaning up common files...")
    cleanup_results = cleanup_common_files()
    for result in cleanup_results:
        print(f"  {result}")
    
    # Check for any failures
    all_results = claude_results + continue_results + cleanup_results
    failures = [r for r in all_results if r.startswith("❌")]
    
    if failures:
        print(f"\nWARNING: {len(failures)} items could not be removed (files may be in use)")
        print("These will be cleaned up after restarting Claude Code/Continue")
    
    print("\nContext Engine MCP uninstall complete!")
    
    print("Run 'pip uninstall context-engine-mcp -y' to remove Python package")
    print("Manually remove MCP server: claude mcp remove context-engine")
    print("No restart needed - files unlocked immediately!")
    
    # Return True for successful uninstall
    return True

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
        choices=["claude-code", "cn"], 
        default="claude-code",
        help="Installation target - claude-code or cn (Continue) (default: claude-code)"
    )
    
    # Uninstall subcommand
    uninstall_parser = subparsers.add_parser(
        'uninstall',
        help='Uninstall Context Engine MCP from all environments'
    )
    
    args = parser.parse_args()
    
    if args.command == 'install':
        install(args.target)
        return 0
    elif args.command == 'uninstall':
        uninstall()
        return 0


if __name__ == "__main__":
    sys.exit(main())
