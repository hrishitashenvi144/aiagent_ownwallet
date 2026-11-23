# AuditAgent Windows PowerShell Local Development Runner
Write-Host "=== Launching AuditAgent Local Development Stack ===" -ForegroundColor Cyan

# Check for anvil
if (Get-Command anvil -ErrorAction SilentlyContinue) {
    Write-Host "--> Starting Anvil node on 127.0.0.1:8545..." -ForegroundColor Yellow
    Start-Process -NoNewWindow anvil -ArgumentList "--port 8545"
} else {
    Write-Host "--> Notice: 'anvil' not detected in PATH. Running services in mock web3 / testnet mode." -ForegroundColor DarkYellow
}

Write-Host "--> Launching FastAPI Agent Core on http://localhost:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONPATH='agent;analysis'; uvicorn agent.main:app --host 0.0.0.0 --port 8000 --reload"

Write-Host "--> Launching Next.js Dashboard on http://localhost:3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd dashboard; npm run dev"

Write-Host "=== Stack Launched! Open http://localhost:3000 to interact. ===" -ForegroundColor Green
