#!/usr/bin/env bash
set -e

echo "=== Running AuditAgent Monorepo Lint & Validation ==="

# 1. Validate JSON Schemas and ABIs
echo "--> Validating shared JSON schemas and ABIs..."
python -c "import json, glob; [json.load(open(f)) for f in glob.glob('shared/schemas/*.json') + glob.glob('shared/abis/*.json')]; print('Schemas OK!')"

# 2. Lint Python if ruff is installed
if command -v ruff >/dev/null 2>&1; then
    echo "--> Running Ruff linter on Python code..."
    ruff check agent/ analysis/ security-tests/ benchmarks/
else
    echo "--> Ruff not installed. Skipping Python linter."
fi

# 3. Test contracts
echo "--> Validating contracts module..."
cd contracts && npm test && cd ..

# 4. Test dashboard
echo "--> Validating dashboard module..."
cd dashboard && npm test && cd ..

echo "=== All Lint Checks Passed! ==="
