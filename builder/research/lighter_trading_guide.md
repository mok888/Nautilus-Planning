# Lighter Login & Sub-Account Trading Guide

## Your Credentials

```bash
LIGHTER_API_KEY_PRIVATE_KEY="2b2eb5fd7b1bd3b62e"
LIGHTER_ACCOUNT_INDEX="281474976651006"
LIGHTER_API_KEY_INDEX="8"
```

---

## Quick Understanding of Your Credentials

| Credential | Purpose | Your Value |
|------------|---------|-------------|
| `LIGHTER_API_KEY_PRIVATE_KEY` | Private key for signing transactions | `2b2eb5fd7b1bd3b62e` |
| `LIGHTER_ACCOUNT_INDEX` | Which account to trade on | `281474976651006` |
| `LIGHTER_API_KEY_INDEX` | Which API key index (0-255) to use | `8` |

**Important:** Each account can have up to 256 API keys (indices 0-255). Each API key has its own nonce sequence!

---

## Complete Working Example

```python
import asyncio
import lighter

# ===== YOUR CREDENTIALS =====
BASE_URL = "https://mainnet.zklighter.elliot.ai"
LIGHTER_API_KEY_PRIVATE_KEY = "2b2eb5fd7b1bd3b62e"
LIGHTER_ACCOUNT_INDEX = 281474976651006
LIGHTER_API_KEY_INDEX = 8

async def main():
    print("=" * 60)
    print("LIGHTER TRADING - AUTHENTICATION COMPLETE")
    print("=" * 60)

    # STEP 1: Initialize SignerClient with your credentials
    client = lighter.SignerClient(
        url=BASE_URL,
        api_private_keys={
            LIGHTER_API_KEY_INDEX: LIGHTER_API_KEY_PRIVATE_KEY
        },
        account_index=LIGHTER_ACCOUNT_INDEX
    )

    # STEP 2: Verify credentials are correct
    err = client.check_client()
    if err is not None:
        print(f"❌ Client check failed: {err}")
        print("\nPossible issues:")
        print("1. Account index doesn't exist")
        print("2. API key index not registered for this account")
        print("3. Network issue (try testnet)")
        return

    print(f"✅ Account Index: {client.account_index}")
    print(f"✅ API Key Indices: {list(client.api_private_keys.keys())}")

    # STEP 3: Generate auth token for API requests
    auth_token, err = client.create_auth_token_with_expiry(
        deadline=3600,  # 1 hour
        api_key_index=LIGHTER_API_KEY_INDEX
    )

    if err:
        print(f"❌ Auth token generation failed: {err}")
        return

    print(f"✅ Auth token generated: {auth_token[:20]}...")

    # STEP 4: Get current nonce (managed automatically by SDK)
    nonce = client.next_nonce(api_key_index=LIGHTER_API_KEY_INDEX)
    print(f"✅ Next nonce for API key {LIGHTER_API_KEY_INDEX}: {nonce}")

    # STEP 5: Place a test order
    tx_info, tx_hash, err = await client.create_order(
        market_index=0,  # ETH perps market
        client_order_index=123456789012,  # Your unique ID
        base_amount=1000,  # 0.1 ETH (scaled by 10000)
        price=4050_00,  # $4050.00
        is_ask=False,  # Buy order (bid)
        order_type=client.ORDER_TYPE_LIMIT,
        time_in_force=client.ORDER_TIME_IN_FORCE_GOOD_TILL_TIME,
        reduce_only=False,
        nonce=nonce,  # Optional - SDK manages automatically
        api_key_index=LIGHTER_API_KEY_INDEX,
    )

    if err:
        print(f"❌ Order failed: {err}")
    else:
        print(f"✅ Order submitted successfully!")
        print(f"   TX Hash: {tx_hash}")
        print(f"   Client Order Index: {tx_info.client_order_index}")

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Monitor order execution via WebSocket:")
    print("   - Connect: wss://mainnet.zklighter.elliot.ai/stream")
    print(f"   - Subscribe: account_market/0/{LIGHTER_ACCOUNT_INDEX}")
    print("2. Cancel order: client.cancel_order()")
    print("3. Check position: Use /api/v1/account endpoint with auth token")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## How to Find Your Account Index

```python
import asyncio
import eth_account
import lighter

