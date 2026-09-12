# Local LLM Authoring

ULPF V2 utilizes an offline, quantization-optimized LLM solely to aid humans in writing complex regex and JSONPath parsers for proprietary log formats.

## Why a Local LLM?
1. **Privacy & Security:** Security logs contain highly sensitive IP addresses, usernames, and hostnames. Pushing this to an external API (like OpenAI) violates data localization policies in defense networks.
2. **Determinism:** LLMs hallucinate. If we used an LLM in the Data Plane to parse logs in real-time, it would occasionally misparse or drop critical fields. By restricting the LLM to the **Authoring Studio**, we guarantee that the final rule deployed to production is 100% deterministic regex.

## Technology Stack
- **Engine:** `llama.cpp` wrapper (`llama-cpp-python`).
- **Model:** `Qwen2.5-Coder-7B-Instruct-GGUF` (or similar code-generation specialized model).
- **Quantization:** Q4_K_M (4-bit quantization allows it to run on standard CPU architectures without requiring heavy Datacenter GPUs).

## Mock Mode
For development environments where a GGUF file is not present, ULPF provides a mock fallback.
Set `ULPF_MOCK_LLM=true` in your `backend/.env` file. When the Studio requests a new rule draft, the backend bypasses the LLM and uses a hardcoded fallback generator (`app.authoring.agent.generate_rule_from_samples`). 

This mock generator supports basic substring matching against known demo samples (e.g. Cisco ASA, AWS CloudTrail) to return valid Regex or JSON rules. It also dynamically injects the chosen `target_schema` (OCSF or ECS) into the mock output to simulate the schema override feature.
