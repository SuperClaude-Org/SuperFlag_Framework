# SuperFlag

> **⚠️ MIGRATION NOTICE**: If you previously installed `context-engine-mcp`, please uninstall it and install `superflag` instead:
> ```bash
> pip uninstall context-engine-mcp
> pip install superflag
> ```

![Claude Code](https://img.shields.io/badge/Claude%20Code-supported-F37435)
![Gemini CLI](https://img.shields.io/badge/Gemini%20CLI-supported-1ABC9C)
![Continue](https://img.shields.io/badge/Continue-supported-FFFFFF)

> **Note**: This project was inspired by the pioneering work in [SuperClaude Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) and [SuperGemini Framework](https://github.com/SuperClaude-Org/SuperGemini_Framework). Special thanks to [SuperClaude-Org](https://github.com/SuperClaude-Org) team members [@NomenAK](https://github.com/NomenAK) and [@mithun50](https://github.com/mithun50) whose work made this possible.

SuperFlag provides 18 contextual flags that guide assistant behavior (e.g., `--strict`, `--auto`). It exposes an MCP stdio server and small setup helpers for common clients.

## Quick Start

```bash
# Install
pip install superflag

# Interactive installation (choose platforms)
superflag install

# Direct installation
superflag install --target claude-code  # Claude Code only
superflag install --target gemini-cli   # Gemini CLI only
superflag install --target cn           # Continue only
```

Then in your client/assistant, use prompts with flags:
- "Fix this bug --auto" (auto-select flags)
- "--save" (handoff documentation)
- "Analyze --strict" (precise, zero-tolerance mode)

## 18 Flags

| Flag | Purpose |
|------|---------|
| `--analyze` | Multi-angle systematic analysis |
| `--auto` | AI selects optimal flag combination |
| `--collab` | Co-develop solutions through trust-based iteration |
| `--concise` | Minimal communication |
| `--discover` | Discover existing solutions before building new |
| `--explain` | Progressive disclosure |
| `--git` | Version control best practices |
| `--lean` | Essential focus only |
| `--load` | Load handoff documentation |
| `--parallel` | Multi-agent processing |
| `--performance` | Speed and efficiency optimization |
| `--readonly` | Analysis only mode |
| `--refactor` | Code quality improvement |
| `--reset` | Reset all flag states to new (clears session cache) |
| `--save` | Handoff documentation |
| `--seq` | Sequential thinking |
| `--strict` | Zero-error enforcement |
| `--todo` | Task management |

## Installation

### Claude Code
```bash
# Install package
pip install superflag

# Install configuration files (automatic MCP registration)
superflag install
```

### Continue Extension
```bash
# Install package
pip install superflag

# Install configuration files
superflag install --target cn
```

Edit `~/.continue/mcpServers/superflag.yaml`:

```yaml
# Standard Python (most common)
name: SuperFlag
command: python
args: ["-m", "superflag"]

# Or use absolute path to specific environment
# name: SuperFlag
# command: /path/to/venv/bin/python
# args: ["-m", "superflag"]
```

Restart VS Code, then type `@` in Continue chat to access MCP tools.

### Gemini CLI
```bash
# Install package
pip install superflag

# Install configuration files for Gemini CLI
superflag install --target gemini-cli
```

This command:
- Appends `@SUPERFLAG.md` to `~/.gemini/GEMINI.md` (adds once; no duplicate)
- Writes latest instructions to `~/.gemini/SUPERFLAG.md`

Register the MCP stdio command in Gemini CLI settings:
  - Command: `python -m superflag`
  - Args: `[]`
  - Transport: stdio

MCP registration (example)
- File: `~/.gemini/settings.json`
- Add or merge this into the `mcpServers` section:

```json
{
  "mcpServers": {
    "superflag": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "superflag"],
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
- pip (python -m):
```json
{
  "mcpServers": {
    "superflag": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "superflag"],
      "env": {}
    }
  }
}
```

- venv absolute path (Windows):
```json
{
  "mcpServers": {
    "superflag": {
      "type": "stdio",
      "command": "C:\\path\\to\\venv\\Scripts\\superflag.exe",
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
    "superflag": {
      "type": "stdio",
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "superflag"],
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
- `get_directives(['--flag1', '--flag2'])` - Activates flags

Development: use `pip install -e .` for editable installs.

Configuration updates: edit `~/.superflag/flags.yaml` and restart the MCP server.

### Optional MCP Servers
Additional MCP servers can complement certain flags:

#### For `--seq` flag:
```bash
# Sequential thinking server  
claude mcp add -s user -- sequential-thinking npx -y @modelcontextprotocol/server-sequential-thinking
```

These are optional; SuperFlag works without them.

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
├── CLAUDE.md                     # References @SUPERFLAG.md
├── SUPERFLAG.md             # Flag instructions (auto-updated)
├── hooks/
│   └── superflag.py              # Hook for flag detection (Claude Code only)
└── settings.json                 # Updated with hook registration (Claude Code only)

~/.continue/
├── config.yaml         # Contains SuperFlag rules
└── mcpServers/
    ├── superflag.yaml
    ├── sequential-thinking.yaml
    └── context7.yaml

~/.superflag/
└── flags.yaml          # Flag definitions

~/.gemini/
├── GEMINI.md           # References @SUPERFLAG.md
└── SUPERFLAG.md   # Flag instructions (auto-updated)
```

## Uninstallation

```bash
# Complete uninstall from all environments (Claude Code + Continue)
superflag uninstall

# Remove Python package
pip uninstall superflag
```

Note: During uninstallation, `~/.superflag/flags.yaml` is backed up to `~/flags.yaml.backup_YYYYMMDD_HHMMSS` before removal. During installation, existing flags.yaml is backed up and updated to the latest version.

Claude Code note: Uninstall removes the `@SUPERFLAG.md` reference from `~/.claude/CLAUDE.md`, deletes `~/.claude/SUPERFLAG.md` if present, removes the hook file from `~/.claude/hooks/superflag.py`, and removes the hook registration from `~/.claude/settings.json`.

Gemini CLI note: Uninstall removes the `@SUPERFLAG.md` reference from `~/.gemini/GEMINI.md` and deletes `~/.gemini/SUPERFLAG.md` if present.

Continue note: Uninstall removes the SuperFlag rules from `~/.continue/config.yaml` (when present) and deletes `~/.continue/mcpServers/superflag.yaml` if present.

## License
MIT
