
import os
import logging
import time
from apexomni.http_private_v3 import HttpPrivate_v3
from apexomni.constants import APEX_OMNI_HTTP_MAIN, NETWORKID_OMNI_MAIN_ARB
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Load env vars
    load_dotenv("env_example/env_apex_omni_example")
    
    api_key = os.getenv("APEX_API_KEY")
    api_secret = os.getenv("APEX_API_KEY_SECRET")
    api_passphrase = os.getenv("APEX_API_KEY_PASSPHRASE")
    omni_seed = os.getenv("APEX_OMNI_KEY_SEED")
    
    logger.info(f"Loaded credentials: API_KEY={api_key}, SECRET={'*' * 5 if api_secret else 'None'}, PASSPHRASE={'*' * 5 if api_passphrase else 'None'}, SEED={'*' * 5 if omni_seed else 'None'}")
    
    if not all([api_key, api_secret, api_passphrase, omni_seed]):
        logger.error("❌ Missing required Apex Omni credentials")
        return

    logger.info("--- Initializing Apex Omni Client ---")
    
    # Initialize Client
    # Note: APEX_OMNI_HTTP_MAIN is likely the correct endpoint if the example creds are mainnet.
    # The example seed suggests a real or robust test seed.
    
    # We need to derive the L2 Key from the seed first? 
    # The SDK example shows passing seeds/l2Key to HttpPrivateSign, but HttpPrivate_v3 might handle it differently.
    # Let's try the pattern from the SDK docs/examples.
    
    # Derive L2 Key (simulated or using SDK helper if available?)
    # The SDK has 'derive_zk_key' but it needs an ethereum address sign.
    # If we already HAVE the seed (APEX_OMNI_KEY_SEED), we might be able to use it directly.
    # SDK implementation of `derive_zk_key` returns {'seeds': ..., 'l2Key': ...}
    
    # Wait, the `HttpPrivate_v3` init signature isn't shown fully in the snippet.
    # But `demo_private_v3.py` suggests passing `api_key_credentials`.
    # Let's try basic account info retrieval which requires signature.
    
    try:
        # Assuming Mainnet Arbitrum for now as per SDK defaults in examples
        client = HttpPrivate_v3(
            APEX_OMNI_HTTP_MAIN, 
            network_id=NETWORKID_OMNI_MAIN_ARB,
            api_key_credentials={
                'key': api_key, 
                'secret': api_secret, 
                'passphrase': api_passphrase
            }
        )
        
        # Inject the seed manually if the client supports it for signing
        # Inspecting `http_private_v3.py`, it uses `self.zk_l2Key` and `self.zk_seeds` in `register_user_v3`.
        # But for `get_account_v3`, it might just use API Key?
        # SDK says: "some authentication information is required to access private endpoints."
        
        logger.info("Probe 1: Get Account (API Key Only?)")
        account = client.get_account_v3()
        logger.info(f"Account Info: {account}")
        
        if account:
            logger.info("✅ Apex Omni Login Successful!")
        else:
            logger.warning("⚠️ Login returned no data (might need seed signature?)")

    except Exception as e:
        logger.error(f"❌ Apex Omni Login Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
