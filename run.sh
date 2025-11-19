#!/bin/bash

# Augment Code Credits Monitor Launcher
# This script uses uv to run the application

set -e

echo "🚀 Starting Augment Code Credits Monitor..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed!"
    echo ""
    echo "Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Or visit: https://github.com/astral-sh/uv"
    exit 1
fi

# Run the application with uv
echo "✓ Using uv to run the application..."
uv run credits_monitor.py

