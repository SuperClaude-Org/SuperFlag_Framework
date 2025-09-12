Changelog

## 1.0.7 (2025-09-13)

- Fix installer hang on Windows by avoiding spawning the MCP server during checks.
- Replace version/availability checks with import-level (`importlib.util.find_spec`) and PATH checks (`shutil.which`).
- Remove self-reinstall step (`pip install -e ...`) from installer to prevent long waits and file-lock issues.
- Update embedded example configs to reference version 1.0.7.
- Update flags.yaml metadata version to 1.0.7.

Notes
- No breaking changes; requires Python >= 3.10.
- TestPyPI and PyPI packages built with Hatchling; `twine check` passed.
