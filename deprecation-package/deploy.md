# Deployment Instructions for Deprecation Package

After the main `superflag` package is successfully deployed to PyPI, deploy the deprecation package:

## Steps:

1. Wait for `superflag 2.2.2` to be available on PyPI
   ```bash
   pip install superflag==2.2.2  # Verify it's available
   ```

2. Deploy the deprecation package:
   ```bash
   cd deprecation-package
   python -m build
   python -m twine upload dist/*
   ```

3. Test the migration:
   ```bash
   # In a clean environment
   pip install context-engine-mcp
   # Should automatically install superflag
   ```

## What This Does:

- Users who run `pip install context-engine-mcp` will get:
  - The deprecation package (2.2.3)
  - Automatic installation of `superflag>=2.2.2`
  - Clear migration instructions in package description

- Existing users who upgrade will:
  - See the deprecation notice
  - Get superflag installed automatically
  - Have all commands working as before

## Verification:

```bash
pip show context-engine-mcp  # Should show version 2.2.3
pip show superflag           # Should be installed automatically
superflag --version          # Should work
context-engine --version     # Should also work (backward compat)
```