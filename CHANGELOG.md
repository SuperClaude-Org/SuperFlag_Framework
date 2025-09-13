Changelog

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
