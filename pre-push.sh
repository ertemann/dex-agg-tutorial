#!/bin/sh

# Pre-push hook to run formatting and linting
echo "Running pre-push checks and auto-formatting..."

# Run black (format, don't just check)
echo "📝 Auto-formatting code with black..."
poetry run black . || {
    echo "Black formatting failed."
    exit 1
}

# Run ruff (fix auto-fixable issues)
echo "🔧 Auto-fixing ruff issues..."
poetry run ruff check . --fix || {
    echo "Ruff check failed after auto-fixes. Manual intervention required."
    exit 1
}

echo "All checks passed! Proceeding with push..."