#!/usr/bin/env bash
set -e

echo "=== Setting up AuditAgent Monorepo Environment ==="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed. Aborting." >&2; exit 1; }

# Install Python dependencies
echo "--> Installing Analysis Engine dependencies..."
pip install -e analysis/

echo "--> Installing Agent Core dependencies..."
pip install -e agent/

echo "--> Installing Security Test suite dependencies..."
pip install -e security-tests/

# Install Node dependencies
echo "--> Installing Dashboard dependencies..."
cd dashboard && npm install && cd ..

echo "--> Installing Contracts package..."
cd contracts && npm install && cd ..

# Copy .env.example if .env does not exist
if [ ! -f .env ]; then
    echo "--> Creating .env from .env.example..."
    cp .env.example .env
fi

echo "=== Setup Complete! Run 'bash scripts/dev.sh' to launch local dev stack. ==="
