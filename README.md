# Universal Log Pre-processing Framework (ULPF) V2

**Smart India Hackathon 2026 — Problem Statement ID: SIH26156**  
**Team:** S.W.O.R.D.  
**Tagline:** *“Different Logs. One Standard. Trusted Everywhere.”*

---

## 1. What is ULPF?
Enterprise, defense, and government networks generate massive volumes of log data across different vendors and proprietary formats. Before a SIEM (like Splunk or Microsoft Sentinel) can correlate these logs for threat detection, they must be parsed and normalized.

Historically, this meant engineers had to write and maintain fragile regex parsers by hand. **ULPF (Universal Log Preprocessing Framework)** is an adaptive, zero-data-loss, air-gapped middleware that solves this. It sits between log shippers and the SIEM, transforming heterogeneous raw logs into a canonical schema in real-time.

---

## 2. Architecture: Control Plane vs. Data Plane

ULPF V2 utilizes a strict separation between the **Data Plane** (Hot Path) and the **Control Plane** (Authoring). 

### Why the LLM is NOT in the Hot Path
Processing tens of thousands of Events Per Second (EPS) in real-time through an LLM is impossible. LLMs are slow, expensive, and non-deterministic (they hallucinate). Security compliance requires 100% deterministic, auditable parsing rules. Therefore, the Data Plane in ULPF V2 **never** invokes an LLM.

Instead, ULPF uses a **Local AI Authoring Studio** in the Control Plane. The LLM is only used *once* when onboarding a completely new, unrecognized log format. It writes the regex/JSONPath rule, a human approves it, and the lightning-fast Data Plane executes it deterministically.

For more details, see our [Architecture Overview](./docs/ULPF_V2_ARCHITECTURE.md) and [Local LLM Strategy](./docs/ULPF_V2_LOCAL_LLM.md).

---

## 3. The Rule Lifecycle

1. **Fingerprinting:** Incoming logs are hashed structurally by the Fingerprint Engine.
2. **Authoring:** Unrecognized fingerprints are routed to the Authoring Studio. The Local Air-Gapped Qwen LLM drafts a deterministic parser configuration based on samples.
3. **Validation & Approval:** A human operator tests the drafted rule in the React UI and clicks "Approve".
4. **Execution:** The approved rule is loaded into the Data Plane's Rule Registry, where it parses future logs deterministically at scale.

For technical details, see the [Rule Format Definition](./docs/ULPF_V2_RULE_FORMAT.md) and [API Specification](./docs/ULPF_V2_API.md).

---

## 4. Normalization and Zero Data Loss

### OCSF / ECS Canonical Schema
All incoming logs are normalized to the Open Cybersecurity Schema Framework (OCSF), ensuring that regardless of whether a log came from a Cisco firewall or a Palo Alto firewall, the SIEM queries remain identical (e.g., `src_endpoint.ip`).

### Zero Data Loss & Raw Preservation
If a vendor log contains a custom field that doesn't map to OCSF, ULPF **does not drop the field**. Instead, it dynamically injects it into a safe `unmapped_fields` namespace. 

Furthermore, ULPF utilizes a **Write-Before-Transform Vault**. Before a single byte of transformation occurs, the original raw string is vaulted with a cryptographic SHA-256 hash.

### Traceability
Because of this vaulting mechanism, every single normalized JSON event can be traced directly back to its immutable raw origin, ensuring perfect evidence integrity for legal audits.

---

## 5. Air-Gap Deployment Instructions

ULPF is built explicitly for defense and regulated enterprise networks requiring **zero outbound internet connectivity**. By using `llama.cpp` to run the highly quantized `qwen2.5-coder` model entirely on the local CPU/RAM, no log data ever leaves the network.

**Step 1: Model Pre-fetching (Internet Connected Machine)**
1. Download `qwen2.5-coder-7b-instruct-q4_k_m.gguf` from HuggingFace.
2. Transfer the `.gguf` file via secure media to the air-gapped environment.

**Step 2: Prepare the Environment**
Place the transferred model file into a newly created `models/` directory at the root of the ULPF project:
```bash
mkdir -p models
cp /secure-media/qwen2.5-coder-7b-instruct-q4_k_m.gguf ./models/qwen.gguf
```

**Step 3: Build and Export (Connected Machine)**
Run the export script to build the application and package all dependencies into a tarball.
```bash
./airgap/export_bundle.sh
# or .\airgap\export_bundle.ps1 on Windows
```

**Step 4: Transfer**
Copy the entire `ULPF` directory (now containing the `airgap/ulpf-airgap-bundle.tar` file) to a secure removable media drive. Transport the media to the isolated target machine.

**Step 5: Docker Configuration (Isolated Machine)**
Create a `.env` file in the root directory on the target machine:
```env
# Disable mock mode to use the real model
ULPF_MOCK_LLM=false
ULPF_MODEL_PATH=/models/qwen.gguf

# Standard Configs
ULPF_MODE=airgap
POSTGRES_USER=ulpf
POSTGRES_PASSWORD=<secure_password>
OPENSEARCH_INITIAL_ADMIN_PASSWORD=<secure_password>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<secure_password>
```

