# Universal Log Pre-processing Framework (ULPF)

**Smart India Hackathon 2026 — Problem Statement ID: SIH26156**  
**Team:** S.W.O.R.D.  
**Tagline:** *“Different Logs. One Standard. Trusted Everywhere.”*

---

## 1. Problem Statement

Enterprise, defense, and government networks generate massive volumes of log data across firewalls, proxies, routers, endpoint agents, and custom applications. Every device vendor outputs logs in proprietary syntax (RFC 3164/5424, CEF, LEEF, Key-Value, JSON, XML, or custom delimited strings).

Before a SIEM (e.g., Splunk, Microsoft Sentinel) or Security Data Lake can ingest and correlate these logs for threat detection, engineers must manually write and maintain fragile parsers. This causes:
- **Operational Bottleneck:** Weeks of manual regex/parser engineering per log source.
- **Parser Sprawl & Brittleness:** Upstream vendor firmware updates break regex patterns silently.
- **Evidence Loss:** Unrecognized or proprietary fields are discarded, compromising forensic and audit integrity.

---

## 2. Solution Overview

**ULPF** is an adaptive, lossless, and auditable log preprocessing middleware that transforms heterogeneous, unformatted logs into canonical, schema-compliant events in real time.

```
Incoming Raw Logs (Syslog / HTTP / Files)
                  │
                  ▼
   ┌──────────────────────────────┐
   │ S1: Ingestion Gateway        │ ──► Allocates monotonic trace_id (ULID)
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ S5: Raw Event Vault          │ ──► Write-Before-Transform (Immutable SHA-256)
   └──────────────┬───────────────┘
                  │
                  ▼
   ┌──────────────────────────────┐
   │ S2: Format Classifier        │ ──► Detects CEF, LEEF, Syslog, JSON, XML, KV
   └──────────────┬───────────────┘
                  │
                  ├──────────────────────────────┐
                  ▼ (Active Mapping)             ▼ (New / Drifted Template)
   ┌──────────────────────────────┐ ┌──────────────────────────────────────────┐
   │ FAST PATH (Sub-millisecond)  │ │ S3: Adaptive Discovery Factory           │
   │ Deterministic regex parser   │ │ • Drain3 Log Template Miner              │
   └──────────────┬───────────────┘ │ • Type Inference & Entity Extraction     │
                  │                 │ • SentenceTransformer Semantic Proposal  │
                  │                 └────────────────────┬─────────────────────┘
                  │                                      │
                  │                                      ▼
                  │                 ┌──────────────────────────────────────────┐
                  │                 │ S7/S8: Review Queue & Mapping Versioning │
                  │                 │ Human adjudication & atomic version bump │
                  │                 └────────────────────┬─────────────────────┘
                  │                                      │
                  └──────────────────┬───────────────────┘
                                     │
                                     ▼
   ┌───────────────────────────────────────────────────────────┐
   │ S4: Normalization Engine & S6: Provenance Lineage         │
   │ Standardizes to OCSF/ULPF canonical core + records lineage│
   └─────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
              Canonical Normalized JSON Event Stream
```

---

## 3. Running ULPF Locally (Development & Standalone Mode)

ULPF is designed to operate seamlessly as **one unified application** on a single origin (`http://localhost:8000`), serving both the React UI and the FastAPI REST backend.

### Option A: Quick Standalone Run (Fastest — No Heavy Containers Required)

This mode runs the complete pipeline using embedded local SQLite and the filesystem WORM Raw Vault.

#### Windows (PowerShell):
```powershell
# 1. Clone the repository & enter the folder
git clone https://github.com/divyanshrajat/ULPF.git
cd ULPF

# 2. Run the automated local startup script
.\start_local.ps1
```

*Alternatively, run step-by-step manually:*
```powershell
# Build frontend
cd frontend
npm install
npm run build
cd ..

# Start backend (serves compiled UI on port 8000)
$env:PYTHONPATH="backend"
$env:DATABASE_URL="sqlite:///backend/ulpf_dev.db"
$env:VAULT_DIR="data/vault"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Linux / macOS (Bash):
```bash
# 1. Build frontend
cd frontend
npm install
npm run build
cd ..

# 2. Setup Python environment & run
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="."
export DATABASE_URL="sqlite:///ulpf_dev.db"
export VAULT_DIR="data/vault"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

### Option B: Full Containerized Stack (Docker Compose)

Launches the complete enterprise microservices stack (FastAPI Backend, React SPA, PostgreSQL, Redis, and OpenSearch):

```bash
docker compose up --build -d
```

To view container logs or monitor startup:
```bash
docker compose logs -f backend
```

