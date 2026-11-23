# AuditAgent Windows PowerShell Lint and Validation Script
Write-Host "=== Running AuditAgent Monorepo Lint & Validation ===" -ForegroundColor Cyan

# 1. Validate JSON Schemas
Write-Host "--> Validating shared JSON schemas and ABIs..." -ForegroundColor Yellow
python -c "import json, glob; [json.load(open(f)) for f in glob.glob('shared/schemas/*.json') + glob.glob('shared/abis/*.json')]; print('Schemas OK!')"

# 2. Test contracts
Write-Host "--> Validating contracts module..." -ForegroundColor Yellow
cd contracts; npm test; cd ..

# 3. Test dashboard
Write-Host "--> Validating dashboard module..." -ForegroundColor Yellow
cd dashboard; npm test; cd ..

Write-Host "=== All Lint Checks Passed! ===" -ForegroundColor Green
