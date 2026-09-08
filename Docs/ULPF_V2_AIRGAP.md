# Air-Gap Deployment

This document outlines the deployment procedure for the **Universal Log Pre-processing Framework (ULPF) V2**, specifically designed for vendor-neutral, air-gapped operations.

## Deployment Steps

### 1. Model Pre-fetching (Internet Connected Machine)
Since the production environment is completely air-gapped, you must pre-fetch the local LLM weights.
1. Download `qwen2.5-coder-7b-instruct-q4_k_m.gguf` from HuggingFace.
2. Transfer the `.gguf` file via secure media to the air-gapped environment.

### 2. Prepare the Environment
Place the transferred model file into a newly created `models/` directory at the root of the ULPF project:
```bash
mkdir -p models
cp /secure-media/qwen2.5-coder-7b-instruct-q4_k_m.gguf ./models/qwen.gguf
```

### 3. Docker Configuration
Create a `.env` file in the root directory:
```env
# Disable mock mode to use the real model
ULPF_MOCK_LLM=false
ULPF_MODEL_PATH=/models/qwen.gguf

# Standard Configs
ULPF_MODE=airgap
POSTGRES_USER=ulpf
POSTGRES_PASSWORD=<secure_password>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<secure_password>
```

### 4. Build and Start
Build the unified container and start the stack:
```bash
docker-compose build
docker-compose up -d
```
