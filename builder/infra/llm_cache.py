import hashlib, json
from pathlib import Path
from typing import Optional, Dict

CACHE_DIR = Path(".llm_cache")

def _key(data: dict) -> str:
    blob = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()

def load_cache(key_data: dict) -> Optional[str]:
    path = CACHE_DIR / f"{_key(key_data)}.json"
    if path.exists():
        return path.read_text()
    return None

def save_cache(key_data: dict, value: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{_key(key_data)}.json"
    path.write_text(value)
