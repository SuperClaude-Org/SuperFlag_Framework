from setuptools import setup

# Best practice: Minimal redirect package following sklearn pattern
setup(
    name="context-engine-mcp",
    version="2.2.3",  # Minimal increment for deprecation notice
    description="Deprecated: This package has been renamed to 'superflag'",
    long_description="""# IMPORTANT: Package Renamed to superflag

This package has been renamed. Installing this package will automatically install `superflag` instead.

## What Changed?

- **Old name**: `context-engine-mcp`
- **New name**: `superflag`
- **All functionality remains the same**

## Migration Steps

### For New Users
```bash
pip install superflag
```

### For Existing Users
No action needed! This package now installs `superflag` automatically.

### Command Compatibility
All commands work with both names:
- `superflag install` (recommended)
- `context-engine install` (backward compatible)

## Why the Change?

We've simplified the package name to make it easier to remember and use.

## Support

For issues or questions, visit: https://github.com/SuperClaude-Org/context-engine-mcp

---

**Note**: This is a transitional package. In future versions, please use `pip install superflag` directly.
""",
    long_description_content_type="text/markdown",
    install_requires=[
        "superflag>=2.2.2",  # Automatically installs the new package
    ],
    python_requires=">=3.10",
    author="SuperClaude-Org",
    author_email="",
    url="https://github.com/SuperClaude-Org/context-engine-mcp",
    project_urls={
        "Documentation": "https://github.com/SuperClaude-Org/context-engine-mcp",
        "Source": "https://github.com/SuperClaude-Org/context-engine-mcp",
        "Tracker": "https://github.com/SuperClaude-Org/context-engine-mcp/issues",
    },
    classifiers=[
        "Development Status :: 7 - Inactive",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
    ],
    keywords="deprecated, renamed, superflag, context-engine, mcp",
)