#!/usr/bin/env pwsh
# run-airgap.ps1 — Start ULPF in Air-Gapped mode (offline deployment)
# Usage: .\run-airgap.ps1
#
# Prerequisites:
#   - Docker images must already be built (use run-internet.ps1 first on a connected machine)
#   - Local model must be pre-downloaded and ULPF_MODEL_PATH set to its directory
#   - No internet connection required at runtime

$env:ULPF_MODE = "airgap"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║        ULPF — Air-Gapped Mode                ║" -ForegroundColor Yellow
Write-Host "║  Starting with pre-built images...           ║" -ForegroundColor Yellow
Write-Host "║  No internet connection required.            ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Yellow
Write-Host ""

# In airgap mode: do NOT build (requires internet). Use pre-built images only.
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker Compose failed to start." -ForegroundColor Red
    Write-Host "Ensure images were built previously with: .\run-internet.ps1" -ForegroundColor Yellow
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
Write-Host "║  MODE:   AIR-GAPPED                          ║" -ForegroundColor Green
Write-Host "║  Status: READY                               ║" -ForegroundColor Green
Write-Host "║                                              ║" -ForegroundColor Green
Write-Host "║  Network policy: STRICT OFFLINE              ║" -ForegroundColor Green
Write-Host "║  All processing is local.                    ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Verify air-gap status: http://localhost:8000/api/v1/system/airgap" -ForegroundColor Cyan
Write-Host ""
