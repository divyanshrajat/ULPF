# ULPF Airgap Operator Runbook

This guide covers how to securely package, transfer, and deploy the Universal Log Pre-processing Framework (ULPF) into a completely isolated (air-gapped) environment.

## 1. Exporting the Bundle (Connected Machine)

On a machine with internet access and Docker installed:

1. Clone or copy the ULPF repository to the machine.
2. Run the export script for your platform:

**Linux / macOS:**
```bash
./airgap/export_bundle.sh [linux/amd64 | linux/arm64]
```

**Windows (PowerShell):**
```powershell
.\airgap\export_bundle.ps1 -Platform "linux/amd64"
```
*(Note: If your isolated target is x86 architecture, always specify `linux/amd64`, especially if you are building the bundle on Apple Silicon.)*

This script will:
- Download the CPU-only PyTorch and SentenceTransformer models at build-time.
- Build the `backend` and `frontend` images specifically configured for offline environments.
- Freeze all Python dependencies into `airgap/requirements.lock.txt`.
- Pull required database images (`postgres`, `redis`, `opensearch`).
- Save all images into a single tar archive: `airgap/ulpf-airgap-bundle.tar`.
- Generate a SHA-256 checksum: `airgap/manifest.sha256`.

## 2. Transfer

Copy the entire `ULPF` directory to a secure removable media drive. Transport the media to the isolated target machine.

## 3. Importing the Bundle (Isolated Machine)

On the isolated target machine (no internet):

1. Navigate to the transferred directory.
2. Make scripts executable (if on Linux) and run the import script:

```bash
chmod +x airgap/import_bundle.sh
./airgap/import_bundle.sh
```

This script will:
- Verify the SHA-256 manifest against the tar archive to ensure no corruption.
- Adjust the `vm.max_map_count` kernel parameter for OpenSearch (requires root/sudo).
- `docker load` all 5 images from the archive.
- Run `docker compose -f docker-compose.airgap.yml up -d` using `pull_policy: never`.
- Poll the health endpoints to ensure the system is up.

## 4. Demo and Verification

Once the stack is healthy, verify full functionality:
1. Open the UI at `http://localhost:5173`. (Or the host's IP if accessing from another machine on the LAN).
2. Submit a proprietary firewall log through **Onboarding**.
3. Verify the system proposes field mappings **without any network timeouts** or HTTP errors.
4. Approve the mappings in the **Review Queue**.
5. Re-submit another log to ensure it takes the fast path.
6. Check **Traceability** to see the `SHA-256 VERIFIED` derivation chain.

**WARNING:** Do not run `docker compose up --build` or `docker-compose.yml` on the isolated machine. These commands rely on fetching live Node and Python packages and will fail. Always use `docker-compose.airgap.yml` and the pre-built images.
