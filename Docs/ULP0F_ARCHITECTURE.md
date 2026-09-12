# ULPF V2 Architecture Overview

## Design Philosophy
The core principle of ULPF V2 is strict separation between the **Data Plane** and the **Control Plane**.

## 1. Data Plane (Hot Path)
The data plane is responsible for parsing logs at scale (tens of thousands of EPS) using a lightning-fast FastAPI & SQLite backend.
- **Zero AI Dependency:** The data plane does not invoke any LLMs or heavy ML models. It relies solely on compiled Regex and JSONPath engines based on pre-approved JSON rule configurations.
- **Components:** FastAPI Ingestion Endpoints, Fast-Path Fingerprint Engine, Deterministic Parsers, Event Normalizer.
- **Unmapped Field Preservation:** If a log contains fields not present in the target schema (OCSF or ECS), they are dynamically injected into an `unmapped` namespace, guaranteeing zero data loss.

## 2. Control Plane (Authoring)
The control plane is responsible for generating the deterministic configurations used by the data plane.
- **Local AI Authoring:** When a completely new log format is encountered (i.e. the fingerprint does not match any known active rules for the requested Target Schema), the control plane forwards samples to an offline, locally running LLM (`llama.cpp` + `qwen2.5-coder`).
- **Human-in-the-loop:** The LLM generates the JSON parser config. An operator reviews it via the React / Vite Studio UI, tests it live against samples, chooses the Target Schema (OCSF/ECS), and approves it.
- **Registry:** Once approved, the config is pushed to the Rule Registry as an `ACTIVE` version and immediately begins parsing future logs deterministically at scale in the Data Plane.

## 3. Storage Layer
- **Raw Vault:** An immutable, write-before-transform filesystem vault that secures the original bytes of every log with a SHA-256 fingerprint before any parsing occurs.
- **SQLite Database:** Stores active rules, rule versions, fingerprint mappings, parsing state, and session metadata.
- **OpenSearch (Optional in Docker Mode):** Indexes the final normalized, canonical OCSF/ECS JSON events for SIEM querying.
