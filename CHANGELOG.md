# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.5] - 2026-04-16

### Added
- `superflag update` subcommand — syncs `~/.superflag/flags.yaml` with the bundled version
  - Automatically backs up the existing file to `~/.superflag/flags.yaml.<ISO-timestamp>.bak` before overwriting
  - Prints a clear diff-style report and reminds the user to restart their MCP client
  - Works as both a first-time setup and an ongoing update path

### Fixed
- Users on pre-v4.0 flag definitions (e.g. missing `--skill`, `--team`, `--integrity`, `--evolve`)
  can now pull in the latest bundled flags without manually deleting or editing their local YAML.

## [3.1.4] - Previous

- Sync `version.ts` to 3.1.4 for correct build output.
- README updated to reflect the current 21 flags and project state.

## [3.1.3] - Previous

- Extract `SUPERFLAG.md` content from hardcoded string to file read.
- Resolve all 16 security vulnerabilities via `npm audit fix`.
- Merge `flags.yaml` v4.0 3-Layer architecture and `SUPERFLAG.md` from dev branch.

## [3.1.2] - Previous

- Add automatic MCP server registration for all platforms.
- Update `--save` directive with AI-ready SuperFlag handoff template.

## [3.1.0] - Previous

- Complete TypeScript migration and enhanced message handling.
- Platform support improvements across Claude Code, Gemini CLI, and Continue.
