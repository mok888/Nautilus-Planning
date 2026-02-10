
import requests

BASE_URL = "https://edge.grvt.io"

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
    "/",
    "/health",
    "/api/health",
    "/v1/health",
    "/info",
    "/api/v1/info",
    "/rpc", # Many L2s use RPC
]

print("--- Public Probes ---")
for p in endpoint_guesses:
    probe(p)
