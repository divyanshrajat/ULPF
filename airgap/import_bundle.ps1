$ErrorActionPreference = "Stop"

$ScriptDir = $PSScriptRoot
Set-Location $ScriptDir

Write-Host "Verifying SHA-256 manifest..."
$manifest = Get-Content manifest.sha256
$expectedHash = ($manifest -split " ")[0].Trim()
$actualHash = (Get-FileHash -Algorithm SHA256 -Path ulpf-airgap-bundle.tar).Hash.ToLower()

if ($expectedHash -ne $actualHash) {
    Write-Host "ERROR: Manifest verification failed. Archive may be corrupted." -ForegroundColor Red
    exit 1
}

Write-Host "Loading docker images..."
docker load -i ulpf-airgap-bundle.tar

Write-Host "Checking for expected images..."
$ExpectedImages = @(
  "ulpf-backend:airgap",
  "ulpf-frontend:airgap",
  "postgres:15-alpine",
  "redis:7-alpine",
  "opensearchproject/opensearch:2.11.0"
)

foreach ($img in $ExpectedImages) {
    $inspect = docker image inspect $img 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Image $img not found after load." -ForegroundColor Red
        exit 1
    }
}

Write-Host "Starting ULPF in air-gap mode..."
Set-Location ..
docker compose -f docker-compose.airgap.yml up -d

Write-Host "Waiting for services to become healthy..."
$MaxTries = 30
$Tries = 0

while ($Tries -lt $MaxTries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.Content -match '"status":"HEALTHY"') {
            Write-Host "ULPF is up and healthy!" -ForegroundColor Green
            Write-Host "UI available at http://localhost:5173" -ForegroundColor Cyan
            exit 0
        }
    } catch {
        # Ignore connection errors while waiting
    }
    
    Start-Sleep -Seconds 2
    $Tries++
}

Write-Host "ERROR: Services failed to become healthy within 60 seconds." -ForegroundColor Red
Write-Host "Here are the backend logs:"
docker compose -f docker-compose.airgap.yml logs backend
exit 1
