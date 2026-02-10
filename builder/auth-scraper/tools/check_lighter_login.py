
import os
import sys
import requests
import time

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

    base_url = lighter_conf.get("LIGHTER_BASE_URL", "https://mainnet.zklighter.elliot.ai")
    priv_key = lighter_conf["LIGHTER_API_KEY_PRIVATE_KEY"]
    api_key_index = int(lighter_conf.get("LIGHTER_API_KEY_INDEX", 0))
    account_index = lighter_conf.get("LIGHTER_ACCOUNT_INDEX")

    # Use accountLimits which is a cleaner private endpoint for verification
    # matches what worked in check_lighter_login_sdk.py
    path = "/api/v1/accountLimits"
    # Query params for accountLimits: account_index, auth (added later)
    url = f"{base_url}{path}?account_index={account_index}"
    
    # Try generic timestamp (now) vs expiry (now + 60s) for header auth (unused)
    timestamp_ms = int((time.time() + 60) * 1000) 
    body = b""
    
    # Construct signature payload
    # For lighter-sdk token generation, the message payload doesn't matter 
    # as the SDK constructs the message internally based on expiry/nonce.
    # The 'message' arg in lighter_sign is ignored by the SDK path.
    msg = b"ignored_by_sdk"
    
    # Cast account_index to int
    account_index = int(account_index)
    
    auth_data = lighter_sign(
        private_key_hex=priv_key,
        message=msg,
        api_key_index=api_key_index,
        timestamp_ms=timestamp_ms,
        account_index=account_index
    )
    
    if auth_data.auth_token:
        print("Using SDK Auth Token method (Query Param)")
        url = f"{url}&auth={auth_data.auth_token}"
        headers = {} # Token is in query param
    else:
        print("Using Legacy Header method (likely to fail on mainnet)")
        headers = {
            "x-lighter-chain-id": "1",
            "x-api-key": str(api_key_index),
            "x-timestamp": str(timestamp_ms),
            "x-signature": auth_data.signature_hex
        }
    
    print(f"Attempting GET {url}")
    print(f"Headers: {headers}")
    print(f"Payload signed: {msg}")
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
        
        if r.status_code == 200:
            print("SUCCESS: Logged in!")
        elif r.status_code == 401 or r.status_code == 403:
            print("FAILED: Auth invalid.")
        else:
            print("FAILED: Other error.")
            
    except Exception as e:
        print(f"Request Error: {e}")

if __name__ == "__main__":
    main()
