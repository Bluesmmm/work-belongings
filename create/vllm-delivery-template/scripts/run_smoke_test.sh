#!/bin/bash
# Run smoke test suite.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate venv
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "🧪 Running smoke test..."
python client/smoke_test.py

echo ""
echo "🧪 Running pytest suite..."
pytest tests/ -v
