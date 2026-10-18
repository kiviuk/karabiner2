#!/usr/bin/env python3
"""
Fetch free models from OpenRouter's public API (no API key needed).
"""

import json
import sys
import urllib.request


def fetch_models() -> dict:
    """Fetch models from OpenRouter public API"""
    url = "https://openrouter.ai/api/v1/models"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching API: {e}", file=sys.stderr)
        sys.exit(1)


def is_free_model(model: dict) -> bool:
    """Check if a model is free based on pricing"""
    pricing = model.get("pricing", {})
    if not pricing:
        return False
    
    # Check if prompt and completion are both "0" or 0
    prompt_price = pricing.get("prompt", "0")
    completion_price = pricing.get("completion", "0")
    
    try:
        if float(prompt_price) == 0 and float(completion_price) == 0:
            return True
    except (ValueError, TypeError):
        pass
    
    # Also check for :free variant in ID
    if model.get("id", "").endswith(":free"):
        return True
    
    return False


def format_model(m: dict) -> dict:
    """Extract relevant fields for display"""
    pricing = m.get("pricing", {})
    architecture = m.get("architecture", {})
    top_provider = m.get("top_provider", {})
    
    return {
        "id": m.get("id"),
        "name": m.get("name"),
        "context_length": m.get("context_length"),
        "input_modalities": architecture.get("input_modalities", []),
        "output_modalities": architecture.get("output_modalities", []),
        "pricing_prompt": pricing.get("prompt"),
        "pricing_completion": pricing.get("completion"),
        "supported_parameters": m.get("supported_parameters", []),
        "top_provider_context": top_provider.get("context_length"),
        "top_provider_max_completion": top_provider.get("max_completion_tokens"),
        "knowledge_cutoff": m.get("knowledge_cutoff"),
    }


def main():
    print("Fetching models from OpenRouter API...", file=sys.stderr)
    data = fetch_models()
    
    models = data.get("data", [])
    print(f"Found {len(models)} total models", file=sys.stderr)
    
    free_models = [m for m in models if is_free_model(m)]
    print(f"Found {len(free_models)} free models", file=sys.stderr)
    
    # Sort by context length (descending)
    free_models.sort(key=lambda m: -(m.get("context_length") or 0))
    
    formatted = [format_model(m) for m in free_models]
    print(json.dumps(formatted, indent=2))


if __name__ == "__main__":
    main()