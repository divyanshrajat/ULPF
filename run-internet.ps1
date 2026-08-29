#!/usr/bin/env pwsh
# run-internet.ps1 — Start ULPF in Internet mode (connected deployment)
# Usage: .\run-internet.ps1

$env:ULPF_MODE = "internet"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        ULPF — Internet Mode                  ║" -ForegroundColor Cyan
Write-Host "║  Building and starting all services...       ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

docker compose up --build -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker Compose failed to start." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Waiting for services to be ready..."
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          ULPF READY                          ║" -ForegroundColor Green
Write-Host "║                                              ║" -ForegroundColor Green
Write-Host "║  URL:    http://localhost:8000               ║" -ForegroundColor Green
Write-Host "║  MODE:   INTERNET                            ║" -ForegroundColor Green
Write-Host "║  Status: READY                               ║" -ForegroundColor Green
Write-Host "║                                              ║" -ForegroundColor Green
Write-Host "║  API:    http://localhost:8000/api/v1        ║" -ForegroundColor Green
Write-Host "║  Docs:   http://localhost:8000/docs          ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
