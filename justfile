# Justfile for Captain's Log development

# Default recipe to show help
default:
    @just --list

# Install dependencies
install:
    uv sync

# Install test dependencies
install-test:
    uv sync --group test

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=src --cov-report=html

# Run tests with verbose output
test-verbose:
    uv run pytest -v

# Clean up generated files
clean:
    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -rf .coverage
    find . -type d -name __pycache__ -delete
    find . -type f -name "*.pyc" -delete

# Run a specific test
test-file file:
    uv run pytest {{file}} -v

# Run tests matching a pattern
test-pattern pattern:
    uv run pytest -k "{{pattern}}" -v
