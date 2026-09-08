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
Set `ULPF_MOCK_LLM=true` in your `.env` to return a static dummy JSON configuration during the Onboarding flow.