**Step 6: Import and Start**
Run the import script to load the images and start the stack:
```bash
./airgap/import_bundle.sh
# or .\airgap\import_bundle.ps1 on Windows
```

---

## 6. How to Upload Batches of Logs via API

You can ingest batches of logs via the API using API Keys generated from the UI.

**Method A: Upload a Batch File (CSV, JSONL, or TXT)**
Use the `Jobs` endpoint which accepts `multipart/form-data` file uploads.
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/jobs?source_id=paloalto" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@/path/to/your/logs.txt"
```

**Method B: Stream Batches (JSON Array)**
If you are streaming logs from an agent, create a session and push batches of string payloads.
```bash
# 1. Create a session
curl -X POST "http://127.0.0.1:8000/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"source_id": "paloalto"}'
# Expected Response: {"id": "session-uuid-123", "status": "ACTIVE"}

# 2. Push a batch of logs to that session
curl -X POST "http://127.0.0.1:8000/api/v1/sessions/session-uuid-123/events" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '["<14>1 2026-09... log data 1", "<14>1 2026-09... log data 2"]'
```

---

## 7. Quick Start

ULPF is designed to operate seamlessly as **one unified application** on a single origin (`http://localhost:8000`).
Alternatively, you can run `docker compose up --build -d` to start the full stack via Docker (ensure you have configured `.env` based on `backend/.env.example`). Note: The default credentials in `docker-compose.yml` and `.env.example` are for demo purposes only.

#### Prerequisites
- Node.js 18+
- Python 3.11+

#### Build & Run
```bash
# 1. Build frontend
cd frontend
npm install
npm run build
cd ..

# 2. Setup Python environment
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env  # On Windows CMD, use: copy .env.example .env
# Note: The default .env configures a local SQLite database (ulpf.db).

# 4. Setup Database and Start Backend
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

*Note: For testing the LLM UI without a GPU or physical model file, ensure `ULPF_MOCK_LLM=true` is set in `backend/.env`.*

---

## 8. Demo Workflow & Testing

If you are preparing to demonstrate ULPF V2, please read the [Ideal Demo Workflow](./docs/ULPF_V2_DEMO.md) to understand how to best showcase the separation of the data plane and control plane.

To run the automated test suites or the End-to-End mock pipeline, refer to the [Testing Guide](./docs/ULPF_V2_TESTING.md).

---

## 9. Known Limitations (MVP — SIH26156)

The following items are **known gaps** in the current MVP that are either deferred for post-hackathon work or documented here per the project's requirement that undocumented gaps are worse than documented ones.

| # | Limitation | Severity | Mitigation / Roadmap |
|---|---|---|---|
| L1 | **In-memory event queue** — `InMemoryEventQueue` (`core/queue.py`) wraps `asyncio.Queue`. Events accepted between the last DB commit and a process crash (e.g., OOM kill) may be lost. | Medium | Replace with Redis Streams (Redis is already deployed) or Kafka/Redpanda before production. The `EventQueue` protocol is already defined; swap the singleton in `queue.py`. |
| L2 | **Mock LLM default** — `ULPF_MOCK_LLM=false` by default in production; set `ULPF_MOCK_LLM=true` only for development. The mock generator uses hardcoded substring matching against known demo samples and is not a real AI path. | High | Place a Qwen 2.5 `.gguf` file at the path specified by `ULPF_MODEL_PATH` before first run. See [Local LLM Strategy](./docs/ULPF_V2_LOCAL_LLM.md). |
| L3 | **OCSF/ECS field mapping is structural only** — The normalization adapters map field names between schemas but do not perform full semantic enrichment (e.g., `activity_id` integer codes, `category_uid` lookup tables). | Low | Extend `services/normalization/adapters/ocsf.py` and `ecs.py` with the relevant enum tables once OCSF and ECS schemas are finalized. |
| L4 | **Single-tenant only** — All sources, rules, events, and API keys share a single namespace. There are no `tenant_id` foreign keys and no Postgres Row-Level Security policies in place. | Low for MVP | Requires adding a `Tenant` model, `tenant_id` FKs, and RLS policies. Documented as a post-hackathon roadmap item. ULPF is explicitly single-tenant for SIH26156. |
| L5 | **CEF/LEEF/KeyValue/XML parsers** — Real parsers for these formats exist in `services/rules/parsers/`. If a rule declares one of these types but the format does not match, the factory raises an error rather than silently falling back to regex. This is the correct behavior (loud failure > silent mis-parse). | Low | Golden-sample tests exist for each parser type. |
| L6 | **Streaming is micro-batch** — `POST /sessions/{id}/events` accepts a JSON array per request. It is a micro-batch endpoint with a session ID attached, not a persistent bidirectional stream. The detect → lock → spot-check lifecycle applies correctly across micro-batches. | Low | If true persistent streaming is required, add a WebSocket or SSE endpoint. |
| L7 | **Single hardcoded admin user** — Authentication uses a single configured admin from environment variables. There is no multi-user RBAC UI or user management API. | Medium | Requires a `users` table, password hashing, and a session management flow. Roadmap item post-SIH26156. |

---

## 10. License

Developed by **Team S.W.O.R.D.** for the **Smart India Hackathon 2026 (SIH26156)**.
