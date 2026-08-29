# start_local.ps1
# This script starts the ULPF backend and frontend simultaneously for local development.

Write-Host "Starting ULPF Local Development Environment..." -ForegroundColor Cyan

# 1. Build frontend
Write-Host "Building Frontend UI..." -ForegroundColor Yellow
Set-Location -Path frontend
npm install
npm run build
Set-Location -Path ..

# 2. Start backend API which now serves the frontend
Write-Host "Starting Backend API (Serves Frontend on port 8000)..." -ForegroundColor Yellow
Set-Location -Path backend
if (-Not (Test-Path -Path venv)) { python -m venv venv }
.\venv\Scripts\activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload

