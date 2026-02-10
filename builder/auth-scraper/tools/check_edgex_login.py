
import asyncio
import os
import sys
import json
import logging

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import dotenv_values
config = dotenv_values("env_example/env_edgex_example")

# Set env vars for SDK (it might look for them, though we pass them explicitly)
os.environ["EDGEX_ACCOUNT_ID"] = config.get("EDGEX_ACCOUNT_ID", "")
os.environ["EDGEX_STARK_PRIVATE_KEY"] = config.get("EDGEX_STARK_PRIVATE_KEY", "")
os.environ["EDGEX_BASE_URL"] = config.get("EDGEX_BASE_URL", "https://pro.edgex.exchange")

try:
    from edgex_sdk import Client
except ImportError:
    print("Error: edgex_sdk not installed.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    account_id = config.get("EDGEX_ACCOUNT_ID")
    private_key = config.get("EDGEX_STARK_PRIVATE_KEY")
    if not private_key:
         # fallback
         private_key = config.get("EDGEX_PRIVATE_KEY")
    base_url = config.get("EDGEX_BASE_URL", "https://pro.edgex.exchange")
    
    if not all([account_id, private_key]):
        print("Missing config in env_example/env_edgex_example")
        return

    print(f"Initializing EdgeX Client for Account: {account_id}")
    try:
        client = Client(
            base_url=base_url,
            account_id=int(account_id),
            stark_private_key=private_key
        )
    except Exception as e:
        print(f"Failed to init client: {e}")
        return

    # 1. Public Request
    print("\n--- Public Request: Get MetaData ---")
    try:
        # get_metadata is likely async
        meta = await client.get_metadata()
        print(json.dumps(meta, indent=2)[:500] + "...")
    except Exception as e:
        print(f"Public request failed: {e}")

    # 2. Private Request
    print("\n--- Private Request: Get Account Positions ---")
    try:
        # get_account_positions is async
        positions = await client.get_account_positions()
        print(json.dumps(positions, indent=2))
        
        if positions and "data" in positions:
            print("SUCCESS: Authenticated and fetched positions.")
        else:
            print("WARNING: Response structure unexpected (no 'data' field).")
            
    except Exception as e:
        print(f"Private request failed: {e}")
        # Print full exception for debugging
        import traceback
        traceback.print_exc()

    # Cleanup
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
