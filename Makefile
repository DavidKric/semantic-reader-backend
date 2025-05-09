.DEFAULT_GOAL := help

PYTHON_VERSION := 3.11

.PHONY: .uv
.uv: ## Ensure uv is installed
	@command -v uv >/dev/null 2>&1 || (echo "Please install uv: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)

.PHONY: setup
setup: .uv ## Setup the project environment
	./scripts/setup_dev.sh

.PHONY: dependencies
dependencies: .uv ## Install dependencies
	uv pip install -e .

.PHONY: dev-dependencies
dev-dependencies: .uv ## Install development dependencies
	uv pip install -e ".[dev]"

.PHONY: test
test: .uv ## Run tests
	./scripts/run_tests.sh --all

.PHONY: test-e2e
test-e2e: .uv ## Run end-to-end tests only
	./scripts/run_tests.sh --e2e

.PHONY: test-unit
test-unit: .uv ## Run unit tests only
	./scripts/run_tests.sh --unit

.PHONY: lint
lint: .uv ## Run linting with ruff
	./scripts/quality_check.sh --lint

.PHONY: format
format: .uv ## Format code with ruff
	./scripts/quality_check.sh --format --fix

.PHONY: typecheck
typecheck: .uv ## Run type checking with mypy
	./scripts/quality_check.sh --typecheck

.PHONY: quality-check
quality-check: .uv ## Run all code quality checks
	./scripts/quality_check.sh --all

.PHONY: test-coverage
test-coverage: .uv ## Run tests with coverage
	./scripts/run_tests.sh --all --coverage

.PHONY: generate-report
generate-report: .uv ## Generate test HTML report
	./scripts/run_tests.sh --all --html

.PHONY: check
check: quality-check test ## Run linting and tests

.PHONY: clean
clean: ## Clean up build artifacts and cache
	rm -rf .uv/ uv.lock .pytest_cache/ .coverage htmlcov/ report.html
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

.PHONY: help
help: ## Display this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

.PHONY: install dev run test lint format clean help migrate upgrade

PYTHON = python
UV = uv
APP = app

help:
	@echo "Available commands:"
	@echo "  install         Install production dependencies"
	@echo "  dev             Install development dependencies"
	@echo "  run             Run the application"
	@echo "  test            Run tests"
	@echo "  lint            Run linting checks"
	@echo "  format          Format code"
	@echo "  clean           Clean build artifacts"
	@echo "  migrate         Generate a new database migration"
	@echo "  upgrade         Upgrade database to latest migration"
	@echo "  help            Show this help message"

install:
	$(UV) pip install .

dev:
	$(UV) pip install -e ".[dev]"

run:
	$(PYTHON) -m $(APP).main

test:
	pytest -xvs tests/

lint:
	ruff check $(APP)/ tests/
	mypy $(APP)/

format:
	black $(APP)/ tests/
	ruff check --fix $(APP)/ tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Database migrations
migrate:
	alembic revision --autogenerate -m "$(message)"

upgrade:
	alembic upgrade head 