# ULPF V2 Demo Workflow

This document outlines the ideal demo flow for the SIH26156 presentation to highlight the core strengths of the ULPF V2 architecture.

## Step 1: The Dashboard
- Start by showing the main dashboard (`/`).
- Highlight that ULPF sits between the noisy log shippers and the SIEM.

## Step 2: The Data Plane is Fast
- Show the `Rules Registry` (`/rules`). Explain that these rules run entirely deterministically in the data plane (Regex/JSONPath), NOT using an LLM. 
- Emphasize that because the Data Plane doesn't use AI, it achieves massive EPS (Events Per Second) throughput.

## Step 3: The Unknown Log Problem
- Explain the Fingerprint Engine: When a completely new, unseen log format hits the system, the Fingerprint Engine catches it. It doesn't drop the data; it vaults it and sends a sample to the Control Plane.

## Step 4: The Authoring Studio
- Navigate to the `Studio` (`/onboarding`).
- Paste 3-5 raw log lines into the UI (e.g. some proprietary firewall logs).
- Click "Generate Rule". Explain that this invokes the **Local Air-Gapped Qwen LLM**. It runs entirely locally on the machine—no data is sent to the internet.
- Show the generated JSON rule and mapping.
- Run the **Live Validation**.

## Step 5: Zero Data Loss
- Emphasize the `unmapped_fields` feature. If the proprietary firewall log has a random field `vendor_custom_id=123` that doesn't map to the standard OCSF schema, the deterministic parser safely appends it to `unmapped_fields` rather than throwing it away.

## Step 6: Vault Integrity
- Show the `Events Explorer` and trace an event back to the Vault, highlighting the SHA-256 cryptographic hash that guarantees the original bytes were preserved for legal forensics.
