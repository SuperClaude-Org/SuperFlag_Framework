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

# Register MCP server in Claude Code
claude mcp add superflag npx @superclaude-org/superflag@latest -s user
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
- Claude Code installed

### Claude Code Setup
```bash
# Install package globally
npm install -g @superclaude-org/superflag

# Install and configure automatically
superflag install cc

# Verify MCP connection
claude mcp list
```

The installer automatically:
- Registers the MCP server with Claude Code
- Creates configuration files in `~/.claude/`
- Sets up flag detection hooks

### Manual MCP Registration
If automatic setup fails:
```bash
claude mcp add superflag npx @superclaude-org/superflag@latest -s user
```

## Usage

### In Claude Code Chat
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

### MCP Tool Access
The MCP server provides:
- `get_directives(['--flag1', '--flag2'])` - Activate flags and get directives

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

```
~/.claude/
├── CLAUDE.md                    # References @SUPERFLAG.md
├── SUPERFLAG.md                 # Flag instructions (auto-updated)
└── hooks/
    └── superflag.py             # Flag detection hook

~/.superflag/
└── flags.yaml                  # Flag definitions and directives
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

```bash
# Remove SuperFlag configuration and MCP registration
superflag uninstall

# Remove npm package
npm uninstall -g @superclaude-org/superflag
```

**Safety**: Configuration files are backed up to `~/flags.yaml.backup_YYYYMMDD_HHMMSS` before removal.

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

**MCP Connection Failed**
```bash
# Check server status
claude mcp list

# Re-register server
claude mcp remove superflag
claude mcp add superflag npx @superclaude-org/superflag@latest -s user
```

**Flags Not Working**
- Restart Claude Code after installation
- Verify `~/.claude/SUPERFLAG.md` exists
- Check `claude mcp list` shows ✓ Connected

**Version Conflicts**
- Ensure Python version is completely removed
- Use `npm list -g @superclaude-org/superflag` to verify installation

## License

MIT

---

**Need Help?** File issues at: [GitHub Repository](https://github.com/superclaude-org/superflag)