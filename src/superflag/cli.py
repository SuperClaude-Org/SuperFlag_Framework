#!/usr/bin/env python3
"""
Unified CLI for SuperFlag - handles both MCP server and installation commands
"""

import sys
import argparse
from .__version__ import __version__


def main():
    """Main entry point for superflag command"""

    # Check if it's being run as MCP server (no arguments or stdin mode)
    if len(sys.argv) == 1 or (len(sys.argv) == 1 and not sys.stdin.isatty()):
        # Run as MCP server
        from .__main__ import main as server_main
        server_main()
        return

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        prog='superflag',
        description='SuperFlag - Contextual flag system for AI assistants'
    )

    # Add version argument
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'superflag {__version__}'
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Install command
    install_parser = subparsers.add_parser('install', help='Install SuperFlag')
    install_parser.add_argument(
        '--target', '-t',
        choices=['claude-code', 'cn', 'continue', 'gemini-cli', 'gemini'],
        default='claude-code',
        help='Target environment (default: claude-code)'
    )

    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall SuperFlag')

    # Version command (alternative to --version)
    version_parser = subparsers.add_parser('version', help='Show version')

    # Handle --install and --uninstall shortcuts
    if '--install' in sys.argv:
        sys.argv[sys.argv.index('--install')] = 'install'
    if '--uninstall' in sys.argv:
        sys.argv[sys.argv.index('--uninstall')] = 'uninstall'

    args = parser.parse_args()

    # Execute commands
    if args.command == 'install':
        from .install import main as install_main
        # Convert target names for compatibility
        target_map = {
            'claude-code': 'claude-code',
            'cn': 'cn',
            'continue': 'cn',
            'gemini-cli': 'gemini-cli',
            'gemini': 'gemini-cli'
        }
        target = target_map.get(args.target, 'claude-code')
        # Set up sys.argv for install module
        sys.argv = ['superflag-install', 'install', '--target', target]
        install_main()

    elif args.command == 'uninstall':
        from .install import main as install_main
        sys.argv = ['superflag-install', 'uninstall']
        install_main()

    elif args.command == 'version':
        print(f'superflag {__version__}')

    else:
        # No command specified, show help
        parser.print_help()


if __name__ == '__main__':
    main()