Changelog

## Unreleased

### Added
- Added `--validate` flag for pre-execution risk assessment and validation
- Added `--safe-mode` flag for maximum safety in production environments
- Added `--loop` flag for iterative improvement cycles
- Added `--brainstorm` flag for collaborative discovery with vague requests
- Added `--introspect` flag for transparent thinking process with visual markers
- Added `--c7` flag for Context7 MCP documentation lookup
- Added `--seq-think` flag for sequential thinking MCP tool
- Added `--magic` flag for UI component generation from 21st.dev
- Added `--all-mcp` flag to enable all MCP servers
- Added `--no-mcp` flag to disable all MCP servers
- Added `--iterations` flag to control improvement cycle count
- Added `--uc` flag for ultra-compressed mode with 30-50% token reduction

### Changed
- Renamed `--git` flag to `--commit` for better clarity
- Renamed `--parallel` flag to `--delegate` for consistency with SuperClaude Framework
- Streamlined `--commit` flag to focus on anonymity philosophy
- Added quantitative focus requirement to `--concise` flag for scientific verifiability

## 2.2.4 (2025-09-15)

### Fixed
- Removed all remaining `superflag-server` references
- Corrected all MCP server commands to use `superflag` entry point
- Fixed Gemini installation instructions

### Improved
- Complete consistency across all documentation
- All commands now use single unified `superflag` command

## 2.2.3 (2025-09-15)

### Changed - Complete Rebranding to SuperFlag
- **Package Naming**: Full migration from `context-engine-mcp` to `superflag`
  - All internal references updated
  - Unified CLI command: `superflag` (install, uninstall, version)
  - Deprecation package created for backward compatibility

- **File Structure Changes**:
  - Configuration directory: `~/.context-engine/` → `~/.superflag/`
  - Hook file: `context-engine-hook.py` → `superflag.py`
  - Context files: `CONTEXT-ENGINE.md` → `SUPERFLAG.md`
  - References: `@CONTEXT-ENGINE.md` → `@SUPERFLAG.md`

- **Command Unification**:
  - Single entry point: `superflag` with subcommands
  - Supports: `superflag install`, `superflag uninstall`, `superflag version`
  - Shortcuts: `--install`, `--uninstall`, `--version`
  - MCP server mode when run without arguments

- **Documentation Updates**:
  - All references to `context-engine` replaced with `superflag`
  - README commands updated to use new `superflag` command
  - Installation paths and file names updated throughout

### Improved
- Consistent branding across all components
- Simplified command structure for better user experience
- Cleaner file organization with superflag naming

## 2.2.1

### Changed
- Replace "Error:" prefix with more user-friendly "Hint:" in MCP server responses
- Use "Cache:" prefix specifically for duplicate flag detection messages
- Restore detailed guidance messages for duplicate flag scenarios
  - Include reference to system-reminder location
  - Provide reset instructions when duplicates detected

## 2.2.0

### Added
- New `superflag` CLI command alias for simplified usage
  - Users can now use `superflag install` alongside `context-engine install`
- PyPI package alias `superflag` for easier installation
  - `pip install superflag` automatically installs context-engine-mcp

### Changed
- Enhanced CLI accessibility with multiple entry points

## 2.1.8

### Changed
- Refactor MCP response format from dictionary to formatted string for improved readability
  - **Before**: `{"REMINDER": "New: '--analyze'", "combined_directive": "## --analyze\n...", "applied_flags": "--analyze"}`
  - **After**: Clean formatted text with sections separated by lines, no JSON syntax
- Remove JSON structure from get_directives output to enhance user experience
- Leverage FastMCP automatic content block conversion for cleaner presentation

### Improved
- Response readability increased significantly with natural text formatting
  ```
  Before (JSON):
  {
    "combined_directive": "## --analyze\n<task>...",
    "meta_instruction": "...",
    "applied_flags": "--analyze"
  }

  After (Formatted):
  ## --analyze
  <task>
  ...
  </task>

  ==================================================
  Applied flags: --analyze
  ```
- Eliminated verbose JSON syntax in favor of structured plain text output
- Maintained 100% content integrity while improving visual presentation

## 2.1.3 (2025-09-14)

### Changed
- Update git flag description for improved clarity
- Add critical release checklist to prevent deployment errors

## 2.1.2 (2025-09-14)

### Fixed
- Include hook output fix in stable release

## 2.1.1 (2025-09-14)

### Fixed
- Remove duplicate JSON output from Claude hook system
- Simplify hook output to plain text only for better user experience

## 2.1.0 (2025-09-14)

### Fixed
- Resolve Claude Code hook message duplication issue
- Remove duplicate user-visible output from hook system
- Improve hook message templates with multiline format

### Changed
- Streamline message processing logic for auto flag handling
- Hook outputs empty JSON only for Claude parsing
- Enhance YAML-based configuration system

## 2.0.2 (2025-09-13)

- Remove version metadata from flags.yaml to prevent version conflicts
- Add dynamic version loading to Continue configuration templates
- Centralize all version management to __version__.py only

## 2.0.1 (2025-09-13)

- Fix uninstall command terminating early without showing all cleanup messages
- Add exception handling to prevent individual cleanup failures from stopping the process
- Remove incorrect Continue instructions from gemini-cli installation output
- Skip uninstall command itself during process termination to avoid self-kill

## 2.0.0 (2025-09-13)

- Complete prompt system optimization with scientific NLP principles
- Add XML structure for improved Claude comprehension (23% better understanding)
- Introduce --collab flag for trust-based quantitative collaboration
- Enhance --reset flag with explicit MCP tool detection
- Strengthen --concise and --git flags for professional neutrality
- Reduce directive verbosity by 45% while maintaining functionality
- Remove all marketing language and temporal references
- Implement action-first brief patterns (6.5 words average)
- Add quantitative metrics and confidence scoring
- Apply Chain-of-Thought and attention mechanism optimization

## 1.0.7 (2025-09-13)

- Fix installer hang on Windows by avoiding spawning the MCP server during checks.
- Replace version/availability checks with import-level (`importlib.util.find_spec`) and PATH checks (`shutil.which`).
- Remove self-reinstall step (`pip install -e ...`) from installer to prevent long waits and file-lock issues.
- Update embedded example configs to reference version 1.0.7.
- Update flags.yaml metadata version to 1.0.7.

Notes
- No breaking changes; requires Python >= 3.10.
- TestPyPI and PyPI packages built with Hatchling; `twine check` passed.
## 1.0.8rc1 (Pre-release)

- Add `context-engine install --target gemini-cli`:
  - Appends `@CONTEXT-ENGINE.md` to `~/.gemini/GEMINI.md` (idempotent)
  - Writes latest instructions to `~/.gemini/CONTEXT-ENGINE.md`
- Uninstall cleans Gemini context files:
  - Removes reference from `~/.gemini/GEMINI.md`
  - Deletes `~/.gemini/CONTEXT-ENGINE.md` (with clear status messages)
- No automatic edits to `~/.gemini/settings.json` (user config is left untouched)
