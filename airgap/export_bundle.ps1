param (
    [string]$Platform = "linux/amd64"
)

$ErrorActionPreference = "Stop"

Write-Host "Building unified application image for platform $Platform..."
docker build --platform $Platform -t ulpf-app:latest -f Dockerfile.app .

Write-Host "Pulling dependency images for platform $Platform..."
docker pull --platform $Platform postgres:15-alpine
docker pull --platform $Platform redis:7-alpine
docker pull --platform $Platform opensearchproject/opensearch:2.11.0

Write-Host "Saving images to airgap/ulpf-airgap-bundle.tar..."
# Use docker save -o instead of pipe, as powershell corrupts binary streams through the pipeline
docker save -o "$PSScriptRoot/ulpf-airgap-bundle.tar" `
  ulpf-app:latest `
  postgres:15-alpine `
  redis:7-alpine `
  opensearchproject/opensearch:2.11.0

Write-Host "Generating SHA-256 manifest..."
$hash = Get-FileHash -Algorithm SHA256 -Path "$PSScriptRoot/ulpf-airgap-bundle.tar"
$hashString = "$($hash.Hash.ToLower())  ulpf-airgap-bundle.tar"
[IO.File]::WriteAllText("$PSScriptRoot/manifest.sha256", "$hashString`n")

Write-Host "Export complete! Transfer airgap/ulpf-airgap-bundle.tar and airgap/manifest.sha256 to the isolated network."
