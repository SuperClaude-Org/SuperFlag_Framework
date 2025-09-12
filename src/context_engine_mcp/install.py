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
    target_dir = home / ".context"
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
    
    # Try multiple locations for flags.yaml
    possible_paths = [
        Path(__file__).parent.parent.parent / "flags.yaml",  # Development
        Path(sys.prefix) / "share" / "context-engine-mcp" / "flags.yaml",  # Installed
    ]
    
    source_file = None
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

def check_existing_mcp_servers():
    """Check which MCP servers are already installed"""
    import subprocess
    try:
        result = subprocess.run(['claude', 'mcp', 'list'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return result.stdout
        return ""
    except:
        return ""

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
    import subprocess
    
    # Check existing servers
    existing = check_existing_mcp_servers()
    
    # Ensure Python package is installed
    ensure_safe_installation()
    
    # Only install NPM-based servers automatically
    # For context-engine, let user decide between uv/python
    servers = [
        {
            "name": "sequential-thinking", 
            "package": "@modelcontextprotocol/server-sequential-thinking",
            "description": "Sequential problem solving"
        },
        {
            "name": "context7",
            "package": "@upstash/context7-mcp",
            "description": "Documentation and examples"
        }
    ]
    
    for server in servers:
        # Skip if already installed
        if server['name'] in existing:
            print(f"✓ {server['name']} already installed, skipping...")
            continue
        print(f"\n📦 Installing {server['name']}...")
        
        if 'package' in server:
            # NPM-based MCP server
            cmd = ['claude', 'mcp', 'add', '-s', 'user', '--', 
                   server['name'], 'npx', '-y', server['package']]
        else:
            # This shouldn't happen since we only have NPM servers now
            print(f"⚠ Skipping {server['name']} - manual configuration needed")
            continue
        
        try:
            # Windows needs shell=True
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, shell=True)
            if result.returncode == 0:
                print(f"✓ {server['name']} installed successfully")
            else:
                print(f"⚠ Failed to install {server['name']}: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"⚠ Installation of {server['name']} timed out")
        except Exception as e:
            print(f"⚠ Error installing {server['name']}: {e}")
    
    # Inform user about context-engine setup
    print("\n📌 For context-engine MCP server:")
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
version: 0.0.1
schema: v1
mcpServers:
- name: context-engine
  command: context-engine-mcp
  args: []
  env: {}

# --- Option 2: UV (Python package manager) ---
# Requires: uv in PATH or use full path like ~/.cargo/bin/uv
# name: Context Engine MCP
# version: 0.0.1
# schema: v1
# mcpServers:
# - name: context-engine
#   command: uv
#   args: ["run", "context-engine-mcp"]
#   env: {}

# --- Option 3: Development mode (pip install -e) ---
# name: Context Engine MCP
# version: 0.0.1
# schema: v1
# mcpServers:
# - name: context-engine
#   command: python
#   args: ["-m", "context_engine_mcp"]
#   env: {}

"""
        },
        {
            "filename": "sequential-thinking.yaml",
            "content": """# Sequential Thinking MCP - Step-by-step problem solving
# This server helps break down complex problems into manageable steps

name: Sequential Thinking MCP
version: 0.0.1
schema: v1
mcpServers:
- name: sequential-thinking
  command: npx
  args: ["-y", "@modelcontextprotocol/server-sequential-thinking"]
  env: {}

# Usage in Continue:
# 1. Type @ in the chat
# 2. Select "MCP"
# 3. Use sequential thinking for complex problems
"""
        },
        {
            "filename": "context7.yaml",
            "content": """# Context7 MCP - Up-to-date documentation and code examples
# Provides access to the latest library documentation

name: Context7 MCP
version: 0.0.1
schema: v1
mcpServers:
- name: context7
  command: npx
  args: ["-y", "@upstash/context7-mcp"]
  env: {}

# Usage in Continue:
# 1. Type @ in the chat
# 2. Select "MCP"
# 3. Ask for documentation about any library
# Example: "Get React hooks documentation"
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
            
            # Automatically install MCP servers via CLI
            print("\n📦 Installing MCP servers to Claude Code (user scope)...")
            print("  - context-engine (contextual flag system)")
            print("  - sequential-thinking (problem solving)")
            print("  - context7 (documentation)")
            
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
        print("   • list_available_flags() - View all 16 available flags")
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
        print("   • Available servers: context-engine, sequential-thinking, context7")
        print("\n📚 All configuration files: ~/.continue/mcpServers/")
    
    print("\n✅ Context Engine MCP installation completed!")
    print("-" * 50)

def kill_context_engine_processes():
    """Kill context-engine-mcp processes to unlock files"""
    killed = []
    
    if psutil is None:
        return ["ℹ️ psutil not available - manual process termination may be needed"]
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline'] or []
                name = proc.info['name'] or ''
                
                # Check if process is context-engine related
                if ('context-engine-mcp' in ' '.join(cmdline) or 
                    'context-engine-mcp' in name):
                    
                    proc.kill()
                    killed.append(f"✅ Killed process {proc.info['name']} (PID: {proc.info['pid']})")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if killed:
            time.sleep(1)  # Wait for processes to fully terminate
            
        return killed if killed else ["ℹ️ No context-engine processes found running"]
        
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
        # 1. Remove from ~/.claude.json
        claude_config_path = home / ".claude.json"
        if claude_config_path.exists():
            with open(claude_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if 'mcpServers' in config and 'context-engine' in config['mcpServers']:
                del config['mcpServers']['context-engine']
                
                with open(claude_config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                results.append("✅ Removed context-engine from ~/.claude.json")
            else:
                results.append("ℹ️ context-engine not found in ~/.claude.json")
        else:
            results.append("ℹ️ ~/.claude.json not found")
        
        # 2. Remove @CONTEXT-ENGINE.md reference from CLAUDE.md
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
        
        # Remove .context directory with backup
        home = get_home_dir()
        context_dir = home / ".context"
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
                
                # Remove the entire .context directory
                shutil.rmtree(context_dir)
                results.append("✅ Removed ~/.context directory (flags.yaml, etc.)")
            except Exception as e:
                results.append(f"⚠️ Could not remove .context directory: {str(e)}")
        else:
            results.append("ℹ️ .context directory not found")
        
        results.append("ℹ️ Run 'pip uninstall context-engine-mcp -y' to remove Python package")
        
    except Exception as e:
        results.append(f"❌ Error cleaning up files: {str(e)}")
    
    return results

def uninstall():
    """Main uninstall function - removes Context Engine from all environments"""
    print("🗑️ Uninstalling Context Engine MCP...")
    print("🔥 Force-killing processes and immediately removing files...")
    
    # 1. Claude Code cleanup
    print("\n📝 Cleaning up Claude Code configuration...")
    claude_results = uninstall_claude_code()
    for result in claude_results:
        print(f"  {result}")
    
    # 2. Continue cleanup
    print("\n🔧 Cleaning up Continue configuration...")
    continue_results = uninstall_continue()
    for result in continue_results:
        print(f"  {result}")
    
    # 3. Common files cleanup
    print("\n🧹 Cleaning up common files...")
    cleanup_results = cleanup_common_files()
    for result in cleanup_results:
        print(f"  {result}")
    
    # Check for any failures
    all_results = claude_results + continue_results + cleanup_results
    failures = [r for r in all_results if r.startswith("❌")]
    
    if failures:
        print(f"\n⚠️ {len(failures)} items could not be removed (files may be in use)")
        print("💡 These will be cleaned up after restarting Claude Code/Continue")
    
    print("\n✅ Context Engine MCP uninstall complete!")
    
    print("🏷️ Run 'pip uninstall context-engine-mcp -y' to remove Python package")
    print("💡 No restart needed - files unlocked immediately!")
    
    return {
        "status": "success", 
        "claude_code": claude_results,
        "continue": continue_results,
        "cleanup": cleanup_results,
        "failures": failures
    }

def main():
    """Main entry point for the installer"""
    import argparse
    try:
        from .__version__ import __version__
    except ImportError:
        __version__ = "unknown"
    
    parser = argparse.ArgumentParser(description="Install/Uninstall Context Engine MCP")
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"context-engine-mcp {__version__}"
    )
    parser.add_argument(
        "--target", 
        choices=["claude-code", "cn"], 
        default="claude-code",
        help="Installation target - claude-code or cn (Continue) (default: claude-code)"
    )
    parser.add_argument(
        "--uninstall", "-u",
        action="store_true", 
        help="Uninstall Context Engine MCP"
    )
    args = parser.parse_args()
    
    if args.uninstall:
        uninstall()
    else:
        install(args.target)

if __name__ == "__main__":
    main()