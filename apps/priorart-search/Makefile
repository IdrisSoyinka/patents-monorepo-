# Makefile for Patent Search Agent

.PHONY: install test lint format clean run help

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies using Poetry"
	@echo "  test       - Run all tests"
	@echo "  lint       - Run linting checks"
	@echo "  format     - Format code using Black"
	@echo "  clean      - Clean up temporary files"
	@echo "  run        - Run the example workflow"
	@echo "  setup      - Initial project setup"

# Install dependencies
install:
	poetry install

# Run tests
test:
	poetry run pytest tests/ -v

# Run linting
lint:
	poetry run flake8 src/
	poetry run mypy src/

# Format code
format:
	poetry run black src/ tests/

# Clean temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Run example workflow
run:
	poetry run python -m src.patent_search_agent.graph

# Initial setup
setup: install
	@echo "Creating .env file from .env.example..."
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "Setup complete! Please configure your API keys in .env file."
	@echo ""
	@echo "Required API keys:"
	@echo "  - ANTHROPIC_API_KEY or OPENAI_API_KEY (for LLM)"
	@echo "  - TAVILY_API_KEY (for web search)"
	@echo "  - GOOGLE_API_KEY and GOOGLE_CSE_ID (for patent search)"
	@echo "  - IPCCAT_API_URL (for IPC classification)"

# Development server (if using LangGraph Studio)
studio:
	@echo "Open this project in LangGraph Studio:"
	@echo "1. Install LangGraph Studio: https://github.com/langchain-ai/langgraph-studio"
	@echo "2. Open this directory in LangGraph Studio"
	@echo "3. Configure API keys in the Studio UI"

# Run specific node tests
test-nodes:
	poetry run pytest tests/test_nodes/ -v

test-tools:
	poetry run pytest tests/test_tools/ -v

# Install pre-commit hooks
pre-commit:
	poetry run pre-commit install

# Update dependencies
update:
	poetry update

# Build documentation (if using Sphinx)
docs:
	@echo "Documentation build not configured yet"

# Package for distribution
package:
	poetry build

# Run integration tests
test-integration:
	poetry run pytest tests/integration/ -v

# Security scan
security:
	poetry run safety check

# Check for outdated dependencies
check-deps:
	poetry show --outdated
