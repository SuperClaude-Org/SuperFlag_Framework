#!/usr/bin/env python3
"""
Environment detection for SuperFlag installation.
Detects installation method and provides appropriate MCP commands.
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class CommandSpec:
    """Normalized command representation for MCP registrations."""

    executable: str
    args: List[str]
    note: Optional[str] = None

    def as_cli(self) -> str:
        parts = [self.executable] + list(self.args)
        return " ".join(part for part in parts if part)


class EnvironmentDetector:
    """Detects Python package installation environment and provides MCP commands."""

    def __init__(self):
        self.detection_results = {}
        self.installation_method = None
        self.mcp_command = None

    def detect(self) -> Dict[str, Any]:
        """
        Main detection method that checks all installation methods.

        Returns:
            Dict containing:
                - method: Installation method (pipx/pip/uv/unknown)
                - command: Recommended MCP command
                - executable_path: Path to superflag executable if found
                - in_path: Whether superflag is in PATH
                - details: Additional installation details
        """
        # Check for superflag in PATH first
        superflag_path = which('superflag')
        in_path = superflag_path is not None

        # Try detection methods in order of preference
        detection_methods = [
            self._detect_pipx,
            self._detect_uv,
            self._detect_pip,
        ]

        for detect_method in detection_methods:
            try:
                is_installed, details = detect_method()
                if is_installed:
                    method_name = detect_method.__name__.replace('_detect_', '')
                    return self._build_response(method_name, in_path, superflag_path, details)
            except Exception:
                # Continue to next method if this one fails
                continue

        # Fallback if no specific method detected but superflag is importable
        if self._is_module_importable():
            return self._build_response('unknown', in_path, superflag_path, {})

        # Not installed at all
        return {
            'method': 'not_installed',
            'command': None,
            'executable_path': None,
            'in_path': False,
            'details': {}
        }

    def _detect_pipx(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect if superflag is installed via pipx.

        Returns:
            Tuple of (is_installed, details)
        """
        if not which('pipx'):
            return False, {}

        try:
            result = subprocess.run(
                ['pipx', 'list', '--short'],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )

            if result.returncode == 0 and 'superflag' in result.stdout:
                # Parse version if present
                for line in result.stdout.splitlines():
                    if line.startswith('superflag'):
                        parts = line.split()
                        version = parts[1] if len(parts) > 1 else 'unknown'
                        return True, {'version': version, 'pipx_installed': True}
                return True, {'pipx_installed': True}

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False, {}

    def _detect_uv(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect if superflag is installed via uv.

        Returns:
            Tuple of (is_installed, details)
        """
        if not which('uv'):
            return False, {}

        try:
            # Check uv pip list
            result = subprocess.run(
                ['uv', 'pip', 'list'],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )

            if result.returncode == 0 and 'superflag' in result.stdout:
                # Parse version
                for line in result.stdout.splitlines():
                    if line.strip().startswith('superflag'):
                        parts = line.split()
                        version = parts[1] if len(parts) > 1 else 'unknown'
                        return True, {'version': version, 'uv_installed': True}
                return True, {'uv_installed': True}

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False, {}

    def _detect_pip(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect if superflag is installed via pip.

        Returns:
            Tuple of (is_installed, details)
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', 'superflag'],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )

            if result.returncode == 0:
                details = {}
                for line in result.stdout.splitlines():
                    if line.startswith('Version:'):
                        details['version'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Location:'):
                        details['location'] = line.split(':', 1)[1].strip()
                    elif line.startswith('Editable project location:'):
                        details['editable'] = True
                        details['editable_location'] = line.split(':', 1)[1].strip()

                details['pip_installed'] = True
                return True, details

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False, {}

    def _is_module_importable(self) -> bool:
        """Check if superflag module can be imported."""
        try:
            from importlib.util import find_spec
            return find_spec('superflag') is not None
        except Exception:
            return False

    def _build_response(self, method: str, in_path: bool,
                       executable_path: Optional[str],
                       details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the response dictionary with appropriate MCP command.

        Args:
            method: Installation method detected
            in_path: Whether superflag is in PATH
            executable_path: Path to superflag executable
            details: Additional installation details

        Returns:
            Complete response dictionary
        """
        # Determine the appropriate MCP command
        if method == 'pipx':
            command = 'superflag'
            command_list = ['superflag']
            command_note = None
        elif method == 'uv':
            command = '"uv run superflag"'
            command_list = ['uv', 'run', 'superflag']
            command_note = 'UV requires quotes around the full command'
        elif method == 'pip':
            if in_path:
                command = 'superflag'
                command_list = ['superflag']
                command_note = None
            else:
                command = '"python -m superflag"'
                command_list = ['python', '-m', 'superflag']
                command_note = 'Using -m flag since superflag is not in PATH'
        else:
            # Unknown or fallback
            if in_path:
                command = 'superflag'
                command_list = ['superflag']
                command_note = None
            else:
                command = '"python -m superflag"'
                command_list = ['python', '-m', 'superflag']
                command_note = 'Using -m flag as safe fallback'

        response = {
            'method': method,
            'command': command,
            'command_list': command_list,
            'command_args': command_list[1:],
            'executable_path': executable_path,
            'in_path': in_path,
            'details': details
        }

        if command_note:
            response['command_note'] = command_note

        return response

    def get_mcp_install_command(self) -> Optional[str]:
        """Get the complete MCP install command for Claude CLI."""
        detection = self.detect()

        if detection['method'] == 'not_installed':
            return None

        spec = self.get_command_spec(detection)
        if not spec:
            return None

        return f"claude mcp add superflag -s user {spec.as_cli()}"

    def get_command_spec(self, detection: Optional[Dict[str, Any]] = None) -> Optional[CommandSpec]:
        """Return the normalized command specification for the detected environment."""
        if detection is None:
            detection = self.detect()

        if detection.get('method') == 'not_installed':
            return None

        command_list = detection.get('command_list') or []
        if not command_list and detection.get('command'):
            command_list = detection['command'].strip('"').split()

        if not command_list:
            return None

        executable, *args = command_list
        return CommandSpec(executable=executable, args=args, note=detection.get('command_note'))

    def print_detection_results(self):
        """Print formatted detection results for user display."""
        detection = self.detect()

        # ANSI colors
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        RESET = "\033[0m"
        BOLD = "\033[1m"

        if detection['method'] == 'not_installed':
            print(f"{YELLOW}[WARN] SuperFlag is not installed{RESET}")
            return

        # Format method name for display
        method_display = {
            'pipx': 'pipx',
            'pip': 'pip',
            'uv': 'uv',
            'unknown': 'Python module'
        }.get(detection['method'], detection['method'])

        print(f"{GREEN}[INFO] Detected installation: {method_display}{RESET}")

        if detection.get('details', {}).get('version'):
            print(f"       Version: {detection['details']['version']}")

        if detection.get('details', {}).get('editable'):
            print(f"       {YELLOW}Editable installation (development mode){RESET}")

        print(f"{CYAN}[INFO] Recommended MCP command:{RESET}")
        print(f"   {BOLD}{self.get_mcp_install_command()}{RESET}")

        if detection.get('command_note'):
            print(f"       {YELLOW}Note: {detection['command_note']}{RESET}")


def detect_and_suggest() -> str:
    """
    Convenience function to detect environment and return MCP command.

    Returns:
        MCP command string or None if not installed
    """
    detector = EnvironmentDetector()
    return detector.get_mcp_install_command()


if __name__ == '__main__':
    # For testing
    detector = EnvironmentDetector()
    detector.print_detection_results()