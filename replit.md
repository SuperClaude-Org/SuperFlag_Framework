# Context Engine MCP

## Overview

Context Engine MCP is a Model Context Protocol (MCP) server that provides AI assistants with 17 specialized contextual flags to control their working modes and behavior. The system allows users to apply flags like `--strict` for zero-error enforcement, `--auto` for automatic flag selection, or `--save` for creating handoff documentation. The project is designed as a Python package that integrates with AI coding assistants like Claude Code and Continue.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

**Package Architecture**: Python package following PEP 440 standards with a modular structure separating concerns into distinct modules (server, installation, prompts, and versioning).

**MCP Server Implementation**: Built on FastMCP framework to handle Model Context Protocol communication. The server runs as a stdio-based service that AI assistants can communicate with to retrieve flag definitions and directives.

**Session Management**: Thread-safe, memory-based session tracking system that automatically detects sessions using thread and process IDs. Sessions maintain flag usage history with automatic cleanup of expired sessions (1-hour TTL, 100 session limit).

**Flag System**: 17 predefined contextual flags stored in YAML configuration with metadata including descriptions, working philosophies, and directive details. Flags cover various AI working modes from analysis (`--analyze`) to task management (`--todo`).

**Installation System**: Cross-platform installer supporting both Claude Code and Continue IDE integrations. Uses pipx for isolated package installation and automatically configures MCP server settings in target applications.

**Configuration Management**: Thread-safe configuration handling with user-editable flags.yaml file stored in `~/.context-engine` directory. System provides backup and update mechanisms for configuration files.

**CLI Interface**: Command-line interface accessible via `context-engine` command for installation and setup operations across different target environments.

## External Dependencies

**Python Runtime**: Requires Python >= 3.10 with support for modern async/await patterns and importlib.resources.

**FastMCP Framework**: Core MCP server implementation providing stdio transport and protocol handling.

**PyYAML**: Configuration file parsing for flags.yaml definitions and metadata.

**PSUtil**: Optional dependency for enhanced process management during installation (graceful fallback if unavailable).

**Package Distribution**: Published to PyPI (stable releases) and TestPyPI (pre-releases) with automated CI/CD via GitHub Actions using OIDC authentication.

**Target AI Assistants**: Designed to integrate with Claude Code and Continue IDE through MCP protocol configuration files and context setup.

**Development Tools**: Uses Hatchling for package building, pytest for testing, and twine for package validation and distribution.