# Your L1 private key
ETH_PRIVATE_KEY = "YOUR_L1_PRIVATE_KEY_HERE"
BASE_URL = "https://mainnet.zklighter.elliot.ai"

async def find_account_index():
    # Get your L1 address
    eth_acc = eth_account.Account.from_key(ETH_PRIVATE_KEY)
    eth_address = eth_acc.address
    print(f"Your L1 Address: {eth_address}")

    # Query Lighter for all accounts tied to this address
    api_client = lighter.ApiClient(
        configuration=lighter.Configuration(host=BASE_URL)
    )
    account_api = lighter.AccountApi(api_client)

    response = await account_api.accounts_by_l1_address(
        l1_address=eth_address
    )

    print(f"\nFound {len(response.sub_accounts)} account(s):")
    print("=" * 60)

    for sub_account in response.sub_accounts:
        print(f"Account Index: {sub_account.index}")
        print(f"  Collateral: {sub_account.collateral}")
        print(f"  Status: {'✅ Active' if sub_account.status == 1 else '❌ Inactive'}")
        print(f"  Account Type: {'Main' if not sub_account.is_subaccount else 'Sub-account'}")
        print("-" * 60)

    await api_client.close()

if __name__ == "__main__":
    asyncio.run(find_account_index())
```

---

## How Sub-Accounts Work

### Account Structure

```
Ethereum Wallet (L1 Address: 0x123...)
│
├── Main Account (account_index: 100)
│   ├── API Key 0 (for general trading)
│   ├── API Key 1 (for TWAP orders)
│   ├── API Key 8 (your credential!)
│   └── API Keys 9-254 (up to 256 total)
│
├── Sub-Account 1 (account_index: 101)
│   ├── API Key 0-254
│   └── API Keys 9-254 (up to 256 total)
│
└── Sub-Account 2 (account_index: 102)
    └── API Keys 0-254 (up to 256 total)
```

### Key Points

1. **All accounts tied to same L1 Ethereum wallet**
2. **Each account has its own `account_index`**
3. **Each account can have up to 256 API keys (0-255)**
4. **Each API key has its own public/private key pair and nonce**
5. **API keys 0-1 are reserved for web/mobile interfaces**

---

## Authentication Flow

### Login Process

```
1. Initialize SignerClient with credentials
   └─> Validates account_index exists
   └─> Validates API key is registered for this account

2. Generate Auth Token (for REST/WebSocket API calls)
   └─> Format: {expiry_unix}:{account_index}:{api_key_index}:{random_hex}
   └─> Max expiry: 8 hours (standard) / 10 years (read-only)

3. Use Auth Token for API requests
   └─> Header: "Authorization: {auth_token}"
   └─> Query param: "auth={auth_token}"

4. Sign Transactions with Private Key (for trading)
   └─> Sign with Schnorr signature
   └─> Submit via sendTx() or WebSocket
```

---

## WebSocket Trading (Recommended for Real-time)

```python
import asyncio
import lighter
import websockets
import json

LIGHTER_API_KEY_PRIVATE_KEY = "2b2eb5fd7b1bd3b62e"
LIGHTER_ACCOUNT_INDEX = 281474976651006
LIGHTER_API_KEY_INDEX = 8

