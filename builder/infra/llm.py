import os
import time
import random
import subprocess
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

    # Opencode CLI provider
    if provider == "opencode-cli":
        timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "300"))
        debug = os.getenv("LLM_DEBUG", "").strip().lower() in {"1", "true", "yes"}
        model_prefix = os.getenv("LLM_OPENCODE_MODEL_PREFIX", "zai-coding-plan/")
        if "/" not in model:
            model = f"{model_prefix}{model}"
        if debug:
            print(
                f"DEBUG: opencode-cli model={model} timeout={timeout_seconds}s prompt_len={len(prompt)}",
                flush=True,
            )
        result = subprocess.run(
            ["opencode", "run", "--model", model, "--format", "json"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        if result.returncode != 0:
            raise RuntimeError(f"opencode-cli failed: {result.stderr or result.stdout}")
        text_parts = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            if evt.get("type") == "error":
                raise RuntimeError(f"opencode-cli error: {evt}")
            part = evt.get("part") or {}
            if part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        return "".join(text_parts).strip()

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

    timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "300"))
    debug = os.getenv("LLM_DEBUG", "").strip().lower() in {"1", "true", "yes"}
    if debug:
        print(
            f"DEBUG: LLM request provider={provider} model={model} temp={temperature} "
            f"timeout={timeout_seconds}s prompt_len={len(prompt)}",
            flush=True,
        )

    env_retries = os.getenv("LLM_RETRIES")
    if env_retries is not None:
        try:
            retries = int(env_retries)
        except ValueError:
            if debug:
                print(f"DEBUG: Invalid LLM_RETRIES='{env_retries}', using default {retries}", flush=True)

    for attempt in range(retries + 1):
        try:
            r = client.chat.completions.create(timeout=timeout_seconds, **completion_kwargs)
            out = r.choices[0].message.content
            if debug:
                print(f"DEBUG: LLM response received len={len(out)}", flush=True)
            if cache:
                save_cache(cache_key, out)
            return out
        except Exception as e:
            err_text = str(e)
            print(f"DEBUG: LLM Attempt {attempt} failed for model '{model}': {e}", flush=True)
            # Exponential backoff on rate limit
            if "429" in err_text or "rate limit" in err_text.lower():
                base = 2 ** attempt
                jitter = random.uniform(0.5, 1.5)
                sleep_s = min(60.0, base * jitter)
                if debug:
                    print(f"DEBUG: Rate limit backoff sleeping {sleep_s:.1f}s", flush=True)
                time.sleep(sleep_s)
            else:
                time.sleep(1)

    raise RuntimeError(f"LLM failed after {retries} retries for model '{model}'")
