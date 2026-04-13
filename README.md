# SuperFlag

![Claude Code](https://img.shields.io/badge/Claude%20Code-supported-F37435)
![NPM](https://img.shields.io/badge/NPM-v3.1.4-CB3837)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6)

> **Note**: This project was inspired by the pioneering work in [SuperClaude Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) and [SuperGemini Framework](https://github.com/SuperClaude-Org/SuperGemini_Framework). Special thanks to [SuperClaude-Org](https://github.com/SuperClaude-Org) team members [@NomenAK](https://github.com/NomenAK) and [@mithun50](https://github.com/mithun50) whose work made this possible.

SuperFlag provides 21 contextual flags that guide AI assistant behavior through precise directives. It exposes an MCP stdio server for seamless integration with modern AI development tools.

## Quick Start

```bash
# Install globally
npm install -g @superclaude-org/superflag

# Interactive installation (choose platforms)
superflag install

# Direct installation for Claude Code
superflag install cc
```

Then use flags in your AI assistant:
- "Fix this bug --analyze --strict"
- "Refactor --auto" (auto-select optimal flags)
- "--save" (create handoff documentation)
- "Run with 3 agents --team-3"

## 21 Available Flags

### Analysis & Optimization
| Flag | Purpose |
|------|---------|
| `--analyze` | Multi-perspective evidence-based analysis with 3+ independent perspectives |
| `--performance` | Measure-first optimization with baseline metrics and ROI calculation |
| `--refactor` | Safe atomic refactoring with continuous test verification |
| `--strict` | Zero-error transparent execution with verify-before-claim |
| `--lean` | Minimal resource-efficient implementation eliminating waste |

### Discovery & Documentation
| Flag | Purpose |
|------|---------|
| `--discover` | Research-first solution selection with 3+ alternatives comparison |
| `--explain` | Progressive domain-expert disclosure from overview to details |
| `--save` | Document development context for seamless continuation |
| `--load` | Load and verify handoff context against git reality |

### Workflow Management
| Flag | Purpose |
|------|---------|
| `--team` | Multi-agent coordination with optional count (`--team-N`) |
| `--skill` | Context-aware skill invocation — auto-selects appropriate skill |
| `--todo` | Scope-locked task tracking with real-time progress |
| `--seq` | Dependency-ordered sequential execution with checkpoints |
| `--collab` | Evidence-anchored peer collaboration with quantitative validation |

### Output Control
| Flag | Purpose |
|------|---------|
| `--concise` | Precise professional content prioritizing accuracy over brevity |
| `--git` | Anonymous atomic commits with ASCII-only WHY-focused messages |
| `--readonly` | Analysis-only mode with absolute no-modification guarantee |

### Execution Discipline
| Flag | Purpose |
|------|---------|
| `--integrity` | Verification-before-claim with evidence for every assertion |
| `--evolve` | Monotonic forward improvement with regression prevention |

### Meta Control
| Flag | Purpose |
|------|---------|
| `--reset` | Clear session and force fresh directives |
| `--auto` | Grant autonomous flag selection authority |

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
- `~/.claude/CLAUDE.md` - References @SUPERFLAG.md
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
- `~/.gemini/GEMINI.md` - References @SUPERFLAG.md
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
"--analyze --strict"       # Thorough analysis with zero-error enforcement
"--save --explain"         # Create documentation with detailed explanations
"--reset --todo"           # Reset session and start task tracking
"--team-3 --todo"          # Multi-agent work with 3 agents + task tracking

# Parametric flags
"--team-5"                 # Spawn 5 role-specialized agents
"--team"                   # Auto-determine team size from task complexity
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
├── SUPERFLAG.md                 # Flag instructions
└── hooks/
    └── superflag.py             # Flag detection hook
```

### Gemini CLI
```
~/.gemini/
├── GEMINI.md                    # References @SUPERFLAG.md
├── SUPERFLAG.md                 # Flag instructions
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

## Development

### Local Development
```bash
# Clone repository
git clone https://github.com/SuperClaude-Org/SuperFlag_Framework.git
cd SuperFlag_Framework

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

### Project Structure
- `flags.yaml` - All 21 flag definitions and directives (3-Layer architecture)
- `SUPERFLAG.md` - Flag instructions installed to user config directories
- `src/server.ts` - MCP stdio server
- `src/install.ts` - Interactive installer/uninstaller
- `src/directives.ts` - Flag parsing from flags.yaml

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
- Configuration files are backed up before removal
- Interactive confirmation for each platform
- Selective removal - keep other platforms intact

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

## License

MIT

---

**Need Help?** File issues at: [GitHub Repository](https://github.com/SuperClaude-Org/SuperFlag_Framework)
