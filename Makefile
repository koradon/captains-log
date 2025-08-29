.PHONY: help install test lint format type-check clean coverage security

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	uv sync --dev

test: ## Run tests
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	uv run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v

lint: ## Run linting
	uv run ruff check src/ tests/

format: ## Format code
	uv run ruff format src/ tests/

format-check: ## Check code formatting
	uv run ruff format --check src/ tests/

type-check: ## Run type checking
	uv run mypy src/ --ignore-missing-imports

security: ## Run security audit
	uv run pip-audit

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

ci: lint format-check test ## Run all CI checks locally

install-hooks: ## Install pre-commit hooks
	uv run pre-commit install

run-hooks: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files
