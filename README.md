# Universal Log Pre-processing Framework (ULPF)

**Smart India Hackathon 2026 - Problem Statement ID: SIH26156**
**Team:** S.W.O.R.D.
**Tagline:** “Different Logs. One Standard. Trusted Everywhere.”

---

## 1. Problem
Enterprise and government networks generate log data from a vast array of devices and applications. Each source writes data in its own proprietary structure, vocabulary, and format. Before a SIEM or Data Lake can correlate these logs to detect threats, security engineers must manually analyze each log format and write a custom parser. This creates a severe operational bottleneck: parser sprawl, fragile regex rules that break during firmware updates, and silent loss of forensic evidence when fields don't fit the target schema.

## 2. Solution
ULPF is an adaptive, lossless, and traceable preprocessing middleware. Instead of requiring manual parser development for every new source, ULPF ingests an unknown log, automatically discovers its underlying template (via Drain3), extracts the fields, infers their types, and uses a local semantic AI model to propose mappings to a standard OCSF-aligned schema. 

A human reviewer validates low-confidence mappings. Once approved, the mapping acts as a deterministic, reusable parser for all subsequent logs from that source. The system guarantees **lossless normalization** by preserving the exact original byte payload in an immutable vault, calculating an integrity digest, and writing unmapped proprietary fields into a `vendor` extension namespace.

## 3. Architecture
ULPF is built as a pipeline of independent processing stages:
- **S1 Ingestion Gateway:** Accepts TCP/UDP Syslog, HTTP, and File inputs. Allocates a monotonic `trace_id`.
- **S5 Raw Event Vault:** Stores the exact byte-for-byte payload locally with a SHA-256 integrity digest before processing starts.
- **S2 Format Detection Engine:** Classifies the log (JSON, Syslog, CEF, CSV, etc.) and routes it.
- **S3 Adaptive Parser Factory:** Uses online template mining (`Drain3`) and compact sentence-embedding models (`all-MiniLM-L6-v2`) to extract and map fields.
- **S4 Normalization Engine:** Standardizes data into an Open Cybersecurity Schema Framework (OCSF) structure.
- **S6 Traceability Layer:** Records field-level provenance, proving exactly how `event.action` was derived from the raw bytes.
- **S7/S8 Review Console:** A React-based interface for adjudication of low-confidence mapping proposals.

## 4. Setup
ULPF is designed to run locally using Docker Compose, satisfying strict air-gapped requirements.

**Prerequisites:**
- Docker & Docker Compose
- Python 3.11 (for local development)
- Node.js & npm (for frontend development)

**Quick Start (Docker):**
ULPF is fully containerized. You can launch the entire stack (PostgreSQL, OpenSearch, Redis, Backend API, and Frontend UI) with a single command:
```bash
docker compose up --build -d
```

**Local Development Start (Without Docker):**

If you prefer to run the application components outside of Docker, you must first ensure you have local instances of PostgreSQL, OpenSearch, and Redis running. Then, you can choose one of the following methods to start the application:

**Method 1: Unified Start Script (Windows PowerShell)**
*Ensure you are in the root `ULPF` directory when running this command.*
```powershell
.\start_local.ps1
```
*This script will compile the frontend and automatically serve it via the backend API at `http://localhost:8000`.*

## 5. Demo
1. Open the UI at `http://localhost:8000`.
2. Navigate to **Onboarding** and submit an unknown proprietary firewall log.
3. The system will detect it as `UNRECOGNIZED` and route it to **Adaptive Discovery**.
4. The template will be mined, variables extracted, and types inferred.
5. In the **Review Queue**, you will see proposals for the fields. Approving the mapping registers a new version.
6. Submit a second log from the same source; it will bypass the AI and use the **FAST PATH**.
7. Go to **Traceability**, enter the `Trace ID`, and observe the side-by-side comparison of the raw log and normalized OCSF event, complete with `SHA-256 VERIFIED` status.

## 6. API
The framework exposes a REST API built on FastAPI. The full OpenAPI specification is available at `http://localhost:8000/docs`.

**Key Endpoints:**
- `POST /api/v1/ingest`: Ingest raw events.
- `POST /api/v1/onboarding/sample`: Analyze an unknown log sample.
- `POST /api/v1/mappings/{source_id}/{template_id}/approve`: Approve a mapping.
- `GET /api/v1/events/{trace_id}/raw`: Retrieve verbatim log with digest verification.
- `GET /api/v1/events/{trace_id}/provenance`: Get the derivation chain of the event.

## 7. Testing
The framework relies on `pytest` for backend unit and integration testing.

```bash
cd backend
pytest tests/
```
Tests assert deterministic classification, correct inference boundaries, fallback to semantic matching, preservation of unknown extensions, and byte-for-byte SHA-256 verification of the Raw Vault.

## 8. Offline Operation
ULPF is built explicitly for defense and regulated sectors requiring air-gapped networks.

- **No Cloud APIs:** All semantic mapping happens locally via CPU-optimized Sentence Transformers baked directly into the `backend/Dockerfile.airgap` image at build time.
- **No Telemetry:** The application is explicitly configured with `HF_HUB_DISABLE_TELEMETRY=1` and offline variables to prevent dialing home.
- **Vendored Dependencies:** All frontend dependencies and API endpoints are built into the UI statically, and Python requirements are frozen.
- **Airgap Bundling:** Use the provided scripts in the `airgap/` directory (`export_bundle.sh` or `export_bundle.ps1`) to bundle the entire application (including PostgreSQL, Redis, OpenSearch, and pre-trained models) into a single tar archive on a connected machine. This archive and its SHA-256 manifest can be moved via physical media to the isolated network and spun up safely using `import_bundle.sh` and `docker-compose.airgap.yml`.

> [!WARNING]
> Do NOT use `docker compose up --build` on the isolated machine. It will fail since it requires NPM and PyPI access. See `AIRGAP.md` for the operator runbook.

## 9. Limitations
- **Horizontal Scaling:** The current `docker-compose.yml` configures a single-node processing pipeline suitable for the MVP demonstration. Moving to a distributed multi-node architecture requires replacing the internal `asyncio.Queue` with the available Kafka integration (as per TRD).
- **GPU Acceleration:** Semantic mapping runs on the CPU. While sufficient for onboarding/discovery tasks, heavy backfilling of historical data through the adaptive path may cause latency spikes.
- **Encrypted Logs:** Proprietary binary or encrypted log formats are out of scope.
