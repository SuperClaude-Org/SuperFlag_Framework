# Context Engine MCP

![Claude Code](https://img.shields.io/badge/Claude%20Code-supported-F37435)
![Gemini CLI](https://img.shields.io/badge/Gemini%20CLI-supported-1ABC9C)
![Continue](https://img.shields.io/badge/Continue-supported-FFFFFF)

Context Engine provides 17 contextual flags that guide assistant behavior (e.g., `--strict`, `--auto`). It exposes an MCP stdio server and small setup helpers for common clients.

## Quick Start

```bash
# Install (recommended)
pipx install context-engine-mcp

# For Claude Code
context-engine install

# For Continue 
context-engine install --target cn
```

Then in your client/assistant, use prompts with flags:
- "Fix this bug --auto" (auto-select flags)
- "--save" (handoff documentation)
- "Analyze --strict" (precise, zero-tolerance mode)

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
| `--reset` | Reset all flag states to new (clears session cache) |
| `--save` | Handoff documentation |
| `--seq` | Sequential thinking |
| `--strict` | Zero-error enforcement |
| `--todo` | Task management |

## Installation

### Claude Code
```bash
# Install package
pipx install context-engine-mcp

# Install configuration files
context-engine install
```

Register the MCP server with Claude CLI:

```bash
# Choose ONE of these commands:

# Standard Python installation
claude mcp add -s user -- context-engine context-engine-mcp

# UV installation  
claude mcp add -s user -- context-engine uv run context-engine-mcp

# Custom command
claude mcp add -s user -- context-engine <your-command>
```

This also writes `~/.claude/CONTEXT-ENGINE.md` and appends a reference to `~/.claude/CLAUDE.md`.

### Continue Extension  
```bash
# Install package
pipx install context-engine-mcp

# Install configuration files
context-engine install --target cn
```

Edit `~/.continue/mcpServers/context-engine.yaml` and uncomment ONE option:

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

Restart VS Code, then type `@` in Continue chat to access MCP tools.

### Gemini CLI
```bash
# Install package
pipx install context-engine-mcp

# Install configuration files for Gemini CLI
context-engine install --target gemini-cli
```

This command:
- Appends `@CONTEXT-ENGINE.md` to `~/.gemini/GEMINI.md` (adds once; no duplicate)
- Writes latest instructions to `~/.gemini/CONTEXT-ENGINE.md`

It does not modify `~/.gemini/settings.json`.
If required, register the MCP stdio command in Gemini CLI settings:
  - Command: `context-engine-mcp`
  - Args: `[]`
  - Transport: stdio

MCP registration (example)
- File: `~/.gemini/settings.json`
- Add or merge this into the `mcpServers` section:

```json
{
  "mcpServers": {
    "context-engine": {
      "type": "stdio",
      "command": "context-engine-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

Gemini CLI settings
- Location: `~/.gemini/settings.json`
- Structure:

```json
{
  "mcpServers": {
    "<server-name>": {
      "type": "stdio",
      "command": "<executable or interpreter>",
      "args": ["<arg1>", "<arg2>", "..."],
      "env": { "ENV_KEY": "value" }
    }
  }
}
```

Common setups
- pipx (PATH):
```json
{
  "mcpServers": {
    "context-engine": {
      "type": "stdio",
      "command": "context-engine-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

- uv (run):
```json
{
  "mcpServers": {
    "context-engine": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "context-engine-mcp"],
      "env": {}
    }
  }
}
```

- venv absolute path (Windows):
```json
{
  "mcpServers": {
    "context-engine": {
      "type": "stdio",
      "command": "C:\\path\\to\\venv\\Scripts\\context-engine.exe",
      "args": [],
      "env": {}
    }
  }
}
```

- venv with interpreter (module run):
```json
{
  "mcpServers": {
    "context-engine": {
      "type": "stdio",
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "context_engine_mcp"],
      "env": {}
    }
  }
}
```

Notes
- `type` is `stdio`.
- If the command is not on PATH, use an absolute path (escape backslashes on Windows).
- After editing, restart Gemini CLI and verify tools (e.g., list_available_flags).

## Usage

### In Chat
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

### MCP Tools
- `list_available_flags()` - Shows all 17 flags
- `get_directives(['--flag1', '--flag2'])` - Activates flags

Development: use `pip install -e .` for editable installs.

Configuration updates: edit `~/.context-engine/flags.yaml` and restart the MCP server.

### Optional MCP Servers
Additional MCP servers can complement certain flags:

#### For `--research` flag:
```bash
# Documentation and examples server
claude mcp add -s user -- context7 npx -y @upstash/context7-mcp
```

#### For `--seq` flag:
```bash
# Sequential thinking server  
claude mcp add -s user -- sequential-thinking npx -y @modelcontextprotocol/server-sequential-thinking
```

These are optional; Context Engine works without them.

### Session
- Duplicate flags produce a brief reminder instead of repeating full directives.
- Use `--reset` when the task/context changes (resets all flag states to new).
- The server tracks active flags per session.
- Note: In Claude, flag states persist through `/clear` or `/compact` commands. Use `--reset` to reinitialize.

## `--auto`
`--auto` instructs the assistant to analyze the task and pick appropriate flags (do not include `--auto` in get_directives calls).

Behavior
- `--auto` only: the assistant selects a full set of flags automatically.
- `--auto --flag1 --flag2`: the assistant applies `--flag1`, `--flag2` and may add additional flags if helpful. User‑specified flags take priority when there is overlap or conflict.
- `--flag1 --flag2` (without `--auto`): only the specified flags are applied.

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

~/.context-engine/
└── flags.yaml          # Flag definitions

~/.gemini/
├── GEMINI.md           # References @CONTEXT-ENGINE.md
└── CONTEXT-ENGINE.md   # Flag instructions (auto-updated)
```

## Uninstallation

```bash
# Complete uninstall from all environments (Claude Code + Continue)
context-engine uninstall

# Remove Python package
pipx uninstall context-engine-mcp
```

Note: During uninstallation, `~/.context-engine/flags.yaml` is backed up to `~/flags.yaml.backup_YYYYMMDD_HHMMSS` before removal. During installation, existing flags.yaml is backed up and updated to the latest version.

Claude Code note: Uninstall removes the reference in `~/.claude/CLAUDE.md` and deletes `~/.claude/CONTEXT-ENGINE.md` if present.

Gemini CLI note: Uninstall also removes the reference in `~/.gemini/GEMINI.md` and deletes `~/.gemini/CONTEXT-ENGINE.md` if present.

Continue note: Uninstall removes the Context Engine rules from `~/.continue/config.yaml` (when present) and deletes `~/.continue/mcpServers/context-engine.yaml` if present.

## License
MIT
