#!/bin/bash
# One-click development startup script.
# This script starts the vLLM server and runs the smoke test.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🚀 Starting vLLM development environment..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Install with:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment with uv..."
    uv venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies with uv..."
uv pip install -e .

echo ""
echo "🔥 Starting vLLM server..."
echo "   Press Ctrl+C to stop"
echo ""

# Start server in background
python serving/launch.py &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to start..."
sleep 10

# Run smoke test
echo ""
echo "🧪 Running smoke test..."
python client/smoke_test.py

# Keep server running
echo ""
echo "✅ Server is running at http://localhost:8000"
echo "   Press Ctrl+C to stop"

wait $SERVER_PID
