
import os
import sys

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.dex_config import load_and_validate
from src.auth_builders import grvt_sign

def main():
    env_path = "env_example/env_grvt_example"
    print(f"Loading config from {env_path}...")
    
    try:
        config = load_and_validate("config/dex-canonical-env.schema.json", dotenv_path=env_path)
    except Exception as e:
        print(f"Config Load Error: {e}")
        return

    grvt_conf = config.get("GRVT")
    if not grvt_conf:
        print("No GRVT config found!")
        return

    print("GRVT Config Loaded:")
    for k, v in grvt_conf.items():
        masked_v = v[:8] + "..." if isinstance(v, str) and len(v) > 10 else v
        print(f"  {k}: {masked_v}")

    # Generate Signature
    msg = b"hello_grvt_demo"
    priv_key = grvt_conf["GRVT_PRIVATE_KEY"]
    
    print(f"\nGenerating Auth Headers for message '{msg.decode()}'...")
    
    headers = grvt_sign(
        private_key_hex=priv_key,
        message=msg
    )
    
    print("\nGenerated Headers:")
    print(headers)

if __name__ == "__main__":
    main()
