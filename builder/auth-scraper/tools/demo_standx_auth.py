
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.dex_config import load_and_validate
from src.auth_builders import standx_sign_ed25519

def main():
    # 1. Load the specific env file provided by user
    env_path = "env_example/env_standx_example"
    schema_path = "config/dex-canonical-env.schema.json"
    
    print(f"Loading config from {env_path}...")
    try:
        config = load_and_validate(schema_path=schema_path, dotenv_path=env_path)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    # 2. Extract StandX config
    standx_config = config.get("STANDX")
    if not standx_config:
        print("No STANDX config found!")
        return

    print("StandX Config Loaded:")
    for k, v in standx_config.items():
        print(f"  {k}: {v[:10]}..." if isinstance(v, str) else f"  {k}: {v}")

    # 3. Generate Auth Headers
    # Assuming we want to sign a message "hello"
    private_key = standx_config["STANDX_REQUEST_ED25519_PRIVATE_KEY"]
    
    print("\nGenerating Auth Headers for message 'hello_standx'...")
    headers = standx_sign_ed25519(
        private_key_base58_or_bytes=private_key,
        message=b"hello_standx"
    )
    
    print("\nGenerated Headers:")
    print(headers)

if __name__ == "__main__":
    main()
