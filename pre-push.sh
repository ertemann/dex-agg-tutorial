#!/bin/sh

# Pre-push hook to run linting and type checking
echo "Running pre-push checks..."

# Run black
echo "📝 Checking code formatting with black..."
poetry run black --check . || {
    echo "Black formatting check failed. Run 'poetry run black .' to fix."
    exit 1
}

# Run ruff
echo "🔍 Running ruff linter..."
poetry run ruff check . || {
    echo "Ruff check failed. Run 'poetry run ruff check .' to see issues."
    exit 1
}

echo "All checks passed! Proceeding with push..."