# ULPF V2 Live Demo Script

**Theme:** "From Raw Chaos to Standardized Intelligence in Seconds"

## Prep & Environment Check
1. Start Backend: `uv run fastapi dev app/main.py`
2. Start Frontend: `npm run dev`
3. Navigate to: `http://localhost:5173`

## Scene 1: The Operator's View (Dashboard)
- **Goal:** Show the overarching state and robustness.
- **Action:** Open Dashboard.
- **Talking Track:** 
  > "Welcome to the ULPF Pipeline. What you're seeing here is a live view of our ingestion framework. Notice the 'Fast Path' vs 'Adaptive Path' split. 
  > Fast Path processes logs deterministically via known rules, bypassing overhead. Adaptive Path kicks in for unknown formats, dynamically discovering and extracting schema mappings. 
  > This ensures our system is incredibly fast when it can be, and highly intelligent when it needs to be."

## Scene 2: Cataloging the Chaos (Sources Directory)
- **Goal:** Show where logs come from and how they are tracked.
- **Action:** Click "Sources".
- **Talking Track:**
  > "Here is our Source Directory. Every telemetry emitter is registered here. We have everything from syslogs to HTTP endpoints. We automatically detect schema drift and maintain a live inventory."

## Scene 3: The Magic of AI Authoring (Onboarding Studio)
- **Goal:** Showcase the local Qwen2.5-Coder-7B GGUF model generating rules on the fly.
- **Action:** Click "Onboarding".
- **Demo Steps:**
  1. Select **Palo Alto firewall** (unknown format).
  2. Explain the raw payload.
  3. Click **Analyze sample**.
  4. Point out the Rule Authoring Agent step lighting up.
  5. Show the generated JSON mapping and the parsed output.
- **Talking Track:**
  > "This is where ULPF shines. We have a raw Palo Alto firewall log. We don't have a parser for this. Normally, a security engineer would spend hours writing complex Regex or JSON extractors.
  > Instead, we click 'Analyze'. Our local, privacy-preserving Qwen 2.5 Coder LLM kicks in. It analyzes the raw string, understands the context—like identifying source and destination IPs—and generates a deterministic parser. 
  > The parser is then self-verified. We just saved hours of engineering time, completely offline and secure."
- **Action:** Now switch the sample to **AWS CloudTrail**. Click **Analyze sample**.
- **Talking Track:**
  > "If we ingest something we already know—like AWS CloudTrail—ULPF instantly detects the fingerprint, routes it to the Fast Path, and bypasses the LLM entirely for zero-latency processing."

## Scene 4: The Rule Registry (Rules)
- **Goal:** Show governance and lifecycle management.
- **Action:** Click "Rules".
- **Talking Track:**
  > "Every rule drafted by the AI isn't just a black box. It enters our Rule Registry as a declarative configuration.
  > Engineers can review, version, and manage these parsers via our Git-like lifecycle. Once approved, it executes at line-rate."

## Scene 5: Standardized Outputs (Events & Jobs)
- **Goal:** Show the final normalized data ready for SIEMs.
- **Action:** Click "Events", then "Jobs".
- **Talking Track:**
  > "Finally, the output. All heterogeneous logs are normalized into a unified schema, like OCSF, ready for downstream analytics. 
  > Whether it's live streaming events or bulk historical ingestion via Jobs, ULPF guarantees data integrity and uniformity."

## Conclusion
> "That is ULPF V2. A framework that combines the deterministic speed of traditional parsers with the adaptability of local LLMs, fully equipped to handle the telemetry scale of modern enterprises."
