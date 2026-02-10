
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def probe_edgex():
    base_url = "https://pro.edgex.exchange"
    endpoints = [
        "/api/v1/public/meta/getServerTime",
        "/api/v1/public/meta/getMetaData",
    ]
    
    for ep in endpoints:
        url = f"{base_url}{ep}"
        try:
            logger.info(f"GET {url}")
            resp = requests.get(url, timeout=5)
            logger.info(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(json.dumps(data, indent=2)[:500] + "...") # Truncate
                except:
                    print(resp.text[:500])
            else:
                print(f"Error: {resp.text}")
        except Exception as e:
            logger.error(f"Failed: {e}")

if __name__ == "__main__":
    probe_edgex()
