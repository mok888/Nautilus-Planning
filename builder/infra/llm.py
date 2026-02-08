import os
import time
import json
from pathlib import Path
from openai import OpenAI
from .llm_cache import load_cache, save_cache

def _get_opencode_config():
    """
    Load key and model from ~/.config/opencode/opencode.json
    """
    config = {"key": os.getenv("Z_AI_API_KEY"), "model": os.getenv("LLM_MODEL")}
    
    try:
        config_path = Path.home() / ".config/opencode/opencode.json"
        if config_path.exists():
            data = json.loads(config_path.read_text())
            
            # Key discovery
            if not config["key"]:
                mcp = data.get("mcp", {})
                for server in mcp.values():
                    env = server.get("environment", {})
                    if "Z_AI_API_KEY" in env:
                        config["key"] = env["Z_AI_API_KEY"]
                        break
            
            # Model discovery
            if not config["model"]:
                model_data = data.get("model")
                if isinstance(model_data, dict):
                    config["model"] = model_data.get("coding") or model_data.get("general")
                elif isinstance(model_data, str):
                    config["model"] = model_data
    except Exception:
        pass
    return config

def _create_client(provider: str):
    base_url = os.getenv("LLM_BASE_URL")
    
    if provider == "openai":
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=base_url)
    
    if provider == "glm":
        return OpenAI(
            api_key=os.getenv("GLM_API_KEY"),
            base_url=base_url or "https://open.bigmodel.cn/api/paas/v4",
        )
    
    if provider == "oh-my-opencode":
        cfg = _get_opencode_config()
        return OpenAI(
            api_key=cfg["key"],
            base_url=base_url or "https://api.z.ai/api/coding/paas/v4"
        )
    
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=base_url)

def ask_llm(
    prompt: str,
    provider: str = None,
    model: str = None,
    temperature: float = 0.0,
    max_tokens: int = None,
    cache: bool = True,
    retries: int = 2,
    **kwargs
) -> str:
    # 1. Resolve Provider
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "openai")
        
    # 2. Resolve Model
    if model is None:
        model = os.getenv("LLM_MODEL")
        if not model and provider == "oh-my-opencode":
            model = _get_opencode_config()["model"]
        
        if not model:
            model = "gpt-4-turbo-preview"

    # Normalize model for Oh My OpenCode
    if provider == "oh-my-opencode" and model.startswith("zai-coding-plan/"):
        model = model.replace("zai-coding-plan/", "")

    # Define cache key early to avoid NameError
    cache_key = {
        "provider": provider,
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if cache:
        cached = load_cache(cache_key)
        if cached:
            return cached

    client = _create_client(provider)
    
    # Check if API key is valid
    if not client.api_key:
         print(f"WARNING: API Key for provider '{provider}' is MISSING or EMPTY.")

    completion_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return ONLY valid JSON or code."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    
    if max_tokens is not None:
        completion_kwargs["max_tokens"] = max_tokens

    for attempt in range(retries + 1):
        try:
            r = client.chat.completions.create(timeout=300.0, **completion_kwargs)
            out = r.choices[0].message.content
            if cache:
                save_cache(cache_key, out)
            return out
        except Exception as e:
            print(f"DEBUG: LLM Attempt {attempt} failed for model '{model}': {e}")
            time.sleep(1)

    raise RuntimeError(f"LLM failed after {retries} retries for model '{model}'")
