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

## 5. Deployment and Air-Gap Capabilities

ULPF is built explicitly for defense and regulated enterprise networks requiring **zero outbound internet connectivity**.

By using `llama.cpp` to run the highly quantized `qwen2.5-coder` model entirely on the local CPU/RAM, no log data ever leaves the network.

For full deployment instructions, see the [Zero-Trust Air-Gap Deployment Guide](./docs/ULPF_V2_AIRGAP.md).

---

## 6. Quick Start

ULPF is designed to operate seamlessly as **one unified application** on a single origin (`http://localhost:8000`).

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

# 3. Start Backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

*Note: For testing the LLM UI without a GPU or physical model file, ensure `ULPF_MOCK_LLM=true` is set in `backend/.env`.*

---

## 7. Demo Workflow & Testing

If you are preparing to demonstrate ULPF V2, please read the [Ideal Demo Workflow](./docs/ULPF_V2_DEMO.md) to understand how to best showcase the separation of the data plane and control plane.

To run the automated test suites or the End-to-End mock pipeline, refer to the [Testing Guide](./docs/ULPF_V2_TESTING.md).

---

## 8. License

Developed by **Team S.W.O.R.D.** for the **Smart India Hackathon 2026 (SIH26156)**.
