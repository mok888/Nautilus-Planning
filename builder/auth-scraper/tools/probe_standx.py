
import requests
import os
import json

BASE_URL = "https://perps.standx.com"

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
    "/meta",
    "/v1/meta",
    "/api/v1/info",
    "/health",
]

print("--- Public Probes ---")
for p in endpoint_guesses:
    probe(p)
