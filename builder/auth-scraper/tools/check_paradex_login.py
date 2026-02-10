
import asyncio
import os
from dotenv import dotenv_values
from paradex_py.api.api_client import ParadexApiClient
from paradex_py.account.subkey_account import SubkeyAccount
from paradex_py.environment import TESTNET, PROD

def main():
    # Load env
    env_vars = dotenv_values("env_example/env_paradex_example")
    
    paradex_env = env_vars.get("PARADEX_ENV", "TESTNET").upper()
    l2_address = env_vars.get("PARADEX_MAIN_ACCOUNT_L2_ADDRESS")
    l2_private_key = env_vars.get("PARADEX_SUBKEY_PRIVATE_KEY")
    
    if not all([l2_address, l2_private_key]):
        print("❌ Missing PARADEX_MAIN_ACCOUNT_L2_ADDRESS or PARADEX_SUBKEY_PRIVATE_KEY")
        return

    print(f"Initializing Paradex Client for {paradex_env}")
    print(f"Account: {l2_address}")
    
    env = TESTNET if paradex_env == "TESTNET" else PROD
    client = ParadexApiClient(env=env)
    
    try:
        # Fetch system config (required for chain ID)
        print("\n--- Phase 1: Fetching System Config ---")
        config = client.fetch_system_config()
        print(f"Config Fetched. Chain ID: {config.starknet_chain_id}")
        
        # Initialize Subkey Account
        account = SubkeyAccount(
            config=config,
            l2_private_key=l2_private_key,
            l2_address=l2_address
        )
        
        # Initialize authorized client
        private_client = ParadexApiClient(env=env)
        private_client.init_account(account)
        
        # 1. Public Test: Get Markets
        print("\n--- Phase 2: Public Request (Markets) ---")
        markets = client.fetch_markets()
        print(f"Fetched {len(markets)} markets.")
        if isinstance(markets, dict) and "results" in markets:
             results = markets["results"]
             if results:
                 print(f"First Market: {results[0].get('symbol')}")
        elif isinstance(markets, list) and markets:
             print(f"First Market: {markets[0].get('symbol')}")

        # 2. Private Test: Get Account Summary
        print("\n--- Phase 3: Private Request (Account Summary) ---")
        summary = private_client.fetch_account_summary()
        print("SUCCESS: Account Summary retrieved.")
        print(f"Account Value: {summary.account_value}")
        print(f"Account Status: {summary.status}")
        
        # 3. Private Test: Get Open Orders
        print("\n--- Phase 4: Private Request (Open Orders) ---")
        orders = private_client.fetch_orders()
        print(f"SUCCESS: Fetched {len(orders.get('results', []))} open orders.")

    except Exception as e:
        print(f"❌ Paradex Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
