.PHONY: help install test pre-commit check-all

help: ## Show help for commands
	@echo "🔍 Displaying help:"; grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with poetry
	@echo "📦 Installing dependencies..."; poetry install

test: ## Run tests
	@echo "🧪 Running tests..."; poetry run pytest tests

pre-commit: ## Install pre-commit hooks
	@echo "🔗 Installing pre-commit hooks..."; pre-commit install

check-all: ## Run all code checks
	@echo "🔍 Running all checks..."; \
	poetry run ruff format aiotrade && \
	poetry run ruff check aiotrade --fix && \
	poetry run mypy aiotrade