async def websocket_trading():
    # Generate auth token
    client = lighter.SignerClient(
        url="https://mainnet.zklighter.elliot.ai",
        api_private_keys={
            LIGHTER_API_KEY_INDEX: LIGHTER_API_KEY_PRIVATE_KEY
        },
        account_index=LIGHTER_ACCOUNT_INDEX
    )

    auth_token, _ = client.create_auth_token_with_expiry(
        deadline=3600,
        api_key_index=LIGHTER_API_KEY_INDEX
    )

    # Connect to WebSocket
    ws_url = f"wss://mainnet.zklighter.elliot.ai/stream"

    async with websockets.connect(ws_url) as ws:
        print("✅ WebSocket connected!")

        # Subscribe to account updates
        subscribe_msg = {
            "channel": f"account_market/0/{LIGHTER_ACCOUNT_INDEX}",
            "auth": auth_token
        }
        await ws.send(json.dumps(subscribe_msg))

        print(f"✅ Subscribed to account_market/0/{LIGHTER_ACCOUNT_INDEX}")

        # Listen for updates
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(message)

                if "type" in data:
                    msg_type = data["type"]

                    if msg_type == "update/account_market":
                        # Parse account update
                        account_data = data.get("account", {})
                        positions = account_data.get("positions", [])
                        orders = account_data.get("orders", [])

                        print(f"\n📊 Account Update:")
                        print(f"  Collateral: {account_data.get('collateral', 'N/A')}")
                        print(f"  Positions: {len(positions)}")
                        print(f"  Orders: {len(orders)}")

                        for pos in positions[:3]:  # Show first 3
                            print(f"    - Market {pos.get('market_index')}: {pos.get('position')} @ {pos.get('avg_entry_price')}")

                    elif msg_type == "update/order_book":
                        # Parse order book update
                        order_book = data.get("order_book", {})
                        asks = order_book.get("asks", [])
                        bids = order_book.get("bids", [])

                        if asks and bids:
                            print(f"\n📈 Order Book:")
                            print(f"  Best Ask: ${asks[0].get('price')}")
                            print(f"  Best Bid: ${bids[0].get('price')}")

            except asyncio.TimeoutError:
                # Send ping/keepalive
                await ws.send(json.dumps({"ping": int(asyncio.get_event_loop().time())}))
                continue

if __name__ == "__main__":
    asyncio.run(websocket_trading())
```

---

## Troubleshooting

### Common Errors

**"account not found"**
- Your `account_index` doesn't exist on Lighter
- Use `accounts_by_l1_address` to find valid indices

**"api key not found"**
- API key index not registered for this account
- Check that you created API key with correct account

**"ambiguous api key"**
- You provided `api_private_keys` dict but didn't specify which one to use
- Always specify `api_key_index` when signing

**"invalid nonce"**
- Nonce already used or too low
- SDK manages automatically - use `client.next_nonce()`

**"checkClient error"**
- Verify your BASE_URL is correct (mainnet vs testnet)
- Verify credentials are correct

---

## Resources

- **API Keys Doc**: https://apidocs.lighter.xyz/docs/api-keys
- **Sub-Accounts**: https://docs.lighter.xyz/perpetual-futures/sub-accounts-and-api-keys
- **Trading Docs**: https://apidocs.lighter.xyz/docs/trading
- **WebSocket Reference**: https://apidocs.lighter.xyz/docs/websocket-reference
- **Python SDK**: https://github.com/elliottech/lighter-python
- **Go SDK**: https://github.com/elliottech/lighter-go

---

## Summary

✅ **You have everything you need to trade:**
1. `LIGHTER_API_KEY_PRIVATE_KEY` - For signing transactions
2. `LIGHTER_ACCOUNT_INDEX` - Your account index (281474976651006)
3. `LIGHTER_API_KEY_INDEX` - Which API key to use (8)

✅ **Next steps:**
1. Run the provided code example
2. Test with small amounts first
3. Use WebSocket for real-time updates
4. Check trade execution via WebSocket or API

✅ **Key concepts:**
- Multiple API keys = parallel trading (independent nonces)
- Each account can have 256 API keys
- Sub-accounts share L1 wallet but have separate indices
- Auth tokens for API, signatures for transactions
