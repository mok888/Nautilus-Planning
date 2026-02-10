
import os
import sys

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.dex_config import load_and_validate
from src.auth_builders import lighter_sign

def main():
    env_path = "env_example/env_lighter_example"
    print(f"Loading config from {env_path}...")
    
    try:
        config = load_and_validate("config/dex-canonical-env.schema.json", dotenv_path=env_path)
    except Exception as e:
        print(f"Config Load Error: {e}")
        return

    lighter_conf = config.get("LIGHTER")
    if not lighter_conf:
        print("No LIGHTER config found!")
        return

    print("LIGHTER Config Loaded:")
    for k, v in lighter_conf.items():
        masked_v = v[:8] + "..." if isinstance(v, str) and len(v) > 10 else v
        print(f"  {k}: {masked_v}")

    # Generate Signature
    msg = b"hello_lighter_demo"
    priv_key = lighter_conf["LIGHTER_API_KEY_PRIVATE_KEY"]
    api_key_index = int(lighter_conf.get("LIGHTER_API_KEY_INDEX", 0))
    
    msg = b"hello_lighter_demo"
    priv_key = lighter_conf["LIGHTER_API_KEY_PRIVATE_KEY"]
    api_key_index = int(lighter_conf.get("LIGHTER_API_KEY_INDEX", 0))
    account_index = int(lighter_conf.get("LIGHTER_ACCOUNT_INDEX", 0))
    
    # Strip quotes if present (schema validation usually handles this but env_example has quotes)
    if isinstance(priv_key, str):
        priv_key = priv_key.strip('"')
    
    print(f"\nGenerating Auth Headers for message '{msg.decode()}'...")
    
    headers = lighter_sign(
        private_key_hex=priv_key,
        message=msg,
        api_key_index=api_key_index,
        timestamp_ms=1600000000000,
        account_index=account_index
    )
    
    print("\nGenerated Headers:")
    print(headers)

if __name__ == "__main__":
    main()
