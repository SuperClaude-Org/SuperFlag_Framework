#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server Management for SuperFlag.
Handles registration, status checking, and removal of MCP servers.
"""

import json
import subprocess
import sys
from pathlib import Path
from shutil import which
from typing import Dict, Any, Optional, Tuple, List


class MCPManager:
    """Manages MCP server registration for Claude Code and other platforms."""

    def __init__(self):
        self.home = Path.home()
        self.claude_config = self.home / ".claude.json"
        self.gemini_config = self.home / ".gemini" / "settings.json"

    def check_claude_mcp_registered(self, server_name: str = "superflag") -> bool:
        """
        Check if a MCP server is registered in Claude Code.

        Args:
            server_name: Name of the MCP server to check

        Returns:
            True if server is registered, False otherwise
        """
        if not self.claude_config.exists():
            return False

        try:
            with open(self.claude_config, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Check mcpServers section
            mcp_servers = config.get('mcpServers', {})
            return server_name in mcp_servers

        except (json.JSONDecodeError, IOError):
            return False

    def check_gemini_mcp_registered(self, server_name: str = "superflag") -> bool:
        """
        Check if a MCP server is registered in Gemini CLI.

        Args:
            server_name: Name of the MCP server to check

        Returns:
            True if server is registered, False otherwise
        """
        if not self.gemini_config.exists():
            return False

        try:
            with open(self.gemini_config, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Check mcpServers section
            mcp_servers = config.get('mcpServers', {})
            return server_name in mcp_servers

        except (json.JSONDecodeError, IOError):
            return False

    def register_claude_mcp(self, command: str, server_name: str = "superflag") -> Tuple[bool, str]:
        """
        Register MCP server with Claude CLI.

        Args:
            command: The command to register (e.g., 'superflag', '"python -m superflag"')
            server_name: Name for the MCP server

        Returns:
            Tuple of (success, message)
        """
        # Check if Claude CLI is available
        if not which('claude'):
            return False, "Claude CLI not found"

        # Check if already registered
        if self.check_claude_mcp_registered(server_name):
            return True, f"MCP server '{server_name}' already registered"

        try:
            # Build the command
            cmd_parts = ['claude', 'mcp', 'add', server_name, '-s', 'user']

            # Handle command with spaces (needs to be passed as single argument)
            if ' ' in command and not command.startswith('"'):
                cmd_parts.append(command)
            else:
                cmd_parts.append(command.strip('"'))

            # Execute registration (use shell=True on Windows for better command handling)
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=10,
                shell=(sys.platform == 'win32')
            )

            if result.returncode == 0:
                return True, f"Successfully registered MCP server '{server_name}'"
            else:
                # Check for common errors
                if "already exists" in result.stderr:
                    return True, f"MCP server '{server_name}' already exists"
                return False, f"Registration failed: {result.stderr.strip()}"

        except subprocess.TimeoutExpired:
            return False, "Registration timed out"
        except Exception as e:
            return False, f"Registration error: {str(e)}"

    def unregister_claude_mcp(self, server_name: str = "superflag") -> Tuple[bool, str]:
        """
        Unregister MCP server from Claude CLI.

        Args:
            server_name: Name of the MCP server to remove

        Returns:
            Tuple of (success, message)
        """
        # Check if Claude CLI is available
        if not which('claude'):
            # If CLI not available, try manual removal
            return self._manual_remove_claude_mcp(server_name)

        try:
            # Use claude mcp remove command
            result = subprocess.run(
                ['claude', 'mcp', 'remove', server_name],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return True, f"Successfully removed MCP server '{server_name}'"
            else:
                # Try manual removal as fallback
                return self._manual_remove_claude_mcp(server_name)

        except subprocess.TimeoutExpired:
            return False, "Removal timed out"
        except Exception:
            # Try manual removal as fallback
            return self._manual_remove_claude_mcp(server_name)

    def _manual_remove_claude_mcp(self, server_name: str) -> Tuple[bool, str]:
        """
        Manually remove MCP server from .claude.json.

        Args:
            server_name: Name of the MCP server to remove

        Returns:
            Tuple of (success, message)
        """
        if not self.claude_config.exists():
            return True, "No Claude configuration found"

        try:
            with open(self.claude_config, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Check and remove from mcpServers
            mcp_servers = config.get('mcpServers', {})
            if server_name in mcp_servers:
                del mcp_servers[server_name]

                # Write updated config
                with open(self.claude_config, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)

                return True, f"Manually removed MCP server '{server_name}' from config"
            else:
                return True, f"MCP server '{server_name}' not found in config"

        except (json.JSONDecodeError, IOError) as e:
            return False, f"Failed to modify config: {str(e)}"

    def register_gemini_mcp(self, command: str, args: List[str] = None,
                          server_name: str = "superflag") -> Tuple[bool, str]:
        """
        Register MCP server in Gemini CLI settings.

        Args:
            command: The command to execute
            args: Arguments for the command
            server_name: Name for the MCP server

        Returns:
            Tuple of (success, message)
        """
        # Ensure directory exists
        self.gemini_config.parent.mkdir(parents=True, exist_ok=True)

        # Load or create config
        config = {}
        if self.gemini_config.exists():
            try:
                with open(self.gemini_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError):
                config = {}

        # Prepare MCP servers section
        if 'mcpServers' not in config:
            config['mcpServers'] = {}

        # Check if already exists
        if server_name in config['mcpServers']:
            return True, f"MCP server '{server_name}' already registered in Gemini CLI"

        # Add the server configuration
        config['mcpServers'][server_name] = {
            "type": "stdio",
            "command": command,
            "args": args or [],
            "env": {}
        }

        # Write updated config
        try:
            with open(self.gemini_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True, f"Successfully registered MCP server '{server_name}' in Gemini CLI"
        except IOError as e:
            return False, f"Failed to write Gemini config: {str(e)}"

    def unregister_gemini_mcp(self, server_name: str = "superflag") -> Tuple[bool, str]:
        """
        Unregister MCP server from Gemini CLI settings.

        Args:
            server_name: Name of the MCP server to remove

        Returns:
            Tuple of (success, message)
        """
        if not self.gemini_config.exists():
            return True, "No Gemini configuration found"

        try:
            with open(self.gemini_config, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Check and remove from mcpServers
            mcp_servers = config.get('mcpServers', {})
            if server_name in mcp_servers:
                del mcp_servers[server_name]

                # Write updated config
                with open(self.gemini_config, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)

                return True, f"Removed MCP server '{server_name}' from Gemini config"
            else:
                return True, f"MCP server '{server_name}' not found in Gemini config"

        except (json.JSONDecodeError, IOError) as e:
            return False, f"Failed to modify Gemini config: {str(e)}"

    def get_mcp_status(self, platform: str = "claude-code") -> Dict[str, Any]:
        """
        Get comprehensive MCP status for a platform.

        Args:
            platform: Target platform ('claude-code' or 'gemini-cli')

        Returns:
            Dict with registration status and details
        """
        if platform == "claude-code":
            registered = self.check_claude_mcp_registered()
            config_exists = self.claude_config.exists()
            cli_available = which('claude') is not None

            return {
                'registered': registered,
                'config_exists': config_exists,
                'cli_available': cli_available,
                'platform': 'Claude Code'
            }

        elif platform == "gemini-cli" or platform == "gemini":
            registered = self.check_gemini_mcp_registered()
            config_exists = self.gemini_config.exists()

            return {
                'registered': registered,
                'config_exists': config_exists,
                'platform': 'Gemini CLI'
            }

        else:
            return {
                'registered': False,
                'config_exists': False,
                'platform': 'Unknown'
            }


def test_mcp_manager():
    """Test MCP manager functionality."""
    manager = MCPManager()

    # Test Claude status
    claude_status = manager.get_mcp_status('claude-code')
    print(f"Claude Code MCP Status: {claude_status}")

    # Test Gemini status
    gemini_status = manager.get_mcp_status('gemini-cli')
    print(f"Gemini CLI MCP Status: {gemini_status}")


if __name__ == '__main__':
    test_mcp_manager()