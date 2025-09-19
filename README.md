# SuperFlag

> **🚀 TYPESCRIPT MIGRATION COMPLETE**: SuperFlag has been fully migrated to TypeScript/Node.js with MCP support!

![Claude Code](https://img.shields.io/badge/Claude%20Code-supported-F37435)
![NPM](https://img.shields.io/badge/NPM-latest-CB3837)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6)

> **Note**: This project was inspired by the pioneering work in [SuperClaude Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) and [SuperGemini Framework](https://github.com/SuperClaude-Org/SuperGemini_Framework). Special thanks to [SuperClaude-Org](https://github.com/SuperClaude-Org) team members [@NomenAK](https://github.com/NomenAK) and [@mithun50](https://github.com/mithun50) whose work made this possible.

SuperFlag provides 18 contextual flags that guide AI assistant behavior through precise directives. It exposes an MCP stdio server for seamless integration with modern AI development tools.

## Migration Notice

**Python version is DEPRECATED** - All users should migrate to the TypeScript version:

### For Existing Python Users
```bash
# 1. Uninstall old Python version
superflag uninstall  # Remove configurations
pip uninstall superflag  # Remove package

# 2. Install new TypeScript version
npm install -g @superclaude-org/superflag
superflag install cc  # Configure Claude Code
```

## Quick Start

```bash
# Install globally
npm install -g @superclaude-org/superflag

# Interactive installation (choose platforms)
superflag install

# Direct installation for Claude Code
superflag install cc

# MCP server automatically registered during installation
```

Then use flags in your AI assistant:
- "Fix this bug --analyze --strict"
- "Refactor --auto" (auto-select optimal flags)
- "--save" (create handoff documentation)

## 18 Available Flags

| Flag | Purpose |
|------|---------|
| `--analyze` | Multi-perspective systematic analysis |
| `--auto` | AI selects optimal flag combination |
| `--collab` | Co-develop solutions through trust-based iteration |
| `--concise` | Minimal, professional communication |
| `--discover` | Research existing solutions before building |
| `--explain` | Progressive disclosure explanations |
| `--git` | Version control best practices |
| `--lean` | Essential focus only, eliminate waste |
| `--load` | Load handoff documentation context |
| `--parallel` | Multi-agent concurrent processing |
| `--performance` | Speed and efficiency optimization |
| `--readonly` | Analysis only, no modifications |
| `--refactor` | Safe code structure improvements |
| `--reset` | Reset session state, clear flag cache |
| `--save` | Create handoff documentation |
| `--seq` | Sequential step-by-step thinking |
| `--strict` | Zero-error enforcement with transparency |
| `--todo` | Structured task management |

## Installation

### Prerequisites
- Node.js 16+
- Target platform installed (Claude Code, Gemini CLI, or Continue)

### Quick Setup (All Platforms)
```bash
# Install package globally
npm install -g @superclaude-org/superflag

# Interactive installation - choose your platforms
superflag install
```

The interactive installer will:
- Detect installed platforms
- Let you select which ones to configure
- **Automatically register MCP servers** for all platforms
- Set up configuration files and flag detection

### Platform-Specific Installation

#### Claude Code
```bash
# Direct installation (MCP server auto-registered)
superflag install cc

# Verify connection
claude mcp list
```

Creates:
- `~/.claude/CLAUDE.md` - References SuperFlag
- `~/.claude/SUPERFLAG.md` - Flag instructions
- `~/.claude/hooks/superflag.py` - Flag detection hook

**Manual MCP Registration (if auto-registration fails):**
```bash
# Add MCP server manually
claude mcp add superflag npx @superclaude-org/superflag@latest -s user

# Or add to ~/.claude.json
{
  "mcpServers": {
    "superflag": {
      "command": "npx",
      "args": ["@superclaude-org/superflag@latest"],
      "env": {}
    }
  }
}
```

#### Gemini CLI
```bash
# Direct installation (MCP server auto-registered)
superflag install gemini
```

Creates:
- `~/.gemini/GEMINI.md` - References SuperFlag
- `~/.gemini/SUPERFLAG.md` - Flag instructions

**Manual MCP Registration (if auto-registration fails):**
```json
// Edit ~/.gemini/settings.json
{
  "mcpServers": {
    "superflag": {
      "type": "stdio",
      "command": "npx",
      "args": ["@superclaude-org/superflag@latest"],
      "env": {}
    }
  }
}
```

#### Continue (VS Code Extension)
```bash
# Direct installation (MCP server auto-registered)
superflag install cn
```

Creates:
- `~/.continue/config.yaml` - SuperFlag rules
- `~/.continue/mcpServers/superflag.yaml` - MCP server configuration

**Manual MCP Registration (if auto-registration fails):**
```yaml
# Create ~/.continue/mcpServers/superflag.yaml
name: SuperFlag
command: npx
args:
  - '@superclaude-org/superflag@latest'
env: {}
```

### Batch Installation
```bash
# Install for all supported platforms
superflag install all

# Install for specific combinations
superflag install cc gemini  # Claude Code + Gemini CLI
superflag install cn         # Continue only
```

## Usage

### Natural Language with Flags
All platforms support using flags in natural conversation:

```bash
# Auto mode - AI selects appropriate flags
"Optimize this code --auto"

# Specific flag combinations
"--analyze --strict"  # Thorough analysis with zero-error enforcement
"--save --explain"    # Create documentation with detailed explanations
"--reset --todo"      # Reset session and start task tracking

# Sequential workflows
"Review architecture --discover --analyze --seq"
```

### Platform-Specific Usage

#### Claude Code
```bash
# Direct chat with flags
"Fix this bug --analyze --strict"
"Create documentation --save --explain"

# MCP tool access (advanced)
get_directives(['--flag1', '--flag2'])
```

#### Gemini CLI
```bash
# Chat with flags
"Refactor this code --auto --performance"

# MCP server commands
@superflag --analyze --todo
```

#### Continue (VS Code)
```bash
# In Continue chat
"Optimize this function --performance --lean"

# Use @ to access MCP tools
@get_directives(['--strict', '--analyze'])
```

### Session Management
- **Duplicate Detection**: Repeated flags show brief reminders instead of full directives
- **Session Reset**: Use `--reset` when switching tasks or contexts
- **Persistence**: Flag states persist through `/clear` or `/compact` - use `--reset` to reinitialize

## The `--auto` Flag

`--auto` enables intelligent flag selection:

| Usage | Behavior |
|-------|----------|
| `--auto` only | AI selects complete flag set automatically |
| `--auto --strict --analyze` | AI applies specified flags + may add others |
| `--strict --analyze` | Only specified flags, no auto-selection |

**Note**: Do not include `--auto` in direct `get_directives()` calls - it's for natural language use only.

## Configuration Files

### Claude Code
```
~/.claude/
├── CLAUDE.md                    # References @SUPERFLAG.md
├── SUPERFLAG.md                 # Flag instructions (auto-updated)
└── hooks/
    └── superflag.py             # Flag detection hook
```

### Gemini CLI
```
~/.gemini/
├── GEMINI.md                    # References @SUPERFLAG.md
├── SUPERFLAG.md                 # Flag instructions (auto-updated)
└── settings.json                # MCP server configuration (auto-registered)
```

### Continue
```
~/.continue/
├── config.yaml                  # SuperFlag rules and configuration
└── mcpServers/
    └── superflag.yaml           # MCP server settings (auto-registered)
```

### Shared Configuration
```
~/.superflag/
└── flags.yaml                  # Flag definitions and directives (all platforms)
```

## Configuration File Contents

### What Gets Created

**~/.claude/CLAUDE.md**
```markdown
@SUPERFLAG.md
```

**~/.gemini/GEMINI.md**
```markdown
@SUPERFLAG.md
```

**~/.continue/config.yaml**
```yaml
rules:
  - title: SuperFlag
    pattern: '--\w+'
    message: >-
      Flag detected. Execute MCP: get_directives([detected_flags])

      Available: --analyze, --strict, --performance, --refactor, --lean, --discover, --explain, --save, --parallel,
      --todo, --seq, --concise, --git, --readonly, --load, --collab, --reset, --auto
```

**~/.continue/mcpServers/superflag.yaml**
```yaml
name: SuperFlag
command: npx
args:
  - '@superclaude-org/superflag@latest'
env: {}
```

**~/.gemini/settings.json** (MCP section)
```json
{
  "mcpServers": {
    "superflag": {
      "type": "stdio",
      "command": "npx",
      "args": ["@superclaude-org/superflag@latest"],
      "env": {}
    }
  }
}
```

**~/.superflag/flags.yaml**
```yaml
# Contains all 18 flag definitions and their directives
# This file is shared across all platforms
# Auto-updated when SuperFlag package is updated
```

## Development

### Local Development
```bash
# Clone repository
git clone <repository>
cd superflag

# Install dependencies
npm install

# Build TypeScript
npm run build

# Test locally
npm link
superflag --version
```

### Version Management
Update version in `src/version.ts` - all other files sync automatically during build.

## Uninstallation

### Interactive Uninstallation
```bash
# Interactive removal - choose platforms to remove
superflag uninstall
```

### Platform-Specific Removal
```bash
# Remove from specific platforms
superflag uninstall cc          # Claude Code only
superflag uninstall gemini      # Gemini CLI only
superflag uninstall cn          # Continue only
superflag uninstall all         # All platforms
```

### Complete Removal
```bash
# Remove all configurations and package
superflag uninstall all
npm uninstall -g @superclaude-org/superflag
```

**Safety Features:**
- Configuration files are backed up to `~/flags.yaml.backup_YYYYMMDD_HHMMSS` before removal
- Interactive confirmation for each platform
- Selective removal - keep other platforms intact

## Migration from Python

### What Changed
- ✅ **Language**: Python → TypeScript/Node.js
- ✅ **Performance**: Faster startup and execution
- ✅ **Installation**: `pip` → `npm`
- ✅ **Dependencies**: No Python runtime required
- ✅ **MCP Integration**: Native TypeScript MCP support

### Breaking Changes
- Python package completely deprecated
- `pip install superflag` no longer supported
- Configuration file locations remain the same
- Flag behavior and directives unchanged

### Migration Steps
1. **Backup**: Export any custom configurations
2. **Uninstall**: Remove Python version completely
3. **Install**: Set up TypeScript version
4. **Verify**: Test flag functionality
5. **Cleanup**: Remove Python environments if no longer needed

## Troubleshooting

### Common Issues

**Auto-Registration Failed**
If MCP server wasn't automatically registered during installation:

```bash
# For Claude Code
claude mcp add superflag npx @superclaude-org/superflag@latest -s user

# For Gemini CLI - manually edit ~/.gemini/settings.json
{
  "mcpServers": {
    "superflag": {
      "type": "stdio",
      "command": "npx",
      "args": ["@superclaude-org/superflag@latest"],
      "env": {}
    }
  }
}

# For Continue - create ~/.continue/mcpServers/superflag.yaml
name: SuperFlag
command: npx
args:
  - '@superclaude-org/superflag@latest'
env: {}
```

**MCP Connection Issues**
```bash
# Check server status (Claude Code)
claude mcp list

# Re-register if needed
claude mcp remove superflag
superflag install cc  # Auto-register again
```

**Flags Not Working**
- Restart your AI platform after installation
- Verify configuration files exist:
  - Claude Code: `~/.claude/SUPERFLAG.md`
  - Gemini CLI: `~/.gemini/SUPERFLAG.md`
  - Continue: `~/.continue/config.yaml`
- Check MCP server connection (platform-specific)

**Version Conflicts**
- Ensure Python version is completely removed
- Use `npm list -g @superclaude-org/superflag` to verify installation
- Clear platform caches if switching from manual to auto-registration

## License

MIT

---

**Need Help?** File issues at: [GitHub Repository](https://github.com/superclaude-org/superflag)