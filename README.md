# Context Engine MCP

17 contextual flags for AI assistants. Control how AI thinks and works.

## What it does

Gives AI specialized working modes through flags. Like `--strict` for zero errors or `--auto` for automatic flag selection.

## Quick Start

```bash
# Install (recommended)
pipx install context-engine-mcp

# For Claude Code
context-engine-install

# For Continue 
context-engine-install --target cn
```

Then use in AI:
- `"Fix this bug --auto"` → AI selects best flags
- `"--save"` → Creates handoff documentation
- `"Analyze --strict"` → Multi-angle analysis with zero errors

**Note**: Manual MCP server setup required after installation (see details below).

## 17 Flags

| Flag | Purpose |
|------|---------|
| `--analyze` | Multi-angle systematic analysis |
| `--auto` | AI selects optimal flag combination |
| `--concise` | Minimal communication |
| `--explain` | Progressive disclosure |
| `--git` | Version control best practices |
| `--lean` | Essential focus only |
| `--load` | Load handoff documentation |
| `--parallel` | Multi-agent processing |
| `--performance` | Speed and efficiency optimization |
| `--readonly` | Analysis only mode |
| `--refactor` | Code quality improvement |
| `--research` | Technology investigation |
| `--reset` | Reset session flag state |
| `--save` | Handoff documentation |
| `--seq` | Sequential thinking |
| `--strict` | Zero-error enforcement |
| `--todo` | Task management |

## Installation Details

### Claude Code
```bash
# Install package
pipx install context-engine-mcp

# Install configuration files
context-engine-install
```

**⚠️ Important**: After installation, you must manually add the MCP server:

```bash
# Choose ONE of these commands:

# Standard Python installation
claude mcp add -s user -- context-engine context-engine-mcp

# UV installation  
claude mcp add -s user -- context-engine uv run context-engine-mcp

# Custom command
claude mcp add -s user -- context-engine <your-command>
```

This creates MCP server configuration and installs to `~/.claude/`.

### Continue Extension  
```bash
# Install package
pipx install context-engine-mcp

# Install configuration files
context-engine-install --target cn
```

**⚠️ Configuration Required**: Edit `~/.continue/mcpServers/context-engine.yaml` and uncomment ONE option:

```yaml
# Option 1: Standard Python (most common)
name: Context Engine MCP
command: context-engine-mcp

# Option 2: UV installation  
# name: Context Engine MCP
# command: uv
# args: ["run", "context-engine-mcp"]

# Option 3: Custom installation
# name: Context Engine MCP  
# command: <your-custom-command>
```

Then restart VS Code and type `@` in Continue chat to access MCP tools.

## How to Use

### In AI Chat
```python
# Auto mode - AI selects flags
"Refactor this code --auto"

# Direct flags
"--save"  # Creates handoff doc
"--analyze --strict"  # Multi-angle analysis with zero errors
"--reset --analyze"  # Reset session and reapply

# Combined flags
"Review this --analyze --strict --seq"
```

### MCP Tools (Called by AI)
- `list_available_flags()` - Shows all 16 flags
- `get_directives(['--flag1', '--flag2'])` - Activates flags

**Development**: For local development, use `pip install -e .` instead of pipx.

**Configuration Updates**: Edit `~/.context/flags.yaml` and restart MCP server to apply changes.

### Session Management
- Duplicate flags show REMINDER only (saves tokens)
- Use `--reset` when changing context
- AI tracks which flags are active

## Special: --auto Workflow

`--auto` is NOT a flag. It's an instruction for AI to:
1. Analyze your task
2. Select appropriate flags
3. Apply them automatically

Example: `"Fix this bug --auto"` → AI might choose `--analyze`, `--strict`, `--seq`

## Files Created

```
~/.claude/
├── CLAUDE.md           # References @CONTEXT-ENGINE.md
└── CONTEXT-ENGINE.md   # Flag instructions (auto-updated)

~/.continue/
├── config.yaml         # Contains Context Engine rules
└── mcpServers/
    ├── context-engine.yaml
    ├── sequential-thinking.yaml
    └── context7.yaml

~/.context/
└── flags.yaml          # Flag definitions
```

## Uninstallation

```bash
# Uninstall (recommended)
context-engine-install --uninstall

# Remove Python package
pip uninstall context-engine-mcp -y
```

**Note**: During uninstallation, `~/.context/flags.yaml` is backed up to `~/flags.yaml.backup_YYYYMMDD_HHMMSS` before removal. During installation, existing flags.yaml is automatically backed up and updated to the latest version.

## License

MIT