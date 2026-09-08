# ULPF V2 Architecture Overview

## Design Philosophy
The core principle of ULPF V2 is strict separation between the **Data Plane** and the **Control Plane**.

## 1. Data Plane (Hot Path)
The data plane is responsible for parsing logs at scale (tens of thousands of EPS).
- **Zero AI Dependency:** The data plane does not invoke any LLMs or heavy ML models. It relies solely on compiled Regex and JSONPath engines.
- **Components:** Ingestion Queue, Deterministic Parsers, Event Normalizer.
- **Unmapped Field Preservation:** If a log contains fields not present in the target schema (OCSF), they are dynamically injected into an `unmapped_fields` namespace, guaranteeing zero data loss.

## 2. Control Plane (Authoring)
The control plane is responsible for generating the deterministic configurations used by the data plane.
- **Local AI Authoring:** When a new log format is encountered, the control plane forwards samples to an offline, locally running LLM (`llama.cpp` + `qwen2.5-coder`).
- **Human-in-the-loop:** The LLM generates the JSON parser config. An operator reviews it via the React UI, tests it live against samples, and approves it.
- **Registry:** Once approved, the config is pushed to the Rule Registry and becomes active in the Data Plane.

## 3. Storage Layer
- **Raw Vault:** An immutable, write-before-transform filesystem vault that secures the original bytes of every log with a SHA-256 fingerprint before any parsing occurs.
- **PostgreSQL:** Stores rules, versions, state, and metadata.
- **OpenSearch:** Indexes the final normalized, canonical OCSF JSON events for SIEM querying.
