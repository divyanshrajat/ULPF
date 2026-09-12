# ULPF V2: Universal Log Pre-processing Framework

## The Problem
Modern security operations centers (SOCs) are drowning in a heterogeneous sea of logs. Firewalls, endpoint agents, cloud infrastructure, and custom applications all emit telemetry in drastically different formats (Syslog, JSON, CEF, XML).

Security engineers spend an exorbitant amount of time writing, maintaining, and debugging brittle parsers (Regex, Grok) just to normalize this data into a usable format like OCSF or ECS before it can even be analyzed.

## The ULPF V2 Solution
ULPF is an intelligent, high-performance ingestion layer that sits between raw telemetry emitters and downstream analytics (SIEM/Data Lake). It fundamentally solves the parsing bottleneck by introducing a **dual-path architecture**:

### 1. The Fast Path (Deterministic Execution)
When ULPF ingests a log, it computes a structural fingerprint. If the fingerprint matches an existing parser in the Rule Registry, the log is routed to the Fast Path. Here, it is parsed using a highly optimized, compiled declarative rule. This path guarantees maximum throughput and zero inference overhead.

### 2. The Adaptive Path (LLM-Powered Discovery)
When a completely unknown log format is ingested, ULPF routes it to the Adaptive Path. 
- A local, privacy-preserving LLM (Qwen2.5-Coder-7B via `llama.cpp`) analyzes the raw string.
- The LLM drafts a declarative parser configuration (Regex or JSONPath mappings).
- The system automatically validates the generated parser against the sample.
- If it passes, the new parser is saved in the Rule Registry as a "Draft".

Once an engineer approves the drafted rule, all future logs of that format will automatically hit the **Fast Path**.

## Key Features
- **Privacy-First AI:** Operates entirely locally. No sensitive logs are ever sent to external APIs like OpenAI.
- **Git-Like Rule Governance:** Parsers are treated as code with versions, statuses (Draft, Active, Deprecated), and approval workflows.
- **Immutable Preservation:** Raw logs are cryptographically hashed and stored before any transformation occurs, guaranteeing chain of custody.
- **Modern Vendor Portal:** A sleek, Tailwind V4-powered React dashboard for operators to monitor throughput, manage sources, and audit AI-generated rules.

## The Architecture
- **Frontend:** React + Vite + TypeScript, styled exclusively with Tailwind V4 for a premium dark-mode tech aesthetic.
- **Backend:** FastAPI (Python 3.12+), utilizing SQLAlchemy for robust relational data modeling.
- **AI Engine:** `llama-cpp-python` running GGUF quantized models for hardware-efficient inference.
