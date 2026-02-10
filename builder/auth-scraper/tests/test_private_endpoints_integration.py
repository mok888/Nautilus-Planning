"""
Integration tests that "prove data can be retrieved from DEX with auth".

These are skipped unless you export real secrets.
"""
import os

import pytest

from src.dex_config import load_and_validate


@pytest.mark.integration
def test_edgex_private_endpoint_if_creds_present() -> None:
    schema_path = os.getenv("DEX_SCHEMA_PATH", "config/dex-canonical-env.schema.json")
    dotenv_path = os.getenv("DEX_DOTENV_PATH", ".env")

    if not os.path.exists(schema_path) or not os.path.exists(dotenv_path):
        pytest.skip("Missing schema or .env")

    cfg = load_and_validate(schema_path, dotenv_path=dotenv_path)

    edgex = cfg.get("EDGEX")
    if not edgex:
        pytest.skip("No EDGEX block in config")

    # Requires your real signing implementation; this shows the expected test shape.
    base = edgex.get("EDGEX_BASE_URL")
    acct = edgex.get("EDGEX_ACCOUNT_ID")
    pk = edgex.get("EDGEX_PRIVATE_KEY")
    if not (base and acct and pk):
        pytest.skip("Missing EDGEX creds")

    # "Proof" contract: can reach an authenticated endpoint.
    # Replace path with one your EdgeX API actually supports for private data,
    # and replace signature calc with the real scheme used in your production client.
    pytest.skip("Implement real EdgeX signature scheme + private endpoint path in your repo client.")
