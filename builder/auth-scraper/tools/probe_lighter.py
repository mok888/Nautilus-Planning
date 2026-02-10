
import requests
import os

BASE_URL = "https://api.lighter.xyz" # Failed
# Try the value from env example / docs
BASE_URL = "https://mainnet.zklighter.elliot.ai"

def probe(path):
    url = f"{BASE_URL}{path}"
    print(f"Probing {url}...")
    try:
        r = requests.get(url, timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Preview: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

endpoint_guesses = [
    "/info",
    "/v1/info",
    "/v1/tickers?chainId=1",
    "/v1/orderbook?symbol=ETH-USDC&chainId=1",
]

print("--- Public Probes ---")
for p in endpoint_guesses:
    probe(p)

key = "2b2eb5fd7b1bd3b62e34033b0583b15614c004c7d979075cf299be548dcf66e1fec137d3c3bc8b1d"
print(f"\nKey Length (hex chars): {len(key)}")
print(f"Key Length (bytes): {len(bytes.fromhex(key))}")
