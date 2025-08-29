# Continuous Integration (CI) Pipeline

This project includes a comprehensive GitHub Actions CI pipeline for maintaining code quality and ensuring functionality.

## 🚀 Features

### GitHub Actions Workflow (`.github/workflows/ci.yml`)

The CI pipeline runs automatically on:
- **Push** to `main` or `develop` branches
- **Pull requests** to `main` or `develop` branches

### Test Matrix

The pipeline tests across multiple Python versions:
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13

### Pipeline Steps

1. **Code Quality Checks**
   - **Linting**: Ruff for code style and error detection
   - **Formatting**: Ruff formatter for consistent code style
   - **Type Checking**: MyPy (currently disabled, can be enabled later)

2. **Testing**
   - **Unit Tests**: Comprehensive test suite with pytest
   - **Coverage**: Code coverage reporting with pytest-cov
   - **Coverage Upload**: Automatic upload to Codecov

3. **Installation Testing**
   - Tests installation scripts
   - Verifies package installation

4. **Security Auditing**
   - Runs pip-audit for vulnerability scanning
   - Generates security reports

## 🛠️ Local Development

### Quick Commands

```bash
# Run all CI checks locally
make ci

# Individual commands
make lint          # Run linting
make format        # Format code
make format-check  # Check formatting
make test          # Run tests
make test-cov      # Run tests with coverage
make security      # Run security audit
make clean         # Clean build artifacts
```

### Setup Development Environment

```bash
# Install dependencies
make install

# Install pre-commit hooks (optional)
make install-hooks

# Run pre-commit hooks on all files
make run-hooks
```

### Pre-commit Hooks

The project includes pre-commit configuration (`.pre-commit-config.yaml`) for:
- Trailing whitespace removal
- End-of-file fixing
- YAML validation
- Large file checks
- Merge conflict detection
- Ruff linting and formatting
- MyPy type checking

## 📊 Code Quality Standards

### Linting Rules (Ruff)

- **pycodestyle**: Enforces PEP 8 style guidelines
- **pyflakes**: Detects unused imports and variables
- **isort**: Sorts imports automatically
- **flake8-bugbear**: Catches common bugs
- **flake8-comprehensions**: Improves list/dict comprehensions
- **pyupgrade**: Modernizes Python syntax

### Coverage Requirements

- **Current Coverage**: 85%
- **Target**: Maintain or improve coverage
- **Reports**: HTML and XML coverage reports generated

## 🔒 Security

- **pip-audit**: Scans for known vulnerabilities in dependencies
- **Automated Reports**: Security scan results uploaded as artifacts
- **Non-blocking**: Security scans don't fail CI (logged for review)

## 📈 Performance

The CI pipeline is optimized for speed:
- **Parallel Jobs**: Tests run across multiple Python versions simultaneously
- **Caching**: UV package manager with caching enabled
- **Fast Tools**: Ruff for linting (much faster than traditional tools)
- **Efficient Testing**: Well-organized test suite with 109 tests running in ~0.5s

## 🎯 CI Status

### Current Status: ✅ All Checks Passing

- ✅ **109 tests passing**
- ✅ **4 tests appropriately skipped** (legacy tests replaced by domain-specific ones)
- ✅ **85% code coverage**
- ✅ **All linting checks passing**
- ✅ **Code formatting consistent**
- ✅ **No security vulnerabilities**

## 📝 Adding New Dependencies

When adding new dependencies:

1. Add to `pyproject.toml` under appropriate group (`dependencies` for runtime, `dev` for development)
2. Run `uv sync` to update lockfile
3. If adding type stubs, add to dev dependencies with `types-` prefix
4. Test locally with `make ci`

## 🚨 Troubleshooting

### Common Issues

1. **Formatting Failures**: Run `make format` to auto-fix
2. **Linting Errors**: Run `make lint` to see specific issues
3. **Test Failures**: Run `make test` locally to debug
4. **Coverage Drops**: Add tests for new code

### Getting Help

- Check the Makefile for available commands
- Review logs in GitHub Actions for detailed error messages
- Run `make ci` locally to reproduce CI environment
