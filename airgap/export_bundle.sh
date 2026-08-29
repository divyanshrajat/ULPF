#!/usr/bin/env bash
set -e

# Default platform to linux/amd64 to avoid 'exec format error' on x86 target if built on Apple Silicon
PLATFORM=${1:-linux/amd64}

echo "Building backend image for platform ${PLATFORM}..."
docker build --platform ${PLATFORM} -t ulpf-backend:airgap -f backend/Dockerfile.airgap backend/

echo "Extracting requirements.lock.txt..."
docker run --rm ulpf-backend:airgap pip freeze > airgap/requirements.lock.txt

echo "Building frontend image for platform ${PLATFORM}..."
docker build --platform ${PLATFORM} -t ulpf-frontend:airgap frontend/

echo "Pulling dependency images for platform ${PLATFORM}..."
docker pull --platform ${PLATFORM} postgres:15-alpine
docker pull --platform ${PLATFORM} redis:7-alpine
docker pull --platform ${PLATFORM} opensearchproject/opensearch:2.11.0

echo "Saving images to airgap/ulpf-airgap-bundle.tar..."
docker save -o airgap/ulpf-airgap-bundle.tar \
  ulpf-backend:airgap \
  ulpf-frontend:airgap \
  postgres:15-alpine \
  redis:7-alpine \
  opensearchproject/opensearch:2.11.0

echo "Generating SHA-256 manifest..."
cd airgap
sha256sum ulpf-airgap-bundle.tar > manifest.sha256
cd ..

echo "Export complete! Transfer airgap/ulpf-airgap-bundle.tar and airgap/manifest.sha256 to the isolated network."
