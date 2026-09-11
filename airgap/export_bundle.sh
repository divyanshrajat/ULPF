#!/usr/bin/env bash
set -e

# Default platform to linux/amd64 to avoid 'exec format error' on x86 target if built on Apple Silicon
PLATFORM=${1:-linux/amd64}

echo "Building unified application image for platform ${PLATFORM}..."
docker build --platform ${PLATFORM} -t ulpf-app:latest -f Dockerfile.app .

echo "Pulling dependency images for platform ${PLATFORM}..."
docker pull --platform ${PLATFORM} postgres:15-alpine
docker pull --platform ${PLATFORM} redis:7-alpine
docker pull --platform ${PLATFORM} opensearchproject/opensearch:2.11.0

echo "Saving images to airgap/ulpf-airgap-bundle.tar..."
docker save -o airgap/ulpf-airgap-bundle.tar \
  ulpf-app:latest \
  postgres:15-alpine \
  redis:7-alpine \
  opensearchproject/opensearch:2.11.0

echo "Packaging models..."
mkdir -p airgap/models
cp models/*.gguf airgap/models/ 2>/dev/null || true

echo "Generating SHA-256 manifest..."
cd airgap
sha256sum ulpf-airgap-bundle.tar > manifest.sha256
if ls models/*.gguf 1> /dev/null 2>&1; then
  sha256sum models/*.gguf >> manifest.sha256
fi
cd ..

echo "Export complete! Transfer airgap/ulpf-airgap-bundle.tar and airgap/manifest.sha256 to the isolated network."
