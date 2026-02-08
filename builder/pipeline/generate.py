from pathlib import Path
import json
from typing import Dict, Union
from builder.infra.llm import ask_llm
from builder.models import ExchangeSpec

from builder.pipeline.guards import enforce_entropy, EntropyViolation

def _generate_with_guards(prompt: str, config: dict = None) -> str:
    """
    Execute generation with sampling, entropy checks, and temperature decay.
    """
    llm_cfg = config.get("llm", {}).get("generate", {}) if config else {}
    
    model = llm_cfg.get("model", "gpt-4-turbo-preview")
    provider = llm_cfg.get("provider", "openai")
    # max_tokens = llm_cfg.get("max_tokens", 4000) # Removed
    cache = llm_cfg.get("cache", True)
    
    # Sampling parameters
    samples = llm_cfg.get("samples", 1)
    min_similarity = llm_cfg.get("min_similarity", 0.97)
    max_attempts = llm_cfg.get("max_attempts", 1)
    temperature = llm_cfg.get("temperature", 0.15)
    decay = llm_cfg.get("temperature_decay", 0.85)

    for attempt in range(max_attempts):
        try:
            # Generate samples
            outputs = []
            for _ in range(samples):
                out = ask_llm(
                    prompt,
                    provider=provider,
                    model=model,
                    temperature=temperature,
                    # max_tokens=max_tokens, # Removed
                    cache=cache
                )
                outputs.append(out)
            
            # If only 1 sample, just return it (guards need >1 to compare)
            if samples < 2:
                return outputs[0]
                
            # Check entropy
            return enforce_entropy(outputs, min_similarity)
            
        except EntropyViolation:
            # Decay temperature and retry
            temperature *= decay
            # print(f"Entropy violation, retrying with temp={temperature:.2f}")
            continue
            
    raise RuntimeError(f"Generation failed to stabilize after {max_attempts} attempts")

def generate_python_layer(spec: Union[ExchangeSpec, 'ExchangeResearch'], config: dict = None) -> Dict[str, str]:
    """
    Generate the Python layer (config, data, execution, etc.) for the adapter.
    Returns a dictionary of filename -> content.
    """
    from builder.pipeline.prompts.python_codegen_prompt import generate_python_codegen_prompt
    
    template_str = generate_python_codegen_prompt()
    
    # Handle different model types
    if hasattr(spec, 'exchange_identity'):
        name = spec.exchange_identity.exchange_name
    else:
        name = spec.name
        
    # Serialize spec to JSON for the prompt
    spec_json = spec.model_dump_json(indent=2)
    
    prompt = template_str.replace("{ADAPTER_NAME}", name) \
                         .replace("{EXCHANGE_NAME}", name) \
                         .replace("{SPEC_JSON}", spec_json)

    response = _generate_with_guards(prompt, config)
    return parse_llm_json(response, "python_files")

def generate_rust_core(spec: Union[ExchangeSpec, 'ExchangeResearch'], markdown_research: str, config: dict = None) -> Dict[str, str]:
    """
    Generate the Rust core crate for the adapter.
    Returns a dictionary of filename -> content.
    """
    from builder.pipeline.prompts.rust_codegen_prompt import generate_rust_codegen_prompt
    
    template_str = generate_rust_codegen_prompt()
    
    # Handle different model types
    if hasattr(spec, 'exchange_identity'):
        name = spec.exchange_identity.exchange_name
    else:
        name = spec.name
        
    prompt = template_str.replace("{ADAPTER_NAME}", name) \
                         .replace("{EXCHANGE_NAME}", name) \
                         .replace("{MARKDOWN}", markdown_research)

    response = _generate_with_guards(prompt, config)
    return parse_llm_json(response, "rust_files")

def parse_llm_json(response: str, key: str) -> Dict[str, str]:
    """
    Extract JSON from LLM response.
    """
    # Simple cleanup to handle potential markdown code blocks in response
    clean_resp = response.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(clean_resp)
        if key in data:
            return data[key]
        return data # fallback if root is the dict
    except json.JSONDecodeError:
        # Fallback: try to find the start and end of the json object
        try:
            start = clean_resp.find("{")
            end = clean_resp.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(clean_resp[start:end])[key]
        except Exception:
            pass
        raise ValueError(f"Could not parse JSON from LLM response: {response[:100]}...")
