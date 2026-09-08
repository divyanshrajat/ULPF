import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Fallback/Mock mode for testing if llama.cpp is not available
USE_MOCK = os.getenv("ULPF_MOCK_LLM", "false").lower() == "true"
MODEL_PATH = os.getenv("ULPF_MODEL_PATH", "/models/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf")

try:
    from llama_cpp import Llama
    _LLAMA_AVAILABLE = True
except ImportError:
    _LLAMA_AVAILABLE = False
    logger.warning("llama-cpp-python not installed. Local LLM will not function unless MOCK mode is enabled.")

# Lazy loaded singleton
_llm_instance = None

def get_llm():
    global _llm_instance
    if USE_MOCK:
        return "MOCK_LLM"
        
    if not _LLAMA_AVAILABLE:
        raise RuntimeError("llama-cpp-python is not installed. Please install it or enable ULPF_MOCK_LLM=true.")
        
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Local model not found at {MODEL_PATH}. Please download Qwen2.5-Coder-7B GGUF or set ULPF_MODEL_PATH.")
        
    if _llm_instance is None:
        logger.info(f"Loading local LLM from {MODEL_PATH}")
        _llm_instance = Llama(
            model_path=MODEL_PATH,
            n_ctx=4096,
            n_threads=max(1, os.cpu_count() - 1),
            verbose=False
        )
    return _llm_instance

def generate_rule_from_samples(samples: List[str]) -> Dict[str, Any]:
    """
    Invokes the local LLM to generate a declarative parser rule from log samples.
    """
    from .prompt import build_prompt
    
    prompt = build_prompt(samples)
    
    if USE_MOCK:
        logger.info("Using MOCK LLM to generate rule")
        return _mock_generate(samples)
        
    llm = get_llm()
    
    # Qwen-specific prompt format
    formatted_prompt = f"<|im_start|>system\nYou are a deterministic parsing configuration generator.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n```json\n"
    
    logger.info("Invoking local LLM for rule generation...")
    response = llm(
        formatted_prompt,
        max_tokens=1024,
        stop=["```", "<|im_end|>"],
        temperature=0.1,
        echo=False
    )
    
    text = response['choices'][0]['text'].strip()
    
    # Strip any potential markdown formatting
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
        
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode LLM response: {text}")
        raise ValueError("LLM did not return valid JSON") from e

def _mock_generate(samples: List[str]) -> Dict[str, Any]:
    # A deterministic mock for e2e tests
    import re
    # If it's the known firewall sample format
    if any("fw-accept" in s for s in samples):
        return {
            "parser": {
                "type": "regex",
                "pattern": r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s+(?P<host>\S+)\s+(?P<action>fw-accept|fw-drop)\s+src=(?P<src_ip>\S+)\s+dst=(?P<dst_ip>\S+)"
            },
            "field_mappings": {
                "timestamp": "event.time",
                "host": "device.hostname",
                "action": "event.action",
                "src_ip": "source.ip",
                "dst_ip": "destination.ip"
            },
            "required_fields": ["event.time", "source.ip", "destination.ip", "event.action"],
            "target_schema": "ocsf",
            "schema_version": "1.0"
        }
    
    # Generic generic json mock
    return {
        "parser": {
            "type": "jsonpath",
            "paths": {
                "time": "$.timestamp",
                "user": "$.user_id"
            }
        },
        "field_mappings": {
            "time": "event.time",
            "user": "user.id"
        },
        "required_fields": ["event.time"],
        "target_schema": "ocsf",
        "schema_version": "1.0"
    }
