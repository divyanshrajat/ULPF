#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "Verifying SHA-256 manifest..."
if ! sha256sum -c manifest.sha256; then
  echo "ERROR: Manifest verification failed. Archive may be corrupted."
  exit 1
fi

echo "Configuring host for OpenSearch..."
# This requires root privileges on the host
if [ "$(sysctl -n vm.max_map_count)" -lt 262144 ]; then
  echo "Increasing vm.max_map_count to 262144..."
  if command -v sudo &> /dev/null; then
    sudo sysctl -w vm.max_map_count=262144
  else
    su -c "sysctl -w vm.max_map_count=262144"
  fi
fi

echo "Loading docker images..."
docker load -i ulpf-airgap-bundle.tar

echo "Checking for expected images..."
EXPECTED_IMAGES=(
  "ulpf-backend:airgap"
  "ulpf-frontend:airgap"
  "postgres:15-alpine"
  "redis:7-alpine"
  "opensearchproject/opensearch:2.11.0"
)

for img in "${EXPECTED_IMAGES[@]}"; do
  if ! docker image inspect "$img" >/dev/null 2>&1; then
    echo "ERROR: Image $img not found after load."
    exit 1
  fi
done

echo "Starting ULPF in air-gap mode..."
cd ..
docker compose -f docker-compose.airgap.yml up -d

echo "Waiting for services to become healthy..."
MAX_TRIES=30
TRIES=0
while [ $TRIES -lt $MAX_TRIES ]; do
  if command -v curl &> /dev/null; then
      if curl -s http://localhost:8000/health | grep -q '"status":"HEALTHY"'; then
        echo "ULPF is up and healthy!"
        echo "UI available at http://localhost:5173"
        exit 0
      fi
  else
      # fallback if curl isn't available
      if wget -qO- http://localhost:8000/health 2>/dev/null | grep -q '"status":"HEALTHY"'; then
        echo "ULPF is up and healthy!"
        echo "UI available at http://localhost:5173"
        exit 0
      fi
  fi
  sleep 2
  TRIES=$((TRIES+1))
done

echo "ERROR: Services failed to become healthy within 60 seconds."
echo "Here are the backend logs:"
docker compose -f docker-compose.airgap.yml logs backend
exit 1
