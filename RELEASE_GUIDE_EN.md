# Release and CI/CD

This is the exact behavior implemented in the repository today.

Version vs Tag (concise)
- Version = truth in code: `src/context_engine_mcp/__version__.py` (PEP 440). Defines the package’s real version on PyPI. Same version cannot be uploaded twice.
- Tag = trigger in Git: pushing a tag `v<version>` starts the publish pipeline for that exact version.
- They must match exactly: tag `v1.0.8` with version `1.0.8`; tag `v1.0.8rc1` with version `1.0.8rc1`.
- Routing: pre‑release markers (rc/a/b/dev) → TestPyPI; otherwise → PyPI.

What happens on a tag push
- A tag named `v*` starts the release pipeline.
- CI runs first on that commit. Publish waits and continues only if CI succeeds.
- Publish builds distributions and uploads:
  - Tag with a PEP 440 pre‑release marker (`rc`, `a`, `b`, `dev`) → upload to TestPyPI.
  - Tag without a pre‑release marker → upload to PyPI.
- The tag must equal `v<__version__>` exactly. If not, publishing stops.

Version and tag rules
- Version lives in `src/context_engine_mcp/__version__.py`.
- Stable example: version `1.0.7` → tag `v1.0.7` → uploads to PyPI.
- Pre‑release example: version `1.0.8rc1` → tag `v1.0.8rc1` → uploads to TestPyPI.
- Each version can be published once. Change the version for any new build.

CI workflow (`.github/workflows/ci.yml`)
- Triggers: push (all branches and tags), pull_request.
- Matrix: OS = ubuntu/windows/macos; Python = `3.10` and `3.x`.
- Steps:
  - Build sdist+wheel (`python -m build`).
  - Validate metadata (`twine check`).
  - Install built wheel and run `pip check`.
  - Smoke test CLI via module; pipx smoke on Ubuntu.

Publish workflow (`.github/workflows/publish.yml`)
- Trigger: tag push `v*`.
- Requires CI success for the same commit (polling gate).
- Builds on latest Python `3.x` with pip cache and uploads dists.
- Uses OIDC (no passwords in workflow).

One‑time setup on PyPI/TestPyPI UI
- Project Settings → “Add a trusted publisher” → GitHub Actions.
- Owner: `hyunjae-labs`
- Repository: `context-engine-mcp`
- Workflow file name: `publish.yml`

How to release
- Pre‑release to TestPyPI:
  1) Set `__version__ = "1.0.8rc1"`
  2) Commit and push
  3) `git tag v1.0.8rc1 && git push origin v1.0.8rc1`
- Stable to PyPI:
  1) Set `__version__ = "1.0.8"`
  2) Commit and push
  3) `git tag v1.0.8 && git push origin v1.0.8`