# AuditAgent Windows PowerShell Bootstrap Script
Write-Host "=== Setting up AuditAgent Monorepo Environment ===" -ForegroundColor Cyan

# Install Python modules
Write-Host "--> Installing Analysis, Agent, and Security dependencies..." -ForegroundColor Yellow
pip install -e analysis/
pip install -e agent/
pip install -e security-tests/

# Install Node modules
Write-Host "--> Installing Dashboard and Contracts dependencies..." -ForegroundColor Yellow
cd dashboard; npm install; cd ..
cd contracts; npm install; cd ..

if (-not (Test-Path .env)) {
    Write-Host "--> Copying .env.example to .env..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

Write-Host "=== Setup Complete! Run '.\scripts\dev.ps1' to launch local dev stack. ===" -ForegroundColor Green
