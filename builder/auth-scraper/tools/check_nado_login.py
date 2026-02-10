
import asyncio
import os
import logging
import httpx
from eth_account import Account
from eth_utils import to_checksum_address
import binascii

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Credentials from env (provided by user context)
    private_key = os.getenv("NADO_PRIVATE_KEY")
    subaccount_id_hex = os.getenv("NADO_SUBACCOUNT_ID")
    
    if not private_key or not subaccount_id_hex:
        logger.error("❌ Missing NADO_PRIVATE_KEY or NADO_SUBACCOUNT_ID")
        return

    logger.info("--- Initializing Nado Login Check (Dependency-Free) ---")
    
    try:
        # 1. Derive Address from Private Key
        account = Account.from_key(private_key)
        signer_address = account.address
        logger.info(f"Derived Signer Address: {signer_address}")
        
        # 2. Extract Owner from Subaccount ID (First 20 bytes / 40 hex chars)
        # remove 0x prefix
        clean_subaccount = subaccount_id_hex[2:] if subaccount_id_hex.startswith("0x") else subaccount_id_hex
        
        # Check length
        if len(clean_subaccount) != 64:
             logger.error(f"❌ Invalid Subaccount ID length: {len(clean_subaccount)} (expected 64 hex chars)")
             return

        owner_hex = clean_subaccount[:40]
        # Format as checksum address
        owner_address = to_checksum_address(f"0x{owner_hex}")
        logger.info(f"Extracted Owner Address: {owner_address}")
        
        # 3. Verify Ownership
        if signer_address != owner_address:
            logger.warning(f"⚠️ Signer address ({signer_address}) does NOT match owner ({owner_address})!")
            logger.warning("This is only valid if the signer is a Linked Signer authorized on-chain.")
        else:
            logger.info("✅ Signer matches Subaccount Owner.")
            
        # 4. Probe API (Public Read)
        # Nado Mainnet Gateway URL
        base_url = "https://gateway.prod.nado.xyz/v1"
        
        logger.info("\n--- Phase 1: Public Query (Subaccount Info - MAINNET) ---")
        async with httpx.AsyncClient() as client:
            payload = {
                "type": "subaccount_info",
                "subaccount": subaccount_id_hex,
                "txns": None,
                "pre_state": None
            }
            
            logger.info(f"POST {base_url}/query with payload: {payload}")
            resp = await client.post(f"{base_url}/query", json=payload)
            
            logger.info(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    result = data.get("data", {})
                    exists = result.get("exists", False)
                    logger.info(f"✅ Query Success! Subaccount Exists: {exists}")
                    logger.info(f"Collateral: {result.get('spot_balances', [])}")
                else:
                    logger.error(f"❌ API Error: {data}")
            else:
                logger.error(f"❌ Request Failed: {resp.text}")

    except Exception as e:
        logger.error(f"❌ Nado Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

