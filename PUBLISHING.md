# Publishing Captain's Log to PyPI

This guide explains how to publish Captain's Log to PyPI (Python Package Index).

## Prerequisites

1. **PyPI Account**: Create accounts on:
   - [PyPI](https://pypi.org/) (production)
   - [TestPyPI](https://test.pypi.org/) (for testing)

2. **API Token**: Generate an API token:
   - Go to PyPI → Account Settings → API tokens
   - Create a token for "Entire account" or specific project
   - Save it securely (you'll only see it once)

3. **UV installed**: You already have this for building

## Version Management with Git Tags

Captain's Log uses `hatch-vcs` for dynamic versioning based on Git tags.

### Creating a Release

```bash
# 1. Make sure all changes are committed
git status

# 2. Tag the release (use semantic versioning)
git tag v0.2.0 -m "Release version 0.2.0 with PyPI support"

# 3. Push the tag to GitHub
git push origin v0.2.0

# 4. Build the package
uv build

# The built package will have version 0.2.0 (from the tag)
```

### Version Examples

```bash
# On tag v0.2.0
uv build → captains_log-0.2.0-py3-none-any.whl

# 3 commits after v0.2.0
uv build → captains_log-0.2.1.dev3+g1234567-py3-none-any.whl

# On a branch
uv build → captains_log-0.2.1.dev0+g1234567.d20251031-py3-none-any.whl
```

**Only publish tagged releases to PyPI!** Development versions are for testing only.

## Publishing Workflow

### Step 1: Test Locally

```bash
# Build the package
uv build

# Test installation locally
uv pip install dist/captains_log-*.whl

# Test the commands
captains-log --version
captains-log setup
btw --version
wtf --version
```

### Step 2: Publish to TestPyPI (Optional but Recommended)

```bash
# Install twine if you don't have it
uv pip install twine

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ captainslog

# Verify it works
captains-log --version
```

### Step 3: Publish to PyPI (Production)

```bash
# Clean and rebuild
rm -rf dist/
uv build

# Upload to PyPI
twine upload dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: pypi-XXXXX... (your API token)
```

### Step 4: Verify Installation

```bash
# In a fresh environment
pip install captainslog

# Test it
captains-log --version
captains-log setup
```

## Automated Publishing with GitHub Actions

You can automate publishing when you create a GitHub release:

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Needed for hatch-vcs to work

      - name: Install uv
        uses: astral-sh/setup-uv@v1

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

Then add your PyPI API token as a GitHub secret:
- Go to GitHub repo → Settings → Secrets and variables → Actions
- Add secret: `PYPI_API_TOKEN`

## Release Checklist

Before publishing a new version:

- [ ] All tests passing: `uv run pytest`
- [ ] Update CHANGELOG (if you have one)
- [ ] Commit all changes
- [ ] Create and push git tag: `git tag v0.x.0 && git push origin v0.x.0`
- [ ] Build package: `uv build`
- [ ] Test locally: `uv pip install dist/*.whl`
- [ ] Test setup command: `captains-log setup`
- [ ] Upload to TestPyPI (optional): `twine upload --repository testpypi dist/*`
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Create GitHub release (if using GitHub Actions)
- [ ] Test installation: `pip install captainslog`
- [ ] Announce the release!

## Version Bumping Strategy

Use semantic versioning (MAJOR.MINOR.PATCH):

- **PATCH** (0.1.0 → 0.1.1): Bug fixes, minor changes
  ```bash
  git tag v0.1.1 -m "Bug fixes"
  ```

- **MINOR** (0.1.0 → 0.2.0): New features, backwards compatible
  ```bash
  git tag v0.2.0 -m "Add new features"
  ```

- **MAJOR** (0.1.0 → 1.0.0): Breaking changes, major releases
  ```bash
  git tag v1.0.0 -m "First stable release"
  ```

## Troubleshooting

### Package already exists on PyPI

You can't overwrite published versions. You must bump the version:
```bash
# Create a new tag
git tag v0.2.1 -m "Fixed version"
uv build
twine upload dist/*
```

### Version showing as dev version

Make sure you're on a tagged commit:
```bash
# Check current tag
git describe --tags

# Create tag if needed
git tag v0.2.0
```

### commit-msg hook not included in package

Check that it's listed in `pyproject.toml`:
```toml
[tool.hatch.build.targets.sdist]
include = [
    "src/",
    "commit-msg",
    "README.md",
    "LICENSE",
]
```

## Current Configuration

Your `pyproject.toml` is already configured with:
- ✅ Build system: `hatchling` + `hatch-vcs`
- ✅ Dynamic versioning from Git tags
- ✅ Console scripts: `btw`, `wtf`, `captains-log`
- ✅ Package includes: source, hooks, README, LICENSE
- ✅ Version file: `src/_version.py` (auto-generated)

You're ready to publish! Just create a git tag and run `uv build`.