Once running, access the dashboard at:
* **Web UI & API Dashboard:** [http://localhost:8000](http://localhost:8000)
* **Interactive OpenAPI Specs:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Live Component Health:** [http://localhost:8000/api/v1/system/health/details](http://localhost:8000/api/v1/system/health/details)

---

## 4. Running ULPF in Air-Gapped / Isolated Environments

ULPF is built explicitly for defense, intelligence, and regulated enterprise networks requiring **zero outbound internet connectivity**.

### Step 1: Export Airgap Bundle (On an Internet-Connected Machine)

On a connected machine with Docker installed, generate the self-contained offline deployment bundle:

#### Linux / macOS:
```bash
chmod +x airgap/export_bundle.sh
./airgap/export_bundle.sh linux/amd64
```

#### Windows (PowerShell):
```powershell
.\airgap\export_bundle.ps1 -Platform "linux/amd64"
```

**What this script does:**
1. Downloads CPU-optimized PyTorch and SentenceTransformer weights (`all-MiniLM-L6-v2`) locally.
2. Compiles static frontend production assets and freezes all Python wheels into `airgap/requirements.lock.txt`.
3. Pulls required infrastructure container images (`postgres`, `redis`, `opensearch`).
4. Bundles all 5 images into a single tar archive: `airgap/ulpf-airgap-bundle.tar`.
5. Computes a cryptographic checksum manifest: `airgap/manifest.sha256`.

---

### Step 2: Transfer to Isolated Target

Copy the entire `ULPF/` directory (including `airgap/ulpf-airgap-bundle.tar` and `airgap/manifest.sha256`) to a secure removable USB drive or optical media, and transfer it to the target air-gapped machine.

---

### Step 3: Import and Launch on Air-Gapped Machine

On the isolated machine (no internet access):

#### Linux / macOS:
```bash
chmod +x airgap/import_bundle.sh
./airgap/import_bundle.sh
```

#### Windows (PowerShell):
```powershell
.\airgap\import_bundle.ps1
```

*Or run the airgap runtime orchestrator directly:*
```powershell
.\run-airgap.ps1
```

**Verification:**
* Verify offline policy and zero outbound calls:
```bash
curl http://localhost:8000/api/v1/system/airgap
```
Expected output:
```json
{
  "mode": "airgap",
  "airgap_compliant": true,
  "outbound_dependencies": false,
  "network_policy": "STRICT_OFFLINE",
  "local_model_verified": true,
  "telemetry_disabled": true
}
```

---

## 5. End-to-End Walkthrough & Feature Tour

1. **Dashboard (`/`):**
   - Live metrics for Total Ingested, Normalized, Fast Path vs. Adaptive breakdown, and component health.
2. **Onboard New Source (`/onboarding`):**
   - **Auto-Detect from File:** Drop any sample log file (`.log`, `.txt`, `.json`, `.xml`, `.csv`) directly on Step 1 to auto-fill Vendor, Product, Protocol, and Suggested Source ID.
   - **Quick Presets:** One-click presets for Cisco ASA, Palo Alto NGFW, Windows Security, Linux Syslog, AWS VPC Flow, and Nginx Web.
   - **Drain3 Mining:** Automatic clustering and parameter extraction with zero manual regex.
3. **Review Queue (`/reviews`):**
   - Review AI mapping proposals with multi-signal confidence scores (Name, Value Type, Context, History).
   - Approve mappings to atomically increment the source's mapping version.
4. **Trace Explorer (`/traces`):**
   - Inspect individual event traces with complete side-by-side comparison:
     - **Raw Vault Payload** with SHA-256 cryptographic seal.
     - **Normalized Canonical JSON** structure.
     - **Field-by-Field Provenance Lineage** showing source field, target field, and transformation rule.
5. **Events Explorer (`/events`):**
   - Search, filter, inspect normalized events, and export NDJSON streams.
6. **Schema Registry (`/schemas`):**
   - Canonical `ulpf-core-1.0` schema definitions, data types, and namespace hierarchy.
7. **Raw Event Vault (`/vault`):**
   - Immutable write-before-transform storage ledger with real-time SHA-256 integrity verification.
8. **System & Airgap Status (`/system`):**
   - Runtime configuration, processing thresholds, and air-gap compliance monitoring.

---

## 6. Automated Testing

To run the full suite of unit, integration, and end-to-end pipeline tests:

```bash
# Run backend test suite
cd backend
pytest tests/

# Run complete End-to-End Pipeline test
python test_e2e.py
```

---

## 7. System Architecture & Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend SPA** | React 18, TypeScript, Tailwind CSS, Lucide Icons, Vite |
| **Backend API** | FastAPI, Python 3.11+, Uvicorn, Pydantic v2 |
| **Log Discovery Engine** | Drain3 (Online Template Mining & Masking Heuristics) |
| **Semantic AI Engine** | SentenceTransformers (`all-MiniLM-L6-v2`), PyTorch CPU |
| **Database & ORM** | PostgreSQL / SQLite dialect-agnostic via SQLAlchemy 2.0 |
| **Preservation Vault** | Immutable Local WORM Filesystem Vault (SHA-256 Digest) |
| **Message Queue** | Async in-memory processing worker / Redis PubSub |

---

## 8. License

Developed by **Team S.W.O.R.D.** for the **Smart India Hackathon 2026 (SIH26156)**.